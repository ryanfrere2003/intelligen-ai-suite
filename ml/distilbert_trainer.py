"""Provides functions for training and evaluating a DistilBERT
transformer model for email classification. The model is fine-tuned using
labelled email data and evaluated against a held-out test set.
"""

#NOTE: investigated zero-shot classification but found its performance unsuitable fine-tuned DistilBERT for the specific classification task.

from transformers import TrainingArguments, Trainer, AutoTokenizer
from datasets import Dataset, Value
import pandas as pd

from config import DISTILBERT_MODEL
from .data_labeller import LABEL_KEYWORDS

from .distilbert_model import distilbert

MODEL_STORE = DISTILBERT_MODEL

#label conversions
LABELS = list(LABEL_KEYWORDS.keys())
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}
ID_TO_LABEL = {i: label for label, i in LABEL_TO_ID.items()}

#===========
# helper
#===========
def tokenize_dataset(dataset:Dataset, tokenizer) -> Dataset:
    """Tokenise email Dataset text for DistilBERT."""

    return dataset.map(
        lambda x: tokenizer(
            x["email_text"],
            truncation=True,
            padding="max_length",
            max_length=256
        ),
        batched=True
    )

def create_dataset(df:pd.DataFrame) -> Dataset:
    """Convert the pd.Dataframe email data into a Hugging Face dataset."""

    dataset = Dataset.from_pandas(df[["email_text", "training_label"]])
    dataset = dataset.rename_column("training_label","label")
    dataset = dataset.map(lambda x: {"label": LABEL_TO_ID[x["label"]]})
    dataset = dataset.cast_column("label", Value("int64")) #force to int values as sometimes bugs and states str value for column crashing distilbert.

    return dataset

#============
# functions
#============
def run_distilbert_training(training_df:pd.DataFrame,testing_df:pd.DataFrame,load_model:bool=False) -> Trainer:
    """ takes training and testing dataframes and performs a training
    round on distilbert."""

    
    #model loading
    distilBERT,tokenizer = distilbert(load=load_model)
    
    train_dataset = create_dataset(training_df)
    test_dataset = create_dataset(testing_df)

    train_dataset = tokenize_dataset(train_dataset,tokenizer)
    test_dataset = tokenize_dataset(test_dataset,tokenizer)

    training_args = TrainingArguments(
        output_dir=f"{DISTILBERT_MODEL}",
        save_total_limit=2, #helps if there is a corruption, do not set to 1.
        num_train_epochs=2,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        logging_steps=50,
        save_strategy="epoch",
        report_to="none",
        
    )

    trainer_class = Trainer(
        model=distilBERT,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset
    )

    trainer_class.train()

    #save training
    trainer_class.save_model(MODEL_STORE)
    tokenizer.save_pretrained(MODEL_STORE)


    return trainer_class

def predict_distilbert(trainer_class,testing_df: pd.DataFrame) -> dict:
    """Generate predictions from DistilBERT using the supplied test data."""

    tokenizer = AutoTokenizer.from_pretrained(MODEL_STORE)

    test_dataset = create_dataset(testing_df)
    test_dataset = tokenize_dataset(test_dataset,tokenizer)

    predictions = trainer_class.predict(test_dataset)

    predicted_ids = predictions.predictions.argmax(axis=1)
    actual_ids = predictions.label_ids

    predicted_labels = [ID_TO_LABEL[i] for i in predicted_ids]
    actual_labels = [ID_TO_LABEL[i] for i in actual_ids]

    return {
        "predictions": predicted_labels,
        "actual": actual_labels
    }
