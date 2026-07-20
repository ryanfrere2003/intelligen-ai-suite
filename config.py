import os
from dotenv import load_dotenv

load_dotenv()

USER_FULL_NAME = os.getenv("USER_FULL_NAME")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_USERNAME = os.getenv("USER_USERNAME")
USER_CITY = os.getenv("USER_CITY")