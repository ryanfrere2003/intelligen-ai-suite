""" loads data from training tables and allows analysis by the AI agent"""

import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


from database import database 
from config import PROJECT_ROOT


def get_training_data(email_id:int| None=None) -> pd.DataFrame:
    """ takes training data from the database and returns a dataframe"""
    conn = database.get_connection()

    if email_id is None:
        data = pd.read_sql("SELECT * FROM TrainingData", conn)
    else:
        data = pd.read_sql("SELECT * FROM TrainingData WHERE id=?",conn ,params=(email_id,))
    data.set_index("id",inplace=True)

    #remove unlabelled and ambiguous
    print(f"data is currently contains: ({len(data)}) emails.")
    data = data[~data["label"].isin(["unlabelled","ambiguous"])]
    print(f"after filtering to suitable data contains: ({len(data)}) emails.")

    #state health of the sample
    print(data["label"].value_counts())

    return data


def ml_model():
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


def training_round(data: pd.DataFrame):
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

#=================
#logic
#=================

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