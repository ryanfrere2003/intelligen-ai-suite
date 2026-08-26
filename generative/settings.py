from dataclasses import dataclass


@dataclass
class RequestSettings:
    tone: str
    request_type: str
    detail_level: str
    legal_references: str
    additional_instructions: str


def select_request_settings() -> RequestSettings:
    """Prompt the user to configure the takedown request."""

    print()
    print("=" * 80)
    print("REQUEST SETTINGS")
    print("=" * 80)

    # --------------------------------------------------
    # Tone
    # --------------------------------------------------

    tones = {
        "1": "Professional",
        "2": "Formal",
        "3": "Friendly",
        "4": "Direct",
    }

    print()
    print("Tone:")
    for key, value in tones.items():
        print(f"{key}. {value}")

    while True:
        choice = input("Select tone [1-4]: ").strip()

        if choice in tones:
            tone = tones[choice]
            break

        print("Invalid selection. Please choose 1-4.")

    # --------------------------------------------------
    # Request objective
    # --------------------------------------------------

    request_types = {
        "1": "Request removal",
        "2": "Request removal or restriction",
        "3": "Request review and removal",
    }

    print()
    print("Request objective:")
    for key, value in request_types.items():
        print(f"{key}. {value}")

    while True:
        choice = input("Select objective [1-3]: ").strip()

        if choice in request_types:
            request_type = request_types[choice]
            break

        print("Invalid selection. Please choose 1-3.")

    # --------------------------------------------------
    # Detail level
    # --------------------------------------------------

    detail_levels = {
        "1": "Very concise",
        "2": "Concise",
        "3": "Detailed",
    }

    print()
    print("Detail level:")
    for key, value in detail_levels.items():
        print(f"{key}. {value}")

    while True:
        choice = input("Select detail level [1-3]: ").strip()

        if choice in detail_levels:
            detail_level = detail_levels[choice]
            break

        print("Invalid selection. Please choose 1-3.")

    # --------------------------------------------------
    # Legal references
    # --------------------------------------------------

    legal_options = {
        "1": "Do not mention specific legislation",
        "2": "Mention GDPR generally",
        "3": "Mention applicable data protection rights",
    }

    print()
    print("Legal references:")
    for key, value in legal_options.items():
        print(f"{key}. {value}")

    while True:
        choice = input("Select legal reference option [1-3]: ").strip()

        if choice in legal_options:
            legal_references = legal_options[choice]
            break

        print("Invalid selection. Please choose 1-3.")

    # --------------------------------------------------
    # Additional instructions
    # --------------------------------------------------

    print()
    print("Additional instructions:")
    print("Leave blank if you have no additional instructions.")

    additional_instructions = input("> ").strip()

    # --------------------------------------------------
    # Display summary
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("REQUEST SETTINGS")
    print("=" * 80)
    print(f"Tone:                {tone}")
    print(f"Objective:           {request_type}")
    print(f"Detail:              {detail_level}")
    print(f"Legal references:    {legal_references}")
    print(
        "Additional:          "
        f"{additional_instructions or 'None'}"
    )
    print("=" * 80)

    return RequestSettings(
        tone=tone,
        request_type=request_type,
        detail_level=detail_level,
        legal_references=legal_references,
        additional_instructions=additional_instructions,
    )