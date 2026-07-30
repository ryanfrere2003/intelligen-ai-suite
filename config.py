""" has configuration data for the application including commonly used paths"""

import os, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

USER_FULL_NAME = os.getenv("USER_FULL_NAME")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_USERNAME = os.getenv("USER_USERNAME")
USER_LOCATIONS = json.loads(
    os.getenv("USER_LOCATIONS", "[]")
)


#--------------
# PATHS
#--------------
#TODO: you will need to provide your own mbox file
MAILBOX_PATH = "data/raw/raw.mbox"
