class RiskCalculator:

    @staticmethod
    def calculate(connection, page_id):
        """Helper function for calculating risk scores for a given page."""
        cursor = connection.cursor()

        cursor.execute("""
            SELECT entity_type
            FROM PIIEntities
            WHERE page_id=?
        """, (page_id,))

        score = 0

        for row in cursor.fetchall():

            if row["entity_type"] == "email":
                score += 25

            elif row["entity_type"] == "phone":
                score += 40

            elif row["entity_type"] == "username":
                score += 15

            elif row["entity_type"] == "name":
                score += 10

            elif row["entity_type"] == "location":
                score += 5

        # Prevent score exceeding 100
        score = min(score, 100)

        cursor.execute("""
            UPDATE CrawledPages
            SET risk_score=?
            WHERE id=?
        """, (score, page_id))

        print(f"Page {page_id} risk score: {score}")