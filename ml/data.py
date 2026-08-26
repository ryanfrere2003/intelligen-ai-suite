""" interacts with the database to deliver data to svm or distilbert"""

import pandas as pd

from sklearn.model_selection import train_test_split

from database.database import get_connection

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

def get_user_mailbox_data():
    """ takes user data from the database emails table and returns a dataframe
    of all emails in the table"""
    conn = get_connection()
    data = pd.read_sql("SELECT * FROM Emails", conn)
    data.set_index("id",inplace=True)
    conn.close()
    return data

def report_classified_user_emails(mailbox_data:pd.DataFrame) -> pd.DataFrame:
    """ reports all of the emails a user currently has classified."""

    data = mailbox_data.copy()

    #return a table which contains only emails which have been classified
    data = data[data["classification"].notna()]

    return data

#TODO
def update_user_emails_table(email_dataframe:pd.DataFrame, results_frame:pd.DataFrame) -> None:
    """ takes processed information about user emails and updates the user emails table for
    future reference."""
    return