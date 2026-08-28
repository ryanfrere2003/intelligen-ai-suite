""" interacts with the database to deliver data to svm or distilbert"""

import pandas as pd

from sklearn.model_selection import train_test_split

from database.database import get_connection
from .data_preprocess import load_mailbox_data, clean_mailbox_data, commit_data_to_db
#====================
#helper functions
#====================
def training_data_available() -> bool:
    """Check whether TrainingData contains more than one record."""
    conn = get_connection()
    result = conn.execute("SELECT COUNT(*) FROM TrainingData").fetchone()[0]
    conn.close()
    return result > 1

#====================
# Both states
#====================

def prepare_data(df:pd.DataFrame) -> pd.DataFrame:
    """Prepare email data for either model from the database takes in one dataframe
    and returns a tuple of 2 randomly sorted dataframes proving test data and
    training data."""

    df = df.copy()

    df["email_text"] = (
        df["original_sender_string"].fillna("")
        + " "
        + df["subject"].fillna("")
        + " "
        + df["body"].fillna("")
    )

    return df

#====================
# Training Functions
#====================

def get_training_data(email_id:int| None=None) -> pd.DataFrame:
    """ takes training data from the database TraininData table and returns a dataframe
    of all emails in the table
        Requires:
            email_id(int): a known email integer.
            email_id(none): all emails in the table.
        Returns:
            A dataframe object containing the query result."""
        
    conn = get_connection()

    if email_id is None:
        data = pd.read_sql("SELECT * FROM TrainingData", conn)

        #remove unlabelled and ambiguous
        print(f"data is currently contains: ({len(data)}) emails.")
        data = data[~data["label"].isin(["unlabelled","ambiguous"])]
        print(f"after filtering to suitable data contains: ({len(data)}) emails.")

        #state health of the sample
        print(data["label"].value_counts())

    else:
        data = pd.read_sql("SELECT * FROM TrainingData WHERE id=?",conn ,params=(email_id,))

    data.set_index("id",inplace=True)

    #formats labels and ensures retrained labels are used if it has been human varified
    data["training_label"] = data["human_label"].where(data["human_verified"].astype(bool),data["label"])

    return data

def prepare_data_for_training_split(df:pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame]:
    """ splits database training data tables into training and testing data for
    machine learning training. Do not use this function unless training a model. """

    #outputs a tuple of dataframes
    training_data:pd.DataFrame
    testing_data:pd.DataFrame
    
    training_data,testing_data= train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["training_label"]
    )
    return training_data, testing_data

#====================
# Regular functions
#====================

def initialize_training_data() -> None:
    """ initializes the training data and database"""

    if not training_data_available():
        mailbox_raw = load_mailbox_data()
        mailbox_clean = clean_mailbox_data(mailbox_raw)
        commit_data_to_db(mailbox_clean)

    else:
        choice = input("Training data detected, do you want to reset the training database? (Y/N): ")
        if choice.upper() == "Y":
            conn = get_connection()
            conn.execute("DELETE FROM TrainingData")
            conn.commit()
            conn.close()
            print("training data deleted. please call the training function again.")
    return
