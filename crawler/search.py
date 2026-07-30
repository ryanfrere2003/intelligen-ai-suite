"""Provides search functionality for suite. Finds CANDIDATE pages which MAY contain PII. Saves as """

from urllib.parse import urlparse

import pandas as pd
from ddgs import DDGS #DuckDuckGo Search

from config import (
    USER_FULL_NAME,
    USER_EMAIL,
    USER_USERNAME,
    USER_LOCATIONS,
)


class Search:
    """Performs DuckDuckGo searches for user information."""

    @staticmethod
    def build_queries() -> list[str]:
        """Generate search queries."""

        queries = [
            f'"{USER_EMAIL}"',
            f'"{USER_USERNAME}"',
            f'"{USER_EMAIL}" site:pastebin.com',
        ]

        # Name + known locations
        for location in USER_LOCATIONS:
            queries.extend([
                f'"{USER_FULL_NAME}" "{location}"',
                f'"{USER_FULL_NAME}" "{location}" site:linkedin.com',
                f'"{USER_FULL_NAME}" "{location}" site:github.com',
                f'"{USER_FULL_NAME}" "{location}" site:facebook.com',
                f'"{USER_FULL_NAME}" "{location}" site:reddit.com',
                f'"{USER_FULL_NAME}" "{location}" site:x.com',
            ])

        # Name + username
        queries.append(f'"{USER_FULL_NAME}" "{USER_USERNAME}"')

        # Name + email (if the search engine indexes it)
        queries.append(f'"{USER_FULL_NAME}" "{USER_EMAIL}"')

        # Potential data leaks
        queries.append(f'"{USER_FULL_NAME}" "{USER_USERNAME}" site:pastebin.com')

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
    def search(max_results: int = 10) -> pd.DataFrame:
        """
        Search DuckDuckGo for personal information.

        Returns
        -------
        pandas.DataFrame
            Columns:
                source
                query
                title
                url
                snippet
        """

        results = []
        seen_urls = set()

        with DDGS() as ddgs:

            for query in Search.build_queries():

                print(f"Searching: {query}")

                try:
                    search_results = ddgs.text(
                        query,
                        max_results=max_results,
                    )

                    for result in search_results:

                        url = result.get("href", "")

                        if not url:
                            continue

                        url = Search.canonical(url)

                        if url in seen_urls:
                            continue

                        seen_urls.add(url)

                        results.append(
                            {
                                "source": "duckduckgo",
                                "query": query,
                                "title": result.get("title", ""),
                                "url": url,
                                "snippet": result.get("body", ""),
                            }
                        )

                except Exception as e:
                    print(f"Search failed for '{query}': {e}")

        df = pd.DataFrame(results)

        if not df.empty:
            df = df.drop_duplicates(subset="url").reset_index(drop=True)

        return df


if __name__ == "__main__":

    df = Search.search(max_results=10)

    print(df.head())
    print()
    print(f"{len(df)} unique results found")

    df.to_csv("search_results.csv", index=False)