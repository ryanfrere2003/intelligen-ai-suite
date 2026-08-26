from openai import OpenAI

from config import OPENROUTER_API_KEY
from generative.prompt import parent_prompt
from generative.settings import RequestSettings


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def generate_takedown_request(
    entities: list[dict],
    source_url: str,
    organisation: str,
    reason: str,
    settings: RequestSettings,
) -> str:
    """
    Generate a suggested personal information removal request.

    The parent prompt contains the application's fixed safety and
    accuracy requirements. User-configurable settings are supplied
    separately and cannot override those requirements.
    """

    pii_information = "\n".join(
        f"- {entity['entity_type']}: {entity['entity_value']}"
        for entity in entities
    )

    prompt = f"""
{parent_prompt}

USER PREFERENCES:

TONE:
{settings.tone}

REQUEST OBJECTIVE:
{settings.request_type}

DETAIL LEVEL:
{settings.detail_level}

LEGAL REFERENCES:
{settings.legal_references}

ADDITIONAL USER INSTRUCTIONS:
{settings.additional_instructions or "None provided."}

VERIFIED PERSONAL INFORMATION:
{pii_information}

SOURCE:
{source_url}

ORGANISATION:
{organisation}

REASON:
{reason}

Generate the suggested request now.
"""

    response = client.responses.create(
        model="openrouter/free",
        input=prompt,
    )

    return response.output_text