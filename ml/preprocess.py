"""processes incoming data for training"""

import mailbox
import re
import pandas as pd
from bs4 import BeautifulSoup

#from ..config import MAILBOX_PATH

mailboxdata = mailbox.mbox("raw.mbox")

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
        email["sender"] = item["from"]
        email["subject"] = item["subject"]
        email["date"] = item["date"]
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

    # remove duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["subject", "sender", "body"], keep="first")
    after = len(df)
    print(f"removed ({before - after}) duplicated records from dataframe")

    # Handle missing values
    missing = df.isna().sum()
    print(missing)
    text_columns = ["subject", "sender", "body"]

    for col in text_columns:
        df[col] = df[col].fillna("")

    # clean HTML
    for col in text_columns:
        df[col] = df[col].apply(clean_html)

    # removal steps including whitespace, unicode and \
    for col in text_columns:
        df[col] = df[col].apply(clean_unicode) #remove unicode alignment
        df["body"] = df["body"].str.replace(r"\s+", " ", regex=True) #remove escape chars
        df["sender"] = df["sender"].str.replace('"', '', regex=False) #remove quotes from sender field
        df[col] = df[col].str.strip() #do this last incase artifacts from other 2 steps!


    df.to_csv("gmail_dataset_clean.csv", index=False)
    print(df.head())
    return df

def format_mailbox_data(mailbox_data_object:pd.DataFrame) -> pd.DataFrame:
    """ takes clean data and reformats for interpretation"""
    
    #add in columns for db preparation
    mailbox_data_object["sender_domain"] = ""
    mailbox_data_object["is_marketing"] = ""
    mailbox_data_object["is_privacy_update"] = ""
    mailbox_data_object["predicted_label"] = ""
    mailbox_data_object["confidence"] = ""

#TODO: ADAM STOPPED HERE 20th JULY

    #id

    #subject

    #sender


    #sender_domain

    #date_received

    #body

    #is_marketing

    #is_privacy_update

    #predicted_label

    #confidence

    return df



df_raw = load_mailbox_data(mailboxdata)
def_clean = clean_mailbox_data(df_raw)
