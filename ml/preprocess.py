"""processes incoming data for training"""

import mailbox
import re
import pandas as pd
from bs4 import BeautifulSoup
from email.utils import parseaddr

from config import MAILBOX_PATH, PROJECT_ROOT
from database.database import get_connection
from .labeller import label_email

mailboxdata = mailbox.mbox(MAILBOX_PATH)

emails = []

#-------------------------------
# HELPER FUNCTIONS
#-------------------------------
def mail_body_to_plain_text(email) -> str:
    """ checks if an email item has mutiple parts and eliminates
    any parts which are not plain text such as images
    """
    body = ""

    if email.is_multipart():

        for part in email.walk():

            if part.get_content_type() == "text/plain":

                payload = part.get_payload(decode=True)

                if payload:
                    body += payload.decode(errors="ignore")

    else:

        payload = email.get_payload(decode=True)

        if payload:
            body = payload.decode(errors="ignore")

    return body

def clean_html(text:str) -> str:
    """ uses bs4 to remove HTML from strings, does  not remove <email address>"""
    if not text:
        return ""

    # Protect email addresses in angle brackets with re.sub()
    text = re.sub(
        r"<([\w\.-]+@[\w\.-]+\.\w+)>",
        r"\1",
        text
    )

    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")

def clean_unicode(text:str) -> str:
    """ removes unicode strings from emails"""
    return re.sub(r"[\u200B-\u200F\uFEFF]", "", text)

#-------------------------------
#MAIN FUNCTIONS
#-------------------------------
def load_mailbox_data(data_source:mailbox.mbox) -> pd.DataFrame:
    """ loads in a mbox file and parses all emails as a dataframe,
    converting the file to csv and loading it as a dataframe in memory.
    Args:
        datasource: mailbox.mbox
    Returns:
        df: pd.DataFrame"""
    for i, item in enumerate(data_source):

        if i % 100 == 0:
            print(f"Processed {i} emails")

        email = {}
        email["sender"] = str(item.get("from", ""))
        email["subject"] = str(item.get("subject", ""))
        email["date"] = str(item.get("date", ""))
        email["body"] = mail_body_to_plain_text(item)
        emails.append(email)


    df = pd.DataFrame(emails)
    df.to_csv("gmail_dataset.csv", index=False)
    print(df.head())
    return df

def clean_mailbox_data(mailbox_data_object:pd.DataFrame) -> pd.DataFrame:
    """ takes a pandas dataframe and performs cleaning activities
    on each field removing white space and preparing
    """
    #keep original object safe
    df = mailbox_data_object.copy()

    # display info
    df.info()
    df.head()

     #add in columns for db preparation
    df.rename(columns={"sender": "original_sender_string"},inplace=True)
    df["sender_name"] = ""
    df["sender_email_username"] = ""
    df["sender_email_domain"] = ""
    df["advertising_count"] = 0
    df["marketing_count"] = 0
    df["privacy_count"] = 0
    df["newsletter_count"] = 0
    df["notification_count"] = 0
    df["label"] = "unlabelled"

    df = df[
        [
            "sender_name",
            "sender_email_username",
            "sender_email_domain",
            "original_sender_string",
            "subject",
            "body",
            "date",
            "advertising_count",
            "marketing_count",
            "privacy_count",
            "newsletter_count",
            "notification_count",
            "label"
        ]
    ]

    # remove duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["subject", "body"], keep="first")
    after = len(df)
    print(f"removed ({before - after}) duplicated records from dataframe")

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

    for index, row in df.iterrows():
        outcome:dict = label_email(row)
        df.loc[index,"advertising_count"] = outcome.get("advertising_count")
        df.loc[index,"marketing_count"] = outcome.get("marketing_count")
        df.loc[index,"privacy_count"] = outcome.get("privacy_count")
        df.loc[index,"newsletter_count"] = outcome.get("newsletter_count")
        df.loc[index,"notification_count"] = outcome.get("notification_count")
        df.loc[index,"label"] = outcome.get("label")

      
    df.to_csv("gmail_dataset_clean.csv", index=False)
    return df


def commit_data_to_db(dataframe:pd.DataFrame) -> None:
    """ commits clean mailbox data to the TrainingData table"""
    data = dataframe    
    conn = get_connection()
    data.to_sql("TrainingData", conn , if_exists="append", index=False)
    return

#=========
#logic
#=========

df_raw = load_mailbox_data(mailboxdata)
def_clean = clean_mailbox_data(df_raw)
commit_data_to_db(def_clean)
