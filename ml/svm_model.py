""" contains the function to initiate the SVM linear vectorizer model."""

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

import joblib

from config import SVM_MODEL

def svm(load: bool = False) -> Pipeline | None:
    """Load an existing SVM model or create a new SVM model."""

    if load:
        try:
            model = joblib.load(
                f"{SVM_MODEL}/email_classifier.pkl"
            )
            print("Loaded an existing SVM model.")
            return model

        except FileNotFoundError:
            print("No existing SVM model found.")

    print("Initialising a new SVM model...")

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                max_features=10000
            )
        ),
        (
            "classifier",
            LinearSVC(
                class_weight="balanced"
            )
        )
    ])

    return model
