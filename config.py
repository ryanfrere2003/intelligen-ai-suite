""" has configuration data for the application including commonly used paths"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

USER_FULL_NAME = os.getenv("USER_FULL_NAME")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_USERNAME = os.getenv("USER_USERNAME")
USER_CITY = os.getenv("USER_CITY")


#--------------
# PATHS
#--------------

APP_PATH = Path(__file__).resolve().parent
MAILBOX_PATH = APP_PATH / "raw.mbox"
