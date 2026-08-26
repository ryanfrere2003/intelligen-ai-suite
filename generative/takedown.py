from openai import OpenAI

from config import OPENROUTER_API_KEY
from database.database import get_connection


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def generate_takedown_request(
    entities: list[dict],
    source_url: str,
    organisation: str,
    reason: str,
) -> str:

    pii_information = "\n".join(
        f"- {entity['entity_type']}: {entity['entity_value']}"
        for entity in entities
    )

    prompt = f"""
You are assisting a user with a personal information removal request.

Generate a professional suggested takedown request based ONLY
on the information provided below.

VERIFIED PERSONAL INFORMATION:
{pii_information}

SOURCE:
{source_url}

ORGANISATION:
{organisation}

REASON:
{reason}

REQUIREMENTS:
- Clearly identify every verified piece of personal information.
- Include the exact values provided above.
- Clearly identify the source URL.
- Identify the organisation where provided.
- Request removal or appropriate restriction of the identified information.
- Do not invent any facts.
- Do not claim that a legal violation has definitely occurred.
- Do not threaten legal action.
- Do not include information that is not listed as verified.
- Keep the request professional and concise.
- This is a suggested draft and will be reviewed by the user.
"""

    response = client.responses.create(
        model="openrouter/free",
        input=prompt,
    )

    return response.output_text


def generate_requests_for_verified_pages() -> None:
    """
    Generate one GDPR takedown request for each verified page.

    Only PII entities that have been individually verified are
    included in the generated request.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("PRAGMA table_info(CrawledPages)")

    # Find verified pages that do not already have a GDPR request.
    cursor.execute(
        """
        SELECT
            cp.id AS page_id,
            sr.url AS source_url,
            c.id AS company_id,
            c.company_name,
            c.privacy_email,
            c.contact_email

        FROM CrawledPages cp

        JOIN SearchResults sr
            ON cp.search_result_id = sr.id

        LEFT JOIN Companies c
            ON cp.company_id = c.id

        LEFT JOIN GDPRRequests gr
            ON gr.page_id = cp.id

        WHERE cp.verification_status = 'verified'
          AND gr.id IS NULL

        ORDER BY cp.id ASC
        """
    )

    pages = cursor.fetchall()

    if not pages:
        print("No verified pages require takedown requests.")
        connection.close()
        return

    print(f"Found {len(pages)} verified page(s).")

    generated = 0

    for page in pages:

        page_id = page["page_id"]
        source_url = page["source_url"]

        company_id = page["company_id"]
        company_name = page["company_name"]

        privacy_email = page["privacy_email"]
        contact_email = page["contact_email"]

        organisation = company_name or "the organisation"

        # Get only PII that the user individually verified.
        cursor.execute(
            """
            SELECT DISTINCT 
                entity_type,
                entity_value,
                confidence

            FROM PIIEntities

            WHERE page_id = ?
              AND status = 'verified'

            ORDER BY entity_type ASC
            """,
            (page_id,),
        )

        entities = cursor.fetchall()

        # A verified page may contain no individually verified PII.
        if not entities:
            print(
                f"Skipping page {page_id}: "
                "no verified PII entities."
            )
            continue

        # Convert sqlite3.Row objects into dictionaries.
        entities = [
            {
                "entity_type": entity["entity_type"],
                "entity_value": entity["entity_value"],
                "confidence": entity["confidence"],
            }
            for entity in entities
        ]

        reason = (
            "The verified personal information identified above "
            "appears on the specified source page."
        )

        print()
        print("=" * 80)
        print(f"Page ID      : {page_id}")
        print(f"Organisation : {organisation}")
        print(f"Source       : {source_url}")
        print("Verified PII :")

        for entity in entities:
            print(
                f"  - {entity['entity_type']}: "
                f"{entity['entity_value']}"
            )

        try:

            request = generate_takedown_request(
                entities=entities,
                source_url=source_url,
                organisation=organisation,
                reason=reason,
            )

        except Exception as error:

            print(
                f"Failed to generate request for "
                f"page {page_id}: {error}"
            )

            continue

        recipient_email = privacy_email or contact_email

        cursor.execute(
            """
            INSERT INTO GDPRRequests (
                company_id,
                page_id,
                generated_request,
                recipient_email,
                status
            )
            VALUES (?, ?, ?, ?, 'Draft')
            """,
            (
                company_id,
                page_id,
                request,
                recipient_email,
            ),
        )

        connection.commit()

        generated += 1

        print("Request generated successfully.")

    connection.close()

    print()
    print("=" * 80)
    print(f"Generated {generated} GDPR request(s).")
    print("=" * 80)


if __name__ == "__main__":
    generate_requests_for_verified_pages()