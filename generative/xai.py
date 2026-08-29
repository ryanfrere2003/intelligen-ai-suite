from openai import OpenAI

from config import OPENROUTER_API_KEY
from generative.prompt import xai_parent_prompt, xai_output_prompt
from generative.settings import RequestSettings


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def explain_generation(
    request: str,
    entities: list[dict],
    source_url: str,
    organisation: str,
    reason: str,
    settings: RequestSettings,
) -> str:
    """
    Generate a plain-text XAI attribution report.

    The XAI model is asked to identify observable relationships between
    the supplied inputs/settings and the generated request.

    No chain-of-thought is requested or exposed.
    """

    pii_information = "\n".join(
        f"- {entity['entity_type']}: {entity['entity_value']}"
        for entity in entities
    )

    dynamic_prompt = f"""
        INPUTS
    
        VERIFIED PII:
        {pii_information}
    
        SOURCE:
        {source_url}
    
        ORGANISATION:
        {organisation}
    
        REASON:
        {reason}
    
        USER SETTINGS:
        Tone: {settings.tone}
        Request objective: {settings.request_type}
        Detail level: {settings.detail_level}
        Legal references: {settings.legal_references}
        Additional instructions: {settings.additional_instructions or "None"}
    
        APPLICATION CONSTRAINTS:
        - Use only verified information.
        - Preserve verified PII exactly.
        - Include the source URL.
        - Do not invent facts.
        - Do not make definitive legal claims.
        - Do not threaten legal action.
    
        GENERATED REQUEST:
        {request}
    """

    prompt = (
        xai_parent_prompt
        + "\n"
        + dynamic_prompt
        + "\n"
        + xai_output_prompt
    )

    response = client.responses.create(
        model="openrouter/free",
        input=prompt,
    )

    output = response.output_text.strip()

    if not output:
        print()
        print("=" * 80)
        print("XAI WARNING: EMPTY RESPONSE")
        print("=" * 80)
        print("Response object:")
        print(response)
        print("=" * 80)

        return "No XAI explanation was returned."

    return output


def display_explanation(explanation: str) -> None:
    """Display the XAI attribution report."""

    print()
    print("=" * 80)
    print("XAI OUTPUT ATTRIBUTION")
    print("=" * 80)
    print()

    print(explanation)

    print()
    print("=" * 80)