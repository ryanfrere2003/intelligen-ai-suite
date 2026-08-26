"""Provides functions for comparing the SVM and DistilBERT email
classification models.

Both models are evaluated using the same held-out test data. Their
predictions and confidence scores are recorded to allow their
classification performance and areas of disagreement to be analysed for
model suitability within this project.
"""

from config import PROJECT_ROOT

from .data import get_training_data, prepare_data, prepare_data_for_training_split

from .model_evaluation import evaluate_model, compare_models, save_model_comparison, compare_predictions, get_human_review_cases, save_human_review_cases
from .hil_corrections import corrective_actions

from .svm_trainer import run_svm_training
from .distilbert_trainer import run_distilbert_training, predict_distilbert

from pandas import read_csv

#is this an initiation loop or a training loop
try:
    read_csv(f"{PROJECT_ROOT}/data/human_review_cases.csv")
    model_state_exists=True
except FileNotFoundError:
    print("This is the first time the models have been run. INITIALIZING SVM AND DISTILBERT.....")
    model_state_exists=False
    


#load and prepare data
data = get_training_data(None)
data = prepare_data(data)
training_data, testing_data = prepare_data_for_training_split(data)

#svm
svm_results = run_svm_training(training_data,testing_data,load_model=model_state_exists)
svm_evaluation = svm_results["evaluation"]

#distilbert
distilbert_trainer = run_distilbert_training(training_data,testing_data,load_model=model_state_exists)
distilbert_predictions = predict_distilbert(distilbert_trainer,testing_data)
distilbert_results = evaluate_model(distilbert_predictions["actual"],distilbert_predictions["predictions"],"DistilBERT")


#Compare them
comparison = compare_models(svm_evaluation,distilbert_results)

#report
print("\n Model Comparison Report")
print(comparison)

#Save results
save_model_comparison(comparison)

#Prepare human in loop improvement file
predictions = compare_predictions(svm_results,distilbert_results)
predictions = get_human_review_cases(predictions)
save_human_review_cases(predictions)

#perform human in loop improvements if requested.
while True:
    choice = input("would you like to perform human in loop corrections? (Y/N): ")
    if choice.upper() == "Y":
        corrective_actions()
        break

    if choice.upper() == "N":
        break

    print(f"I'm sorry: ({choice}) is not a valid response.\n")    

print("your full comparison and training loop has completed for both models successfully.")
