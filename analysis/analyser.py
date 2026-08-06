from database.database import get_connection

from analysis.pii import PIIExtractor
from analysis.risk import RiskCalculator


class Analyser:
    """Analysis app orchestrator, processes crawled pages and calls pii and risk modules"""
    @staticmethod
    def analyse_pages():

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                extracted_text
            FROM CrawledPages
            WHERE verification_status='pending'
        """)

        pages = cursor.fetchall()

        for page in pages:

            page_id = page["id"]
            text = page["extracted_text"]

            print(f"Analysing page {page_id}")

            PIIExtractor.extract(
                connection,
                page_id,
                text,
            )

            RiskCalculator.calculate(
                connection,
                page_id,
            )

        connection.commit()
        connection.close()


if __name__ == "__main__":
    Analyser.analyse_pages()