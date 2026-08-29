import textwrap
import webbrowser

from database.database import get_connection


WIDTH = 80


class Review:

    @staticmethod
    def review_pending() -> None:
        """CLI interface for user to review analysed pages and individual PII entities."""

        connection = get_connection()
        cursor = connection.cursor()

        print("\nReview Mode")
        print("-" * WIDTH)
        print("[1] Review candidates (score > 0)")
        print("[2] Review possible false negatives (score = 0)")
        print("[3] Review all pending")
        print("[4] Review previous decisions")
        print("[Q] Quit")

        mode = input("> ").strip().lower()

        if mode == "q":
            connection.close()
            return

        score_filter = ""
        status_filter = ""

        if mode == "1":
            status_filter = """
                AND cp.verification_status = 'pending'
            """
            score_filter = """
                AND cp.risk_score > 0
            """

        elif mode == "2":
            status_filter = """
                AND cp.verification_status = 'pending'
            """
            score_filter = """
                AND cp.risk_score = 0
            """

        elif mode == "3":
            status_filter = """
                AND cp.verification_status = 'pending'
            """

        elif mode == "4":
            status_filter = """
                AND cp.verification_status IN (
                    'verified',
                    'false_positive',
                    'ignored'
                )
            """

        else:
            print("Invalid option.")
            connection.close()
            return

        cursor.execute(
            f"""
            SELECT
                cp.id,
                cp.page_title,
                cp.extracted_text,
                cp.risk_score,
                cp.verification_status,
                sr.url
            FROM CrawledPages cp
            JOIN SearchResults sr
                ON cp.search_result_id = sr.id
            WHERE 1=1
            {status_filter}
            {score_filter}
            ORDER BY cp.risk_score DESC,
                     cp.id ASC
            """
        )

        pages = cursor.fetchall()

        if not pages:
            print("No pages available for review.")
            connection.close()
            return

        for page in pages:

            page_id = page["id"]

            print("\n" + "=" * WIDTH)
            print(f"Page ID     : {page_id}")
            print(f"Title       : {page['page_title'] or 'Unknown'}")
            print(f"Risk Score  : {page['risk_score']}")
            print(f"Status      : {page['verification_status']}")
            print(f"URL         : {page['url']}")
            print("=" * WIDTH)

            cursor.execute(
                """
                SELECT
                    id,
                    entity_type,
                    entity_value,
                    confidence,
                    status
                FROM PIIEntities
                WHERE page_id = ?
                ORDER BY confidence DESC, entity_type
                """,
                (page_id,),
            )

            entities = cursor.fetchall()

            print("\nDetected PII")
            print("-" * WIDTH)

            if entities:

                for index, entity in enumerate(entities, start=1):

                    confidence = entity["confidence"]

                    if confidence is None:
                        confidence_text = "N/A"
                    else:
                        confidence_text = f"{confidence:.2f}"

                    print(
                        f"[{index}] "
                        f"{entity['entity_type']:<15}"
                        f"{entity['entity_value']} "
                        f"({confidence_text}) "
                        f"[{entity['status']}]"
                    )

            else:
                print("None")

            print("\nPreview")
            print("-" * WIDTH)

            preview = (page["extracted_text"] or "")[:1000]

            wrapped_preview = textwrap.fill(
                preview,
                width=WIDTH,
                break_long_words=False,
                break_on_hyphens=False,
            )

            print(wrapped_preview)

            print("-" * WIDTH)
            print("[V] Review PII entities")
            print("[F] Mark page as False Positive")
            print("[I] Ignore page")
            print("[R] Reset page to Pending")
            print("[O] Open URL")
            print("[S] Skip")
            print("[Q] Quit")

            while True:

                choice = input("> ").strip().lower()

                if choice == "o":
                    webbrowser.open(page["url"])
                    continue

                if choice == "v":
                    status="verified"

                    Review.review_entities(
                        cursor,
                        connection,
                        page_id,
                    )

                elif choice == "f":
                    status = "false_positive"

                elif choice == "i":
                    status = "ignored"

                elif choice == "r":
                    status = "pending"

                elif choice == "s":
                    break

                else:
                    print("Invalid option.")
                    continue

                cursor.execute(
                    """
                    UPDATE CrawledPages
                    SET verification_status = ?
                    WHERE id = ?
                    """,
                    (
                        status,
                        page_id,
                    ),
                )

                connection.commit()

                print(f"✓ Page marked as {status}.")
                break

        connection.close()

    @staticmethod
    def review_entities(cursor, connection, page_id: int) -> None:
        """Review individual PII entities for a page."""

        while True:

            cursor.execute(
                """
                SELECT
                    id,
                    entity_type,
                    entity_value,
                    confidence,
                    status
                FROM PIIEntities
                WHERE page_id = ?
                ORDER BY confidence DESC, entity_type
                """,
                (page_id,),
            )

            entities = cursor.fetchall()

            if not entities:
                print("\nNo PII entities found for this page.")
                return

            print("\nPII Entity Review")
            print("-" * WIDTH)

            for index, entity in enumerate(entities, start=1):

                confidence = entity["confidence"]

                if confidence is None:
                    confidence_text = "N/A"
                else:
                    confidence_text = f"{confidence:.2f}"

                print(
                    f"[{index}] "
                    f"{entity['entity_type']:<15}"
                    f"{entity['entity_value']} "
                    f"({confidence_text}) "
                    f"[{entity['status']}]"
                )

            print("-" * WIDTH)
            print("[V] Verify entity")
            print("[F] Mark entity as False Positive")
            print("[I] Ignore entity")
            print("[R] Reset entity to Pending")
            print("[B] Back")
            print("[Q] Quit")

            choice = input("> ").strip().lower()

            if choice == "b":
                return

            if choice == "q":
                connection.close()
                raise SystemExit

            if choice not in ("v", "f", "i", "r"):
                print("Invalid option.")
                continue

            selection = input(
                "Enter entity number(s), separated by commas: "
            ).strip()

            try:
                indexes = [
                    int(value.strip())
                    for value in selection.split(",")
                ]
            except ValueError:
                print("Invalid entity selection.")
                continue

            valid_indexes = range(1, len(entities) + 1)

            if any(index not in valid_indexes for index in indexes):
                print("Invalid entity number.")
                continue

            if choice == "v":
                status = "verified"
            elif choice == "f":
                status = "false_positive"
            elif choice == "i":
                status = "ignored"
            else:
                status = "pending"

            for index in indexes:

                entity = entities[index - 1]

                cursor.execute(
                    """
                    UPDATE PIIEntities
                    SET status = ?
                    WHERE id = ?
                    """,
                    (
                        status,
                        entity["id"],
                    ),
                )

                print(
                    f"✓ {entity['entity_type']}: "
                    f"{entity['entity_value']} "
                    f"→ {status}"
                )

            connection.commit()


if __name__ == "__main__":
    Review.review_pending()