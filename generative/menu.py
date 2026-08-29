from database.database import get_connection

from generative.takedown import generate_takedown_request
from generative.settings import select_request_settings
from generative.xai import explain_generation, display_explanation



def get_verified_pages_without_requests():
    """Return verified pages that do not have a takedown request."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            cp.id AS page_id,
            sr.url AS source_url,
            c.id AS company_id,
            c.company_name

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
    connection.close()

    return pages


def generate_request_menu() -> None:
    """Allow the user to select a verified page and generate a request."""

    pages = get_verified_pages_without_requests()

    print()
    print("=" * 80)
    print("GENERATE TAKEDOWN REQUEST")
    print("=" * 80)

    if not pages:
        print("No verified pages require takedown requests.")
        input("\nPress Enter to continue...")
        return

    for index, page in enumerate(pages, start=1):
        print(
            f"{index}. "
            f"{page['company_name'] or 'Unknown organisation'}"
        )
        print(f"   {page['source_url']}")
        print()

    print("0. Return")
    print("=" * 80)

    while True:

        choice = input("Select page: ").strip()

        if choice == "0":
            return

        try:
            selection = int(choice)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if not 1 <= selection <= len(pages):
            print("Please select one of the displayed pages.")
            continue

        page = pages[selection - 1]
        break

    generate_request_for_page(page)

    input("\nPress Enter to continue...")


def generate_request_for_page(page) -> None:
    """Generate a takedown request for a selected verified page."""

    connection = get_connection()
    cursor = connection.cursor()

    page_id = page["page_id"]

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

    if not entities:
        print()
        print("No verified PII exists for this page.")
        connection.close()
        return

    entities = [
        {
            "entity_type": entity["entity_type"],
            "entity_value": entity["entity_value"],
            "confidence": entity["confidence"],
        }
        for entity in entities
    ]

    organisation = (
        page["company_name"]
        or "the organisation"
    )

    reason = (
        "The verified personal information identified above "
        "appears on the specified source page."
    )

    print()
    print("=" * 80)
    print("REQUEST DETAILS")
    print("=" * 80)
    print(f"Organisation : {organisation}")
    print(f"Source       : {page['source_url']}")
    print()
    print("Verified PII:")

    for entity in entities:
        print(
            f"  - {entity['entity_type']}: "
            f"{entity['entity_value']}"
        )

    print("=" * 80)

    confirm = input(
        "Generate a takedown request for this page? [y/N]: "
    ).strip().lower()

    if confirm != "y":
        connection.close()
        print("Generation cancelled.")
        return

    try:
        settings = select_request_settings()
        request = generate_takedown_request(
            entities=entities,
            source_url=page["source_url"],
            organisation=organisation,
            reason=reason,
            settings=settings
        )
        print("=" * 80)
        print("REQUEST GENERATED")
        print("=" * 80)
        print(request)

        explanation = explain_generation(
            entities=entities,
            source_url=page["source_url"],
            organisation=organisation,
            reason=reason,
            request=request,
            settings=settings,
        )
        print("=" * 80)
        print("EXPLANATION GENERATED")
        print("=" * 80)
        display_explanation(explanation)

    except Exception as error:
        connection.close()
        print(f"Failed to generate request: {error}")
        return

    cursor.execute(
        """
        INSERT INTO GDPRRequests (
            company_id,
            page_id,
            generated_request,
            status
        )
        VALUES (?, ?, ?, 'Draft')
        """,
        (
            page["company_id"],
            page_id,
            request,
        ),
    )

    connection.commit()
    connection.close()

    print()
    print("=" * 80)

def show_previous_requests() -> None:
    """Display previous requests and allow regeneration."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            gr.id AS request_id,
            gr.company_id,
            gr.page_id,
            gr.generated_request,
            gr.status,
            gr.sent_date,
            gr.response_date,
            gr.created_at,
            c.company_name,
            sr.url AS source_url

        FROM GDPRRequests gr

        LEFT JOIN Companies c
            ON gr.company_id = c.id

        LEFT JOIN CrawledPages cp
            ON gr.page_id = cp.id

        LEFT JOIN SearchResults sr
            ON cp.search_result_id = sr.id

        ORDER BY gr.created_at DESC
        """
    )

    requests = cursor.fetchall()

    if not requests:
        connection.close()

        print()
        print("No previous takedown requests.")
        input("\nPress Enter to continue...")
        return

    print()
    print("=" * 80)
    print("PREVIOUS TAKEDOWN REQUESTS")
    print("=" * 80)

    for index, request in enumerate(requests, start=1):
        print(
            f"{index}. "
            f"{request['company_name'] or 'Unknown organisation'}"
        )
        print(f"   Request ID : {request['request_id']}")
        print(f"   Page ID    : {request['page_id']}")
        print(f"   Status     : {request['status']}")
        print(f"   Created    : {request['created_at']}")
        print()

    print("0. Return")
    print("=" * 80)

    while True:
        choice = input("Select request: ").strip()

        if choice == "0":
            connection.close()
            return

        try:
            selection = int(choice)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if 1 <= selection <= len(requests):
            request = requests[selection - 1]
            break

        print("Please select one of the displayed requests.")

    show_request_details(request, connection, cursor)

def show_request_details(request, connection, cursor) -> None:
    """Display a request and provide available actions."""

    print()
    print("=" * 80)
    print(f"REQUEST #{request['request_id']}")
    print("=" * 80)

    print(f"Organisation : {request['company_name'] or 'Unknown'}")
    print(f"Source       : {request['source_url']}")
    print(f"Status       : {request['status']}")
    print(f"Created      : {request['created_at']}")
    print(f"Sent         : {request['sent_date'] or 'Not sent'}")
    print(f"Response     : {request['response_date'] or 'None'}")

    print()
    print("GENERATED REQUEST")
    print("-" * 80)
    print(request["generated_request"])
    print("-" * 80)

    print()
    print("1. Regenerate request")
    print("2. Return")

    while True:
        choice = input("Select option: ").strip()

        if choice == "1":
            regenerate_request(
                request,
                connection,
                cursor,
            )
            return

        if choice == "2":
            return

        print("Invalid option. Please select 1-2.")

def regenerate_request(request, connection, cursor) -> None:
    """Regenerate a request using the verified PII for its page."""

    page_id = request["page_id"]

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

    if not entities:
        print()
        print("No verified PII exists for this page.")
        return

    entities = [
        {
            "entity_type": entity["entity_type"],
            "entity_value": entity["entity_value"],
            "confidence": entity["confidence"],
        }
        for entity in entities
    ]

    print()
    print("=" * 80)
    print("REGENERATE REQUEST")
    print("=" * 80)

    settings = select_request_settings()

    reason = (
        "The verified personal information identified above "
        "appears on the specified source page."
    )

    try:
        generated_request = generate_takedown_request(
            entities=entities,
            source_url=request["source_url"],
            organisation=request["company_name"] or "the organisation",
            reason=reason,
            settings=settings,
        )


        explanation = explain_generation(
            entities=entities,
            source_url=request["source_url"],
            organisation=request["company_name"] or "the organisation",
            reason=reason,
            request=generated_request,
            settings=settings,
        )

        display_explanation(explanation)

    except Exception as error:
        print(f"Failed to regenerate request: {error}")
        return

    cursor.execute(
        """
        INSERT INTO GDPRRequests (
            company_id,
            page_id,
            generated_request,
            status
        )
        VALUES (?, ?, ?, 'Draft')
        """,
        (
            request["company_id"],
            page_id,
            generated_request,
        ),
    )

    connection.commit()

    print()
    print("=" * 80)
    print("NEW REQUEST GENERATED")
    print("=" * 80)
    print(generated_request)
    print("=" * 80)

def takedown_menu() -> None:
    """Main takedown module menu."""

    while True:

        print()
        print("=" * 80)
        print("TAKEDOWN REQUESTS")
        print("=" * 80)
        print("1. Generate takedown request")
        print("2. View previous requests")
        print("3. Return")
        print("=" * 80)

        choice = input("Select an option: ").strip()

        if choice == "1":
            generate_request_menu()

        elif choice == "2":
            show_previous_requests()

        elif choice == "3":
            break

        else:
            print("Invalid option. Please select 1-3.")


if __name__ == "__main__":
    takedown_menu()