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

def filter_required_interventions(human_corrections_df:pd.DataFrame) -> pd.DataFrame:
    """ returns a dataframe which tells the application which email
    require a human in loop intervention, filting out any which have
    already had such interventions."""
    
    hil_data = human_corrections_df.copy()

    email_ids = hil_data.index.tolist()
    placeholders = ",".join("?" for _ in email_ids) 

    conn = get_connection()
    query = f"""SELECT * FROM TrainingData WHERE id IN ({placeholders}) AND human_verified = ? """
    data = pd.read_sql_query(query,conn,params=(*email_ids, False))
    data = data.set_index("id")
    conn.close()
    return data
  
# =====================
# human in loop actions
# =====================

def corrective_actions() -> None:
    """Review and manually correct model classification errors."""

    try:
        corrections = pd.read_csv(f"{PROJECT_ROOT}/data/human_review_cases.csv",index_col="email_id")
    except FileNotFoundError:
        print("""could not locate 'human_review_cases.csv' have you performed any training loop yet?""")
        return
    
    filter_df = filter_required_interventions(corrections)

    #only return emails awaiting verification by a human incase the list was not fully completred last time.
    corrections = corrections[corrections.index.isin(filter_df.index)]
    
    labels = list(LABEL_KEYWORDS.keys())
    corrections_completed = 0

    for email_id, item in corrections.iterrows():

        email = get_training_data(email_id).iloc[0]
        body = email['body']

        print("")
        print(f"Email ID: {email_id}")
        print(f"Sender: {email['original_sender_string']}")
        print(f"Subject: {email['subject']}")
        print(f"Body: {body[:1000]}{'...' if len(body) > 1000 else ''}")
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

        update_trainingdata(email_id, selected_label)

        corrections_completed += 1

        print(f"Correction {corrections_completed} committed to database.")

        # Ask if the user wishes to continue after every 10 corrections
        if corrections_completed % 10 == 0:

            while True:
                choice = input("You have completed 10 corrections, would you like to continue? (Y/N): ").upper()

                if choice == "Y":
                    break

                if choice == "N":
                    print("\nHuman in loop corrections stopped by user.")
                    return

                print("Please enter Y or N.")

    print(f"All human in loop corrections have been completed. a total of ({corrections_completed}) corrections were made.")
    return
