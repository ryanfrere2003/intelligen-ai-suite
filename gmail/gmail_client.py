import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_READ_ONLY, AUTH_PATH

def connect_gmail():
    """ contacts the google OAuth2 API and requests a
    user to sign in to acquire access to their gmail inbox
    NOTE: Application will not work with other email services."""
    credentials = None

    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file(
            f"{AUTH_PATH}/token.json",
            GMAIL_READ_ONLY
        )

    if not credentials or not credentials.valid:

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                f"{AUTH_PATH}/credentials.json",
                GMAIL_READ_ONLY
            )

            credentials = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(credentials.to_json())

    gmail = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    return gmail