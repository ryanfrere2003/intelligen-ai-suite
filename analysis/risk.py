class RiskCalculator:

    @staticmethod
    def calculate(connection, page_id):

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

        print(
            f"Page {page_id} risk score: {score}"
        )