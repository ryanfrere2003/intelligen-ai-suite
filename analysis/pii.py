import re

from config import (
    USER_FIRST_NAME,
    USER_MIDDLE_NAMES,
    USER_LAST_NAME,
    USER_EMAIL,
    USER_USERNAME,
    USER_LOCATIONS,
    USER_NUMBERS,
)


def normalise_phone(number: str) -> str:
    """Remove formatting from a phone number."""
    return re.sub(r"\D", "", number)


class PIIExtractor:
    """Detects whether a page contains the user's known PII."""

    @staticmethod
    def extract(connection, page_id: int, text: str) -> None:
        """Extract known user PII from a page."""

        cursor = connection.cursor()

        text_lower = text.lower()
        text_phone = normalise_phone(text)

        findings = []

        # -----------------------------
        # User email
        # -----------------------------
        if USER_EMAIL and USER_EMAIL.lower() in text_lower:
            findings.append(
                ("email", USER_EMAIL, 1.0)
            )

        # -----------------------------
        # Usernames
        # -----------------------------
        for username in USER_USERNAME:

            if username.lower() in text_lower:

                findings.append(
                    ("username", username, 1.0)
                )

        # -----------------------------
        # Names
        # -----------------------------
        names = {
            f"{USER_FIRST_NAME} {USER_LAST_NAME}"
        }

        if USER_MIDDLE_NAMES:

            names.add(
                f"{USER_FIRST_NAME} "
                f"{' '.join(USER_MIDDLE_NAMES)} "
                f"{USER_LAST_NAME}"
            )

            for middle in USER_MIDDLE_NAMES:

                names.add(
                    f"{USER_FIRST_NAME} "
                    f"{middle} "
                    f"{USER_LAST_NAME}"
                )

        for name in names:

            if name.lower() in text_lower:

                findings.append(
                    ("name", name, 1.0)
                )

        # -----------------------------
        # Locations
        # -----------------------------
        for location in USER_LOCATIONS:

            if location.lower() in text_lower:

                findings.append(
                    ("location", location, 0.8)
                )

        # -----------------------------
        # Phone numbers
        # -----------------------------
        for number in USER_NUMBERS:

            if normalise_phone(number) in text_phone:

                findings.append(
                    ("phone", number, 1.0)
                )

        # -----------------------------
        # Remove duplicates
        # -----------------------------
        findings = list(dict.fromkeys(findings))

        # -----------------------------
        # Store results
        # -----------------------------
        for entity_type, entity_value, confidence in findings:

            cursor.execute(
                """
                INSERT INTO PIIEntities
                (
                    page_id,
                    entity_type,
                    entity_value,
                    confidence
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    page_id,
                    entity_type,
                    entity_value,
                    confidence,
                ),
            )