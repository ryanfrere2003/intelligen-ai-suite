"""Provides functions for training and evaluating the SVM email classifier."""

import pandas as pd
import joblib


from config import SVM_MODEL

from .model_evaluation import evaluate_model

from .svm_model import svm

# =================
# Helpers
# =================

def save_svm_model(model) -> None:
    """Save the trained SVM model to the model data directory."""
    joblib.dump(model,f"{SVM_MODEL}/email_classifier.pkl")
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

def run_svm_training(training_data,testing_data,load_model:bool = False) -> dict:
    """Load training data, train the SVM and return its results."""

    results = train_svm(
        training_data,
        testing_data,
        load_model
    )

    #commit the training sequence to memory
    save_svm_model(results["model"])

    #evaluate the model, and add the information to the results dict.
    evaluation = evaluate_model(results["y_test"],results["predictions"],"SVM")
    results["evaluation"] = evaluation

    return results
