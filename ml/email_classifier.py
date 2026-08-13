import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

import joblib

from database import database 


model = joblib.load("email_classifier.pkl")

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
