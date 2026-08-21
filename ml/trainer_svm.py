""" loads data from training tables and allows analysis by the AI agent"""

import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

import joblib
from datetime import datetime

from database import database
from config import MODEL_PATH, PROJECT_ROOT
from .data_labeller import LABEL_KEYWORDS
from .data import get_training_data

#=================
# Helpers
#=================
    
def update_trainingdata(email_id:int,corrected_label:str) -> None:
    """Update the human-corrected label for an email. requires
    a valid email_id and corrected level"""



    conn = database.get_connection()

    conn.execute(
        """
        UPDATE TrainingData
        SET human_label = ?,
            human_verified = ?
        WHERE id = ?
        """,
        (corrected_label, True, email_id)
    )

    conn.commit()
    conn.close()

    return

def record_training_performance(report) -> None:
    """ formats and records the model performance data for that
    training run to check on accuracy and improvement saving as a csv for inspection.
    """
    report_path = PROJECT_ROOT / "data" / "training_performance.csv"

    report_df = pd.DataFrame(report).transpose()

    report_df.index.name = "label"
    report_df.reset_index(inplace=True)

    # Add identifier and round data
    report_df["timestamp"] = datetime.now()
    report_df = report_df.round(2)

    if report_path.exists():
        existing = pd.read_csv(report_path)

        report_df = pd.concat(
            [existing, report_df],
            ignore_index=True
        )

    report_df.to_csv(report_path,index=False)

#=================
# Main Functions
#=================

def ml_model(load=False) -> Pipeline | None:
    """Create a new ML model or load the existing one."""

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

    #if no training data exists
    if load:
        try:
            model = joblib.load(f"{MODEL_PATH}/email_classifier.pkl")
        except FileNotFoundError:
            print("could not find previous training data")
            return None

    return model

def training_round(data: pd.DataFrame,model_load=False,) -> tuple:
    """takes a filtered dataframe and concatenates fields 
    for ML training, running it against the ML model."""

    df = data.copy()

    print(df.head(10))

    df["email_text"] = (
        df["original_sender_string"]
        + " "
        + df["subject"]
        + " "
        + df["body"]
    )

    X = df["email_text"]
    y = df["training_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    #training information
    print(f"Training emails: {len(X_train)}")
    print(f"Testing emails: {len(X_test)}")
    print("\nTraining distribution:")
    print(y_train.value_counts())
    print("\nTesting distribution:")
    print(y_test.value_counts())

    model = ml_model(load=model_load)

    print("\nTraining model...")

    model.fit(X_train, y_train)

    return model, X_test, y_test

def commit_learning(model) -> None:
    """ saves learning in model DIR using pkl file"""
    joblib.dump(model, f"{MODEL_PATH}/email_classifier.pkl")
    return

def perform_training_loop() -> None:
    """ performs a full training loop"""

    df = get_training_data()
    model, X_test, y_test = training_round(df)

    #training model predictions
    svm_prediction = model.predict(X_test)

    #training model evaluation
    svm_report = classification_report(y_test, svm_prediction, output_dict=True)
    print("\nSVM Performance:")
    print(svm_report)

    #record report for performance tracking
    record_training_performance(svm_report)

    #saves the mistakes to the csv file used in the retraining loop
    results = pd.DataFrame({"email_id": X_test.index, "email": X_test.values,"actual": y_test.values, "predicted": svm_prediction})
    results["sender_email_domain"] = df.loc[results["email_id"],"sender_email_domain"].values
    mistakes = results[results["actual"] != results["predicted"]]
    mistakes = mistakes.drop(columns=["email"])
    mistakes.to_csv(PROJECT_ROOT/"data"/"training_results.csv", index=False)

    # Transformer evaluation
    evaluate_transformer(X_test,y_test,50)


    commit_learning(model)
    #perform_corrective_training()

    return

def perform_corrective_training() -> None:
    """Review classifications by the model and provide human correction."""

    corrections = pd.read_csv(
        f"{PROJECT_ROOT}/data/training_results.csv",
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

        for number, label in enumerate(labels, start=0):
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

        # Commit human correction
        update_trainingdata(email_id, selected_label)

    return

#=================
#logic
#=================

#perform_training_loop()
