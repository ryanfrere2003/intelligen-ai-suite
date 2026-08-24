"""Provides shared evaluation functions for machine learning models."""

import pandas as pd
from sklearn.metrics import classification_report

from config import PROJECT_ROOT

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
    """Save model comparison results to a CSV file."""

    comparison_path = PROJECT_ROOT / "data" / "model_comparison.csv"

    comparison.to_csv(
        comparison_path,
        index=True
    )

    print(f"Model comparison saved to: {comparison_path}")