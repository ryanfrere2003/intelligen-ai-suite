""" contains functions that run on the mailbox csv to count events"""

import re
import pandas as pd

#====================
#detection lists
#====================
ADVERTISING_KEYWORDS = [
    "buy now",
    "limited time",
    "offer",
    "sale",
    "discount",
    "exclusive",
    "promotion",
    "shop now",
]

MARKETING_KEYWORDS = [
    "campaign",
    "brand",
    "launch",
    "discover",
    "learn more",
    "introducing",
    "webinar",
    "customer success",
]

PRIVACY_KEYWORDS = [
    "privacy policy",
    "gdpr",
    "data protection",
    "your data",
    "consent",
    "cookies",
    "personal information",
    "privacy notice",
]

NEWSLETTER_KEYWORDS = [
    "newsletter",
    "this month",
    "latest news",
    "weekly update",
    "monthly update",
    "edition",
    "highlights",
    "unsubscribe",
]

#====================
#helpers
#====================

def detect_keywords(*email_sections:str,keyword_list:list) -> int:
    """ uses regex to detect advertising sequences in strings"""
    count = 0

    for section  in email_sections:
        section = section.lower()
        for keyword in keyword_list:
            count += len(re.findall(re.escape(keyword.lower()), section))
    
    return count

#====================
#functions
#====================

def label_email(email:pd.Series) -> dict:
    """ runs an email (pd.DataFrame Row) through a series of detection functions
        and then assigns the highest count"""

    sender = email["original_sender_string"]
    subject = email["subject"]
    body = email["body"]

    advertising_count:int = detect_keywords(sender,subject,body,keyword_list=ADVERTISING_KEYWORDS)
    marketing_count:int = detect_keywords(sender,subject,body,keyword_list=MARKETING_KEYWORDS)
    privacy_count:int = detect_keywords(sender,subject,body,keyword_list=PRIVACY_KEYWORDS)
    newsletter_count:int = detect_keywords(sender,subject,body,keyword_list=NEWSLETTER_KEYWORDS)

    counts: dict[str, int] = {
        "advertising_count": advertising_count,
        "marketing_count": marketing_count,
        "privacy_count": privacy_count,
        "newsletter_count": newsletter_count
    }

    max_value = max(counts.values())
    highest = []

    if max_value == 0:
        counts["label"] = "unlabelled" # type: ignore
    else:
        highest = [ key for key, value in counts.items() if value == max_value  ]

        if len(highest) > 1:
            counts["label"] = "ambiguous" # type: ignore
        else:
            counts["label"] = highest[0].split("_")[0] # type: ignore

    return counts
