import textwrap
import webbrowser

from database.database import get_connection


WIDTH = 80


class Review:

    @staticmethod
    def review_pending() -> None:
        """Review analysed pages awaiting user verification."""

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                cp.id,
                cp.page_title,
                cp.extracted_text,
                cp.risk_score,
                cp.match_score,
                cp.verification_status,
                sr.url
            FROM CrawledPages cp
            JOIN SearchResults sr
                ON cp.search_result_id = sr.id
            WHERE cp.verification_status='pending'
            ORDER BY cp.risk_score DESC, cp.id ASC
            """
        )

        pages = cursor.fetchall()

        if not pages:
            print("No pages awaiting review.")
            connection.close()
            return

        for page in pages:

            page_id = page["id"]

            print("\n" + "=" * WIDTH)
            print(f"Page ID     : {page_id}")
            print(f"Title       : {page['page_title'] or 'Unknown'}")
            print(f"Risk Score  : {page['risk_score']}")
            print(f"Match Score : {page['match_score']}")
            print(f"URL         : {page['url']}")
            print("=" * WIDTH)

            cursor.execute(
                """
                SELECT
                    entity_type,
                    entity_value,
                    confidence
                FROM PIIEntities
                WHERE page_id=?
                ORDER BY confidence DESC, entity_type
                """,
                (page_id,),
            )

            entities = cursor.fetchall()

            print("\nDetected PII")
            print("-" * WIDTH)

            if entities:
                for entity in entities:
                    print(
                        f"{entity['entity_type']:<15}"
                        f"{entity['entity_value']} "
                        f"({entity['confidence']:.2f})"
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
            print()
            print("[V] Verify")
            print("[F] False Positive")
            print("[I] Ignore")
            print("[O] Open URL")
            print("[S] Skip")
            print("[Q] Quit")

            while True:

                choice = input("> ").strip().lower()

                if choice == "o":
                    webbrowser.open(page["url"])
                    continue

                if choice == "v":
                    cursor.execute(
                        """
                        UPDATE CrawledPages
                        SET verification_status='verified'
                        WHERE id = ?
                        """,
                        (page_id,),
                    )

                    connection.commit()

                    print("✓ Marked as verified.")
                    break

                if choice == "f":
                    cursor.execute(
                        """
                        UPDATE CrawledPages
                        SET verification_status='false_positive'
                        WHERE id = ?
                        """,
                        (page_id,),
                    )

                    connection.commit()

                    print("✓ Marked as false positive.")
                    break

                if choice == "i":
                    cursor.execute(
                        """
                        UPDATE CrawledPages
                        SET verification_status='ignored'
                        WHERE id = ?
                        """,
                        (page_id,),
                    )

                    connection.commit()

                    print("✓ Marked as ignored.")
                    break

                if choice == "s":
                    break

                if choice == "q":
                    connection.close()
                    return

                print("Invalid option.")

        connection.close()


if __name__ == "__main__":
    Review.review_pending()