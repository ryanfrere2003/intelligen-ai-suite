"""Provides search functionality for suite. Finds CANDIDATE pages which MAY contain PII. Saves results to database
Create .env file in root directory as follows (minus the arrows):
>USER_FULL_NAME=FNAME LNAME
>USER_EMAIL=email@email.com
>USER_USERNAMES=["Username1", "Username2"...]
>USER_LOCATIONS=["Location1","Location2"...]
>
"""

from database.database import get_connection
from ddgs import DDGS #DuckDuckGo Search
from urllib.parse import urlparse
from itertools import combinations

from config import (
    USER_FIRST_NAME,
    USER_MIDDLE_NAMES,
    USER_LAST_NAME,
    USER_EMAIL,
    USER_USERNAME,
    USER_LOCATIONS,
)


class Search:
    """Performs DuckDuckGo searches for user information."""

    @staticmethod
    def build_name_permutations() -> list[str]:
        """Generate useful name permutations."""

        middle_names = USER_MIDDLE_NAMES or []

        names = set()

        # First Last
        names.add(f"{USER_FIRST_NAME} {USER_LAST_NAME}")

        # First Middle Last
        for i in range(1, len(middle_names) + 1):
            for combo in combinations(middle_names, i):
                names.add(
                    f"{USER_FIRST_NAME} {' '.join(combo)} {USER_LAST_NAME}"
                )

        # Full name
        if middle_names:
            names.add(
                f"{USER_FIRST_NAME} {' '.join(middle_names)} {USER_LAST_NAME}"
            )

        return sorted(names)

    @staticmethod
    def build_queries() -> list[str]:
        """Generate search queries."""

        queries = [
            f'"{USER_EMAIL}"',
            f'"{USER_EMAIL}" site:pastebin.com',
            *[f'"{username}"' for username in USER_USERNAME],
        ]

        name_variants = Search.build_name_permutations()

        for name in name_variants:

            # Name + known locations
            for location in USER_LOCATIONS:
                queries.extend([
                    f'"{name}" "{location}"',
                    f'"{name}" "{location}" site:linkedin.com',
                    f'"{name}" "{location}" site:github.com',
                    f'"{name}" "{location}" site:facebook.com',
                    f'"{name}" "{location}" site:reddit.com',
                    f'"{name}" "{location}" site:x.com',
                ])

            # Name + each username
            for username in USER_USERNAME:
                queries.append(f'"{name}" "{username}"')

                # Potential data leaks
                queries.append(
                    f'"{name}" "{username}" site:pastebin.com'
                )

            # Name + email
            queries.append(f'"{name}" "{USER_EMAIL}"')

        # Remove duplicates while preserving order
        return list(dict.fromkeys(queries))

    @staticmethod
    def canonical(url: str) -> str:
        """
        Remove query strings and fragments from URLs so duplicate
        pages aren't stored multiple times.
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    @staticmethod
    def search(max_results: int = 10) -> None:
        """
        Search DuckDuckGo for candidate pages and store them
        in the SearchResults table.
        """

        connection = get_connection()
        cursor = connection.cursor()

        seen_urls = set()

        with DDGS() as ddgs:

            for query in Search.build_queries():

                print(f"Searching: {query}")

                try:

                    search_results = ddgs.text(
                        query,
                        max_results=max_results,
                    )

                    for rank, result in enumerate(search_results, start=1):

                        url = result.get("href", "")

                        if not url:
                            continue

                        url = Search.canonical(url)

                        if url in seen_urls:
                            continue

                        seen_urls.add(url)

                        parsed = urlparse(url)

                        cursor.execute(
                            """
                            INSERT
                            OR IGNORE INTO SearchResults
                                (
                                    search_engine,
                                    search_query,
                                    url,
                                    domain,
                                    page_title,
                                    snippet,
                                    result_rank
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                "duckduckgo",
                                query,
                                url,
                                parsed.netloc,
                                result.get("title", ""),
                                result.get("body", ""),
                                rank,
                            ),
                        )

                except Exception as e:
                    print(f"Search failed for '{query}': {e}")

        connection.commit()
        connection.close()


if __name__ == "__main__":

    df = Search.search(max_results=10)

    print(df.head())
    print()
    print(f"{len(df)} unique results found")

    df.to_csv("search_results.csv", index=False)