import base64
from email import message_from_bytes
from email.utils import parseaddr

import pandas as pd

from ml.data_preprocess import mail_body_to_plain_text, clean_html, clean_unicode
from .gmail_client import connect_gmail

#===============
#gmail instance (app will not work without this)
#===============
gmail_mailbox = connect_gmail()

#============
#helper functions
#============
def get_gmail_email(gmail, message_id: str):
    """initiates a user gmail inbox for the application"""
    message = gmail.users().messages().get(userId="me",id=message_id,format="raw").execute() #must be raw do decoder works with this and .mbox
    raw_email = base64.urlsafe_b64decode(message["raw"])
    return message_from_bytes(raw_email)

#============
#functions
#============
def load_gmail_mail_ids(gmail,mail_box_size:int):
    """request the inbox data mail ids from OAuth2 API"""

    inbox = gmail.users().messages().list(userId="me",maxResults=mail_box_size).execute()

    #create a list from the gmail API call of only the message IDs
    email_ids:list[str] = [email["id"] for email in inbox.get("messages", [])]

    print(f"Number of Gmail IDs returned: {len(email_ids)}")

    return email_ids

def load_gmail_data(gmail, message_ids: list[str]) -> pd.DataFrame:
    """Loads Gmail API messages into the same DataFrame format
    produced by load_mailbox_data() found in preprocess.py to allow 
    email parsing pipeline to be used for both live and mbox data.
    """

    emails = []

    for i, message_id in enumerate(message_ids):

        if i % 100 == 0:
            print(f"Processed {i} emails")

        # Get the raw Gmail message
        message = gmail.users().messages().get(
            userId="me",
            id=message_id,
            format="raw"
        ).execute()

        # Gmail returns URL-safe base64
        raw_email = base64.urlsafe_b64decode(message["raw"])

        # Convert bytes object into email compatible object for pipeline
        email = message_from_bytes(raw_email)

        # converts email into preprocess compatible format
        email_data = {
            "gmail_id": str(message_id),
            "sender": str(email.get("from", "")),
            "subject": str(email.get("subject", "")),
            "date": str(email.get("date", "")),
            "body": mail_body_to_plain_text(email)
        }
        emails.append(email_data)

    df = pd.DataFrame(emails)
    df.to_csv("gmail_inbox_dataset.csv", index=False)
    return df

def clean_gmail_data(inbox_dataframe:pd.DataFrame) -> pd.DataFrame:
    """ takes a prepared dataframe of the users gmail inbox and
    applies data cleaning rules before the data is commited to
    the database."""

    #keep original object safe
    df = inbox_dataframe.copy()

    # display info
    df.info()
    df.head()

        #add in columns for db preparation
    df.rename(columns={"sender": "original_sender_string"},inplace=True)
    df["sender_name"] = ""
    df["sender_email_username"] = ""
    df["sender_email_domain"] = ""

    df["is_read"] = ""
    df["classification"] = "unclassified"
    df["confidence"] = ""
    df["processed"] = ""
    df["created_at"] = ""

    df = df[
        [
            "gmail_id",
            "sender_name",
            "sender_email_username",
            "sender_email_domain",
            "original_sender_string",
            "subject",
            "body",
            "date",
            "is_read",
            "classification",
            "confidence",
            "processed",
            "created_at"
        ]
    ]

    # Handle missing values
    missing = df.isna().sum()
    print(missing)
    text_columns = ["subject", "body"]

    for col in text_columns:
        df[col] = df[col].fillna("")

    # clean HTML
    for col in text_columns:
        df[col] = df[col].apply(clean_html)

    # removal steps including whitespace, unicode and \
    for col in text_columns:
        df[col] = df[col].apply(clean_unicode) #remove unicode alignment
        df["body"] = df["body"].str.replace(r"\s+", " ", regex=True) #remove escape chars
        #df["sender"] = parseaddr(df["sender"])
        df[col] = df[col].str.strip() #do this last incase artifacts from other 2 steps!

    for index, row in df.iterrows():
        sender:str = row["original_sender_string"]
        sender_name, sender_address = parseaddr(sender) # type: ignore
        sender_email_user, _, sender_domain = sender_address.partition("@")


        df.loc[index, "sender_name"] = sender_name
        df.loc[index, "sender_email_domain"] = sender_domain
        df.loc[index, "sender_email_username"] = sender_email_user

    df.to_csv("gmail_inbox_clean.csv", index=False)
    return df

#TODO
def commit_gmail_data() -> None:
    """ reads the saved gmail_inbox_clean.csv and uses the gmail_id to
    check if an email exists. modiying the database as appropriate to reflect
    any actions taken"""
    
#============
#logic
#============
emails = load_gmail_mail_ids(gmail_mailbox,500)
emails = load_gmail_data(gmail_mailbox, emails)
emails = clean_gmail_data(emails)
