from datetime import datetime

import requests

from database.database import get_connection
from parser import PageParser


HEADERS = {
    "User-Agent": (
        "Privacy Intelligence/1.0 "
        "(Mozilla/5.0 compatible; research project)"
    )
}


class Scraper:

    @staticmethod
    def scrape_pending() -> None:
        """Scrape all pending search results."""

        connection = get_connection()
        cursor = connection.cursor()

        session = requests.Session()
        session.headers.update(HEADERS)

        cursor.execute(
            """
            SELECT id, url
            FROM SearchResults
            WHERE crawl_status = 'pending'
            """
        )

        pages = cursor.fetchall()

        for page in pages:

            search_result_id = page["id"]
            url = page["url"]

            print(f"Scraping {url}")

            try:

                response = session.get(
                    url,
                    timeout=15,
                    allow_redirects=True,
                )

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type",
                    "",
                ).lower()

                if "text/html" not in content_type:

                    cursor.execute(
                        """
                        UPDATE SearchResults
                        SET
                            crawl_status='unsupported',
                            last_crawled=?,
                            crawl_attempts=crawl_attempts+1
                        WHERE id=?
                        """,
                        (
                            datetime.utcnow(),
                            search_result_id,
                        ),
                    )

                    connection.commit()
                    continue

                parsed = PageParser.parse(
                    response.text,
                    response.url,
                )

                # Store the page
                cursor.execute(
                    """
                    INSERT INTO CrawledPages
                    (
                        search_result_id,
                        http_status,
                        content_type,
                        page_title,
                        description,
                        keywords,
                        html,
                        extracted_text
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        search_result_id,
                        response.status_code,
                        content_type,
                        parsed.title,
                        parsed.description,
                        parsed.keywords,
                        response.text,
                        parsed.text,
                    ),
                )

                page_id = cursor.lastrowid

                # Store email addresses
                for email in parsed.emails:

                    cursor.execute(
                        """
                        INSERT INTO PageEmails
                        (
                            page_id,
                            email
                        )
                        VALUES (?, ?)
                        """,
                        (
                            page_id,
                            email,
                        ),
                    )

                # Store images
                for image in parsed.images:

                    cursor.execute(
                        """
                        INSERT INTO PageImages
                        (
                            page_id,
                            image_url
                        )
                        VALUES (?, ?)
                        """,
                        (
                            page_id,
                            image,
                        ),
                    )

                # Store contact links
                for link in parsed.contact_links:

                    cursor.execute(
                        """
                        INSERT INTO PageLinks
                        (
                            page_id,
                            url,
                            link_type
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            page_id,
                            link,
                            "contact",
                        ),
                    )

                # Store privacy links
                for link in parsed.privacy_links:

                    cursor.execute(
                        """
                        INSERT INTO PageLinks
                        (
                            page_id,
                            url,
                            link_type
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            page_id,
                            link,
                            "privacy",
                        ),
                    )

                # Store social links
                for link in parsed.social_links:

                    cursor.execute(
                        """
                        INSERT INTO PageLinks
                        (
                            page_id,
                            url,
                            link_type
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            page_id,
                            link,
                            "social",
                        ),
                    )

                cursor.execute(
                    """
                    UPDATE SearchResults
                    SET
                        crawl_status='success',
                        last_crawled=?,
                        crawl_attempts=crawl_attempts+1
                    WHERE id=?
                    """,
                    (
                        datetime.utcnow(),
                        search_result_id,
                    ),
                )

                connection.commit()

                print(
                    f"✓ {parsed.title}"
                )
                print(
                    f"  Emails: {len(parsed.emails)}"
                )
                print(
                    f"  Images: {len(parsed.images)}"
                )
                print(
                    f"  Contact Links: {len(parsed.contact_links)}"
                )
                print(
                    f"  Privacy Links: {len(parsed.privacy_links)}"
                )
                print(
                    f"  Social Links: {len(parsed.social_links)}"
                )

            except Exception as e:

                print(f"Failed: {e}")

                cursor.execute(
                    """
                    UPDATE SearchResults
                    SET
                        crawl_status='failed',
                        last_crawled=?,
                        crawl_attempts=crawl_attempts+1
                    WHERE id=?
                    """,
                    (
                        datetime.utcnow(),
                        search_result_id,
                    ),
                )

                connection.commit()

        connection.close()


if __name__ == "__main__":
    Scraper.scrape_pending()