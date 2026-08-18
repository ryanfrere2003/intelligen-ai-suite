import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

import joblib

from database import database 

from config import GMAIL_READ_ONLY

#=======================================================
#ML model loader will not funtion without training round
#=======================================================
model = joblib.load("email_classifier.pkl")
#=======================================================




#=====================
#functions
#=====================
def import_user_inbox() -> pd.DataFrame:
    """ only use this command if the user inbox has never been imported
    else use update mailbox function."""

    

        "Emails": """
    CREATE TABLE IF NOT EXISTS Emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        message_id TEXT UNIQUE,
        sender_name TEXT,
        sender_email_username TEXT NOT NULL,
        sender_email_domain TEXT NOT NULL,
        original_sender_string TEXT NOT NULL,

        subject TEXT NOT NULL,
        body TEXT NOT NULL,             
        date DATETIME,
        
        is_read INTEGER DEFAULT 0,

        classification TEXT,
        confidence REAL,
        processed INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,



def get_email() -> pd.DataFrame:
    conn = database.get_connection()
    data = pd.read_sql("SELECT * FROM TrainingData", conn)

    #remove unlabelled and ambiguous
    print(f"data is currently contains: ({len(data)}) unclassified emails.")
    data = data[~data["label"].isin(["unlabelled","ambiguous"])]
    print(f"after filtering to data requiring classification contains: ({len(data)}) emails.")

    #state health of the sample
    print(data["label"].value_counts())

    return data

def classify_email(data) -> None:
    """ classifys an email using the model stored data"""
    email_text = (
        email["original_sender_string"]
        + " "
        + email["subject"]
        + " "
        + email["body"]
    )


