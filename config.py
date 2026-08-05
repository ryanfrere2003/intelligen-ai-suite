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


#--------------
# PATHS
#--------------
#TODO: you will need to provide your own mbox file
PROJECT_ROOT = Path(__file__).resolve().parent

DATABASE_PATH = PROJECT_ROOT / "database" / "main.db"
MAILBOX_PATH = PROJECT_ROOT / "data" / "raw" / "raw.mbox"
