"""Provides shared evaluation functions for machine learning models."""

import pandas as pd
from sklearn.metrics import classification_report

from config import PROJECT_ROOT

#============
#helper
#============

def get_next_training_iteration() -> int:
    """Return the next training iteration number for the model comparison csv."""

    comparison_path = (PROJECT_ROOT/ "data" / "model_comparison_history.csv")

    if not comparison_path.exists():
        return 1

    history = pd.read_csv(comparison_path)

    if history.empty:
        return 1

    return int(history["training_iteration"].max()) + 1

#===========
#functions
#===========

def evaluate_model(actual: list[str],predictions: list[str], model_name: str) -> dict:
    """Evaluate model predictions using a standard classification report."""

    report = classification_report(
        actual,
        predictions,
        output_dict=True,
        zero_division=0
    )

    print(f"\n{model_name} Performance:")

    print(classification_report(actual,predictions,zero_division=0))

    return {
        "model": model_name,
        "actual": actual,
        "predictions": predictions,
        "report": report
    }

def compare_models(svm_results: dict,distilbert_results: dict) -> pd.DataFrame:
    """Compare the performance of the SVM and DistilBERT models."""

    comparison = pd.DataFrame({
        "SVM": {
            "accuracy": svm_results["report"]["accuracy"],
            "macro_precision": svm_results["report"]["macro avg"]["precision"],
            "macro_recall": svm_results["report"]["macro avg"]["recall"],
            "macro_f1": svm_results["report"]["macro avg"]["f1-score"],
        },
        "DistilBERT": {
            "accuracy": distilbert_results["report"]["accuracy"],
            "macro_precision": distilbert_results["report"]["macro avg"]["precision"],
            "macro_recall": distilbert_results["report"]["macro avg"]["recall"],
            "macro_f1": distilbert_results["report"]["macro avg"]["f1-score"],
        }
    })

    return comparison

def save_model_comparison(comparison: pd.DataFrame) -> None:
    """Save model comparison results for a training iteration."""

    comparison_path = (PROJECT_ROOT/ "data" / "model_comparison_history.csv")

    comparison = comparison.copy()
    comparison["training_iteration"] = get_next_training_iteration()

    if comparison_path.exists():
        existing = pd.read_csv(comparison_path)

        comparison = pd.concat(
            [existing, comparison],
            ignore_index=True
        )

    comparison.to_csv(
        comparison_path,
        index=False
    )

    print(f"Model comparison saved to: {comparison_path}")

def compare_predictions(svm_results: dict,distilbert_results: dict) -> pd.DataFrame:
    """Compare SVM and DistilBERT predictions against the labelled data.
    returns problematic emails for human review."""

    comparison = pd.DataFrame({
        "email_id": svm_results["x_test"].index,
        "actual": svm_results["y_test"].values, #taken from labeller db entry in TrainingData table
        "svm_prediction": svm_results["predictions"],
        "distilbert_prediction": distilbert_results["predictions"]
    })

    comparison["svm_correct"] = (
        comparison["svm_prediction"] == comparison["actual"]
    )

    comparison["distilbert_correct"] = (
        comparison["distilbert_prediction"] == comparison["actual"]
    )

    comparison["models_agree"] = (
        comparison["svm_prediction"]
        == comparison["distilbert_prediction"]
    )

    return comparison

def get_human_review_cases(comparison: pd.DataFrame) -> pd.DataFrame:
    """Return emails requiring human review."""

    # return the all cases where SVM is not correct OR DistilBERT is not correct OR where the model disagree.
    review_cases = comparison[
        (~comparison["svm_correct"])
        | (~comparison["distilbert_correct"])
        | (~comparison["models_agree"])
    ]

    return review_cases

def save_human_review_cases(comparison: pd.DataFrame) -> None:
    """ saves the review cases dataframe to CSV in the data directory
    for review by a human."""
    HIL_FILE_PATH = PROJECT_ROOT / "data" / "human_review_cases.csv"
    comparison.to_csv(HIL_FILE_PATH, index=True)
    print("human reviw file successfully created.")
    return
