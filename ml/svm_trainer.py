"""Provides functions for training and evaluating the SVM email classifier."""

import pandas as pd
import joblib

from database.database import get_connection
from config import MODEL_PATH, PROJECT_ROOT
from .data_labeller import LABEL_KEYWORDS
from .data import get_training_data, prepare_data

from .model_evaluation import evaluate_model

from .svm_model import svm

# =================
# Helpers
# =================

def update_trainingdata(email_id: int, corrected_label: str) -> None:
    """Update the human-corrected label for an email."""
    conn = get_connection()
    conn.execute("""UPDATE TrainingData SET human_label = ?, human_verified = ? WHERE id = ?""",(corrected_label, True, email_id))
    conn.commit()
    conn.close()
    return

def save_svm_model(model) -> None:
    """Save the trained SVM model to the model data directory."""
    joblib.dump(model,f"{MODEL_PATH}/email_classifier.pkl")
    return

# =================
# Training
# =================

def train_svm(training_data: pd.DataFrame, testing_data: pd.DataFrame,model_load: bool = False) -> dict:
    """Train the SVM model using the supplied training and testing data."""

    x_train = training_data["email_text"]
    y_train = training_data["training_label"]

    x_test = testing_data["email_text"]
    y_test = testing_data["training_label"]

    print(f"Training emails: {len(x_train)}")
    print(f"Testing emails: {len(x_test)}")

    model = svm(load=model_load)

    print("\nTraining SVM...")

    model.fit(x_train, y_train)

    predictions = model.predict(x_test)

    #return format of trainer identical to distilBERT for analysis
    return {
        "model": model,
        "x_test": x_test,
        "y_test": y_test,
        "predictions": predictions,
    }

def run_svm_training(training_data,testing_data,model_load: bool = False) -> dict:
    """Load training data, train the SVM and return its results."""

    results = train_svm(
        training_data,
        testing_data,
        model_load
    )

    #commit the training sequence to memory
    save_svm_model(results["model"])

    #evaluate the model, and add the information to the results dict.
    evaluation = evaluate_model(results["y_test"],results["predictions"],"SVM")
    results["evaluation"] = evaluation

    return results


# =====================
# human in loop actions
# =====================

def svm_corrective_actions() -> None:
    """Review and manually correct SVM classification errors."""

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
    print("ending corrective actions to SVM model.")
    return
