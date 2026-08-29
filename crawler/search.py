"""Provides search functionality for suite. Finds CANDIDATE pages which MAY contain PII. Saves results to database
Create .env file in root directory as follows (minus the arrows):
>USER_FIRST_NAME="FNAME"
>USER_MIDDLE_NAMES='["Name1", "Name2"...]'
>USER_LAST_NAME="LNAME"
>USER_EMAIL="email@email.com"
>USER_USERNAMES='["Username1", "Username2"...]'
>USER_LOCATIONS='["Location1","Location2"...]'
>USER_NUMBERS='["Phone1","Phone2"...]'
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
    USER_NUMBERS
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
            for combo in combinations(middle_names, i): #Generates any possible combination of given middle names along with first and last
                names.add(
                    f"{USER_FIRST_NAME} {' '.join(combo)} {USER_LAST_NAME}"
                )

        # Full name
        if middle_names:
            names.add(
                f"{USER_FIRST_NAME} {' '.join(middle_names)} {USER_LAST_NAME}"
            )
        print(sorted(names))
        return sorted(names)

    @staticmethod
    def email_queries():

        queries = []

        if not USER_EMAIL:
            return queries

        queries.extend([
            f'"{USER_EMAIL}"',
            f'"{USER_EMAIL}" leak',
            f'"{USER_EMAIL}" breach',
            f'"{USER_EMAIL}" password',
        ])

        return queries

    @staticmethod
    def phone_queries():

        queries = []

        for number in USER_NUMBERS:
            queries.extend([
                f'"{number}"',
                f'"{number}" leak',
                f'"{number}" pastebin',
            ])

        return queries

    @staticmethod
    def username_queries():

        queries = []

        for username in USER_USERNAME:

            queries.append(
                f'"{username}"'
            )

            for site in (
                    Search.SOCIAL_SITES
                    + Search.DEV_SITES
                    + Search.LEAK_SITES
            ):
                queries.append(
                    f'"{username}" site:{site}'
                )

        return queries

    @staticmethod
    def identity_queries():

        queries = []

        names = Search.build_name_permutations()

        for name in names:

            for location in USER_LOCATIONS:
                queries.extend([
                    f'"{name}" "{location}"',
                ])

            for username in USER_USERNAME:
                queries.extend([
                    f'"{name}" "{username}"',
                ])

            if USER_EMAIL:
                queries.append(
                    f'"{name}" "{USER_EMAIL}"'
                )

            for number in USER_NUMBERS:
                queries.append(
                    f'"{name}" "{number}"'
                )

        return queries

    @staticmethod
    def get_query_confidence(query: str) -> float:
        """
        Estimate confidence that a search query relates to the user. Called before search result insertion into db
        """

        query = query.lower()

        # Exact email
        if USER_EMAIL and USER_EMAIL.lower() in query:
            return 1.0

        # Exact phone
        for number in USER_NUMBERS:
            if number.lower() in query:
                return 1.0

        # Username
        for username in USER_USERNAME:
            if username.lower() in query:
                return 0.9

        # Name + location
        for name in Search.build_name_permutations():
            for location in USER_LOCATIONS:
                if (
                        name.lower() in query
                        and location.lower() in query
                ):
                    return 0.6

        # Name only
        for name in Search.build_name_permutations():
            if name.lower() in query:
                return 0.2

        return 0.0

    @staticmethod
    def build_queries():
        """Construct queries from helper functions"""

        queries = []

        queries += Search.email_queries()

        queries += Search.phone_queries()

        queries += Search.username_queries()

        queries += Search.identity_queries()

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
                            INSERT OR IGNORE INTO SearchResults
                                (
                                    search_engine,
                                    search_query,
                                    query_confidence,
                                    url,
                                    domain,
                                    page_title,
                                    snippet,
                                    result_rank
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                "duckduckgo",
                                query,
                                Search.get_query_confidence(query),
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

    print("Search complete.")