import base64
from email import message_from_bytes

from .gmail_client import connect_gmail


#===============
#gmail instance (app will not work without this)
#===============
gmail_mailbox = connect_gmail()

#============
#helper
#============
#TODO
def get_gmail_email(gmail, message_id: str):
    """initiates a user gmail inbox for the application"""
    message = gmail.users().messages().get(userId="me",id=message_id,format="raw").execute() #must be raw do decoder works with this and .mbox
    raw_email = base64.urlsafe_b64decode(message["raw"])
    print(raw_email)
    return message_from_bytes(raw_email)

#============
#functions
#============
def initiate_user(gmail,mail_box_size:int):
    """ authorise and acquire gmail email tokens for the user before
        attempting to parse"""

    inbox = gmail.users().messages().list(userId="me",maxResults=mail_box_size).execute()
    print(inbox)


    #create a list from the gmail API call of only the message IDs
    email_ids = [email["id"] for email in inbox.get("messages", [])]

    #parse each email 
    for email_id in email_ids:
        get_gmail_email(gmail,email_id)


    #commit all emails to database
    #TODO

    #perform ML labelling
    #TODO

#============
#logic
#============
initiate_user(gmail_mailbox,1)
