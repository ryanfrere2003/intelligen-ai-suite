"""Provides functions for comparing the SVM and DistilBERT email
classification models.

Both models are evaluated using the same held-out test data. Their
predictions and confidence scores are recorded to allow their
classification performance and areas of disagreement to be analysed for
model suitability within this project.
"""

from .data import get_training_data

from .model_distilbert import distilbert
from .trainer_distilbert import prepare_data

from .trainer_svm import ml_model


#load and prepare data
data = get_training_data(None)
training_data, testing_data = prepare_data(data)

#load and prepare models
SVM_MODEL = ml_model(load=True)
DISTILBERT_MODEL = distilbert(load=True)

#Run both models on testing_data


#Compare them


#Save results
