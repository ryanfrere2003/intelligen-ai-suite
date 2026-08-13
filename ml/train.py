""" loads data from training tables and allows analysis by the AI agent"""

import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

import joblib

from database import database
from config import MODEL_PATH, PROJECT_ROOT
from labeller import LABEL_KEYWORDS

#=================
# Helpers
#=================
    
def update_trainingdata(email_id:int,corrected_label:str, original_label:str) -> None:
    """Update the human-corrected label for an email. requires
    a valid email_id and corrected level"""

    if corrected_label == original_label:
        return

    conn = database.get_connection()

    conn.execute(
        """
        UPDATE TrainingData
        SET human_label = ?
        SET human_verified = 
        WHERE id = ?
        """,
        (corrected_label, True, email_id)
    )

    conn.commit()
    conn.close()

    return


#=================
# Main Functions
#=================


def get_training_data(email_id:int| None=None) -> pd.DataFrame:
    """ takes training data from the database TraininData table and returns a dataframe
    of all emails in the table
        Requires:
            email_id(int): a known email integer.
            email_id(none): all emails in the table.
        Returns:
            A dataframe object containing the query result."""
        
    conn = database.get_connection()

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

    return data

def ml_model(load=False) -> Pipeline:
    """Create a new ML model or load the existing one."""

    #if no training data exists
    if not load:
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
    else:
        model = joblib.load(f"{MODEL_PATH}/email_classifier.pkl")

    return model

def training_round(data: pd.DataFrame) -> tuple:
    """takes a filtered dataframe and concatenates fields 
    for ML training"""

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
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(f"Training emails: {len(X_train)}")
    print(f"Testing emails: {len(X_test)}")

    print("\nTraining distribution:")
    print(y_train.value_counts())

    print("\nTesting distribution:")
    print(y_test.value_counts())


    model = ml_model()

    print("\nTraining model...")
    model.fit(
        X_train,
        y_train
    )

    return model, X_test, y_test

def commit_learning(model) -> None:
    """ saves learning in model DIR using pkl file"""
    joblib.dump(model, f"{MODEL_PATH}/email_classifier.pkl")
    return

#may need to be removed once UI is functional
def perform_training_loop() -> None:
    """ performs a full training loop"""
    df = get_training_data()
    model, X_test, y_test = training_round(df)
    predictions = model.predict(X_test)
    print(classification_report(y_test,predictions))
    print(confusion_matrix(y_test,predictions))

    results = pd.DataFrame({"email_id": X_test.index, "email": X_test.values,"actual": y_test.values, "predicted": predictions})
    results["sender_email_domain"] = df.loc[results["email_id"],"sender_email_domain"].values

    mistakes = results[results["actual"] != results["predicted"]]
    mistakes = mistakes.drop(columns=["email"])
    mistakes.to_csv(PROJECT_ROOT/"data"/"training_results.csv", index=False)

    decision = model.decision_function(X_test)
    print(decision)
    commit_learning(model)
    return 

#TODO: ADAM
def perform_corrective_training() -> None:
    """ review classifications by the model and provide human correction
    where required to increase its accuracy"""

    corrected_emails = []
    corrections = pd.read_csv(f"{PROJECT_ROOT}/data/training_results_focus.csv",index_col="email_id")

    labels = list(LABEL_KEYWORDS.keys())

    for email_id, item in corrections.iterrows():
        email = get_training_data(email_id)
        corrected_emails.append(email)

    #correction loop
    for email in corrected_emails:
        print(f"")
        print(f"email sender string = {email["original_sender_string"]} \n")
        print(f"email subject: {email["subject"]} \n")
        print(f"email body: {email["body"]} \n")
        print("\n")

        #create list based on valid labels

        #commit change 
        update_trainingdata(email_id=0,corrected_label="",original_label="")

    return


#=================
#logic
#=================

