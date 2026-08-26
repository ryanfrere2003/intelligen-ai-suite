""" performs corrective actions on emails which the svm and distilbert models scored incorrectly on
by assigning a human in loop label that is commited to the database using various functions to increase
the accuracy of future training rounds"""

import pandas as pd

from config import PROJECT_ROOT

from database.database import get_connection

from .data import get_training_data
from .data_labeller import LABEL_KEYWORDS

#=====================
#helper functions
#=====================

def update_trainingdata(email_id: int, corrected_label: str) -> None:
    """Update the human-corrected label for an email."""
    conn = get_connection()
    conn.execute("""UPDATE TrainingData SET human_label = ?, human_verified = ? WHERE id = ?""",(corrected_label, True, email_id))
    conn.commit()
    conn.close()
    return

# =====================
# human in loop actions
# =====================

def corrective_actions() -> None:
    """Review and manually correct SVM classification errors."""

    corrections = pd.read_csv(
        f"{PROJECT_ROOT}/data/human_review_cases.csv",
        index_col="email_id"
    )

    labels = list(LABEL_KEYWORDS.keys())

    for email_id, item in corrections.iterrows():

        email = get_training_data(email_id).iloc[0]

        print("")
        print(f"Email ID: {email_id}")
        print(f"Sender: {email['original_sender_string']}")
        print(f"Subject: {email['subject']}")
        print(f"Body: {email['body']}")
        print()

        print("Select the correct label:")

        for number, label in enumerate(labels):
            print(f"{number}. {label}")

        while True:
            try:
                choice = int(input("\nEnter choice: "))

                if 0 <= choice < len(labels):
                    selected_label = labels[choice]
                    break

                print(
                    f"Please enter a number between "
                    f"0 and {len(labels) - 1}."
                )

            except ValueError:
                print("Please enter a number.")

        update_trainingdata(email_id,selected_label)

    print("corrections completed and commited to database.")
    print("ending human in loop correction actions. you can now run another training loop.")
    return
