"""Provides search functionality for suite. Finds CANDIDATE pages which MAY contain PII. Saves results to database
Create .env file in root directory as follows (minus the arrows):
>USER_FIRST_NAME="FNAME"
>USER_MIDDLE_NAMES='["Name1", "Name2"...]'
>USER_LAST_NAME="LNAME"
>USER_EMAIL="email@email.com"
>USER_USERNAMES='["Username1", "Username2"...]'
>USER_LOCATIONS='["Location1","Location2"...]'
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

    LEAK_SITES = [
        "pastebin.com",
        "controlc.com",
        "ghostbin.com",
        "paste.ee",
        "justpaste.it",
    ]

    PEOPLE_SITES = [
        "whitepages.com",
        "truepeoplesearch.com",
        "fastpeoplesearch.com",
        "spokeo.com",
        "beenverified.com",
        "peekyou.com",
        "radaris.com",
        "addresses.com",
    ]

    SOCIAL_SITES = [
        "facebook.com",
        "linkedin.com",
        "instagram.com",
        "x.com",
        "reddit.com",
        "tiktok.com",
        "threads.net",
        "youtube.com",
        "pinterest.com",
        "flickr.com",
    ]

    DEV_SITES = [
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "stackoverflow.com",
        "npmjs.com",
        "pypi.org",
        "huggingface.co",
    ]

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

        queries = []

        # -----------------------------
        # Email
        # -----------------------------
        if USER_EMAIL:
            queries.extend([
                f'"{USER_EMAIL}"',
                f'"{USER_EMAIL}" site:pastebin.com',
                f'"{USER_EMAIL}" password',
                f'"{USER_EMAIL}" leak',
                f'"{USER_EMAIL}" breach',
            ])

        # -----------------------------
        # Usernames
        # -----------------------------
        for username in USER_USERNAME:
            queries.append(f'"{username}"')

            for site in (
                    Search.SOCIAL_SITES
                    + Search.DEV_SITES
                    + Search.LEAK_SITES
            ):
                queries.append(
                    f'"{username}" site:{site}'
                )

        # -----------------------------
        # Names
        # -----------------------------
        for name in Search.build_name_permutations():

            # Name only
            queries.append(f'"{name}"')

            # Name + email
            if USER_EMAIL:
                queries.append(
                    f'"{name}" "{USER_EMAIL}"'
                )

            # Name + usernames
            for username in USER_USERNAME:
                queries.extend([
                    f'"{name}" "{username}"',
                    f'"{name}" "{username}" site:pastebin.com',
                ])

            # Name + locations
            for location in USER_LOCATIONS:

                # General search
                queries.append(
                    f'"{name}" "{location}"'
                )

                # Social media
                for site in Search.SOCIAL_SITES:
                    queries.append(
                        f'"{name}" "{location}" site:{site}'
                    )

                # Developer sites
                for site in Search.DEV_SITES:
                    queries.append(
                        f'"{name}" "{location}" site:{site}'
                    )

                # Leak sites
                for site in Search.LEAK_SITES:
                    queries.append(
                        f'"{name}" "{location}" site:{site}'
                    )

                # People search sites
                for site in Search.PEOPLE_SITES:
                    queries.append(
                        f'"{name}" "{location}" site:{site}'
                    )

            # -----------------------------
            # Documents
            # -----------------------------
            queries.extend([
                f'"{name}" filetype:pdf',
                f'"{name}" filetype:doc',
                f'"{name}" filetype:docx',
                f'"{name}" filetype:ppt',
                f'"{name}" filetype:pptx',
                f'"{name}" filetype:xls',
                f'"{name}" filetype:xlsx',
                f'"{name}" CV',
                f'"{name}" resume',
            ])

            # -----------------------------
            # Contact information
            # -----------------------------
            queries.extend([
                f'"{name}" contact',
                f'"{name}" email',
                f'"{name}" phone',
                f'"{name}" address',
            ])

            # -----------------------------
            # Profile pages
            # -----------------------------
            queries.extend([
                f'"{name}" inurl:author',
                f'"{name}" inurl:profile',
                f'"{name}" inurl:profiles',
                f'"{name}" inurl:user',
                f'"{name}" inurl:users',
                f'"{name}" inurl:member',
                f'"{name}" inurl:members',
                f'"{name}" inurl:people',
                f'"{name}" inurl:person',
                f'intitle:"{name}"',
            ])

            # -----------------------------
            # Company / staff pages
            # -----------------------------
            queries.extend([
                f'"{name}" staff',
                f'"{name}" team',
                f'"{name}" profile',
                f'"{name}" employee',
                f'"{name}" contact',
            ])

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