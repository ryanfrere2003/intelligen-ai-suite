""" contains all functions and processes relating to distilbert model training, providing
a secondary method to classify text using a token transformer NLP."""

from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, #TODO: accuracy_score
from datasets import Dataset
import pandas as pd

from config import DISTILBERT_MODEL
from .data_labeller import LABEL_KEYWORDS
from .data import get_training_data

#model name and store
MODEL_NAME = "distilbert-base-uncased"
MODEL_STORE = DISTILBERT_MODEL

#label conversions
LABELS = list(LABEL_KEYWORDS.keys())
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}
ID_TO_LABEL = {i: label for label, i in LABEL_TO_ID.items()}


tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(LABELS),
    id2label=ID_TO_LABEL,
    label2id=LABEL_TO_ID,
)

#============
# functions
#============

def create_dataset(df:pd.DataFrame) -> Dataset:
    """Convert the pd.Dataframe email data into a Hugging Face dataset."""

    dataset = Dataset.from_pandas(df[["email_text", "training_label"]])
    dataset = dataset.rename_column("training_label","label")
    dataset = dataset.map(lambda x: {"label": LABEL_TO_ID[x["label"]]}    )
    return dataset

def prepare_data(df):
    """Prepare email data for DistilBERT from the database"""

    df = df.copy()

    df["email_text"] = (
        df["original_sender_string"].fillna("")
        + " "
        + df["subject"].fillna("")
        + " "
        + df["body"].fillna("")
    )

    training_df, testing_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["training_label"]
    )

    return training_df, testing_df

def tokenize_dataset(dataset:Dataset) -> Dataset:
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

def train_distilbert(training_df:pd.DataFrame,testing_df:pd.DataFrame):
    """ takes training and testing dataframes and performs a training
    round on distilbert."""

    train_dataset = create_dataset(training_df)
    test_dataset = create_dataset(testing_df)

    train_dataset = tokenize_dataset(train_dataset)
    test_dataset = tokenize_dataset(test_dataset)

    training_args = TrainingArguments(
        output_dir=f"{DISTILBERT_MODEL}",
        num_train_epochs=2,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        logging_steps=50,
        save_strategy="epoch",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset
    )

    trainer.train()
    return trainer

def evaluate_distilbert(trainer, testing_df):
    """Evaluate the trained DistilBERT model on unseen emails."""

    test_dataset = create_dataset(testing_df)
    test_dataset = tokenize_dataset(test_dataset)

    predictions = trainer.predict(test_dataset)

    predicted_ids = predictions.predictions.argmax(axis=1)
    actual_ids = predictions.label_ids

    predicted_labels = [
        ID_TO_LABEL[i]
        for i in predicted_ids
    ]

    actual_labels = [
        ID_TO_LABEL[i]
        for i in actual_ids
    ]

    report = classification_report(
        actual_labels,
        predicted_labels,
        labels=LABELS
    )

    print("\nDistilBERT Performance:")
    print(report)

    return predicted_labels, actual_labels


#============
#logic
#============
email_data = get_training_data()
training_df, testing_df = prepare_data(email_data)

print(f"training data legnth: {len(training_df)}.")
print(f"testing data length: {len(testing_df)}.")

print("\nStarting DistilBERT training...")

trainer = train_distilbert(
    training_df,
    testing_df
)

evaluate_distilbert(
    trainer,
    testing_df
)

#save training
trainer.save_model(f"{MODEL_STORE}")
tokenizer.save_pretrained(f"{MODEL_STORE}")
print(f"DistilBERT model saved to: {MODEL_STORE}")

print("\nDistilBERT training complete.")

