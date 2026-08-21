from database.database import get_connection
from pathlib import Path


def add_demo_page():

    connection = get_connection()
    cursor = connection.cursor()

    file_path = Path("data/demo_page.html").resolve()

    url = file_path.as_uri()

    cursor.execute(
        """
        INSERT INTO SearchResults
        (
            search_engine,
            search_query,
            query_confidence,
            url,
            domain,
            page_title,
            snippet,
            result_rank,
            crawl_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test",
            "PII demonstration",
            1.0,
            url,
            "local-test",
            "PII Detection Demonstration",
            "Synthetic PII demonstration page",
            1,
            "pending",
        ),
    )

    connection.commit()
    connection.close()

    print(f"Added test page: {url}")


if __name__ == "__main__":
    add_demo_page()