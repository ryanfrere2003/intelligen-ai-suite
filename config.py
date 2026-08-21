""" has configuration data for the application including commonly used paths"""
from pathlib import Path
import os, json
from dotenv import load_dotenv

load_dotenv()

USER_FIRST_NAME = os.getenv("USER_FIRST_NAME")
USER_LAST_NAME = os.getenv("USER_LAST_NAME")
USER_MIDDLE_NAMES= json.loads(os.getenv("USER_MIDDLE_NAMES", "[]"))

USER_EMAIL = os.getenv("USER_EMAIL")
USER_USERNAME = json.loads(os.getenv("USER_USERNAMES", "[]"))
USER_LOCATIONS = json.loads(os.getenv("USER_LOCATIONS", "[]"))
USER_NUMBERS = json.loads(os.getenv("USER_NUMBERS", "[]"))

#--------------
#API Connections
#--------------
GMAIL_READ_ONLY = ["https://www.googleapis.com/auth/gmail.readonly"]

#--------------
# PATHS
#--------------
PROJECT_ROOT = Path(__file__).resolve().parent #for training you must provide your own mbox file.

DATABASE_PATH = PROJECT_ROOT / "database" / "main.db"
MAILBOX_PATH = PROJECT_ROOT / "data" / "raw" / "raw.mbox"
MODEL_PATH = PROJECT_ROOT / "data" / "models"
AUTH_PATH = PROJECT_ROOT / "data" / "oauth2"

CLASSIFIER_MODEL = MODEL_PATH / "svm"
DISTILBERT_MODEL = MODEL_PATH / "distilbert"
