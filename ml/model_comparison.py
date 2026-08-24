"""Provides functions for comparing the SVM and DistilBERT email
classification models.

Both models are evaluated using the same held-out test data. Their
predictions and confidence scores are recorded to allow their
classification performance and areas of disagreement to be analysed for
model suitability within this project.
"""

from .data import get_training_data, prepare_data

from .model_evaluation import evaluate_model, compare_models, save_model_comparison

from .svm_trainer import run_svm_training
from .distilbert_trainer import run_distilbert_training, predict_distilbert

#load and prepare data
data = get_training_data(None)
training_data, testing_data = prepare_data(data)

#svm
svm_results = run_svm_training(training_data,testing_data)
svm_results = svm_results["evaluation"]

#distilbert
distilbert_trainer = run_distilbert_training(training_data,testing_data)
distilbert_predictions = predict_distilbert(distilbert_trainer,testing_data)
distilbert_results = evaluate_model(distilbert_predictions["actual"],distilbert_predictions["predictions"],"DistilBERT")


#Compare them
comparison = compare_models(svm_results,distilbert_results)

#report
print("\n Model Comparison Report")
print(comparison)

#Save results
save_model_comparison(comparison)
