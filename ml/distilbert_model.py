""" contains the function to initiate the distilBERT LLM"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers.trainer_utils import get_last_checkpoint

from config import DISTILBERT_MODEL
from .data_labeller import LABEL_KEYWORDS

def distilbert(load:bool) -> tuple:
    """ loads and returns a distilbert model with it's associated tokenizer"""

    #model name and store
    newest_checkpoint = get_last_checkpoint(DISTILBERT_MODEL)

    if load and newest_checkpoint is not None:
        try:
            model = AutoModelForSequenceClassification.from_pretrained(newest_checkpoint)
            tokenizer = AutoTokenizer.from_pretrained(newest_checkpoint)
            print("loaded an existing distilBERT model.")
            return model, tokenizer
        except OSError as e:
            print(f"an error occured could not load tokenizer or model files: {e}")

    #if model doesnt exist or it cant be loaded, initiate a new model and tokenizer
    print("initiating tokenizer and model for distilBERT....\n")
       
    #label conversions
    labels = list(LABEL_KEYWORDS.keys())
    label_to_id = {label: i for i, label in enumerate(labels)}
    id_to_label = {i: label for label, i in label_to_id.items()}

    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    model = AutoModelForSequenceClassification.from_pretrained(
        pretrained_model_name_or_path="distilbert-base-uncased",
        num_labels=len(labels),
        id2label=id_to_label,
        label2id=label_to_id,
    )

    return model, tokenizer
