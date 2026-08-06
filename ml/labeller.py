""" contains functions that run on the mailbox csv to count events"""

import re
import pandas as pd

#====================
#detection lists
#====================
LABEL_KEYWORDS = {
    "advertising" : {
    "strong": [
        "buy now",
        "shop now",
        "discount code",
        "promo code",
        "coupon",
        "limited time offer",
        "free shipping",
        "save %",
        "clearance",
        "flash sale",
        "exclusive offer",
    ],

    "weak": [
        "sale",
        "discount",
        "offer",
        "promotion",
        "deal",
        "grab",
        "tickets",
        "special price",
    ]
},
    "marketing" : {
    "strong": [
        "introducing",
        "new product",
        "new features",
        "latest release",
        "customer success",
        "customer story",
        "case study",
        "success story",
        "webinar",
        "whitepaper",
        "ebook",
        "our mission",
        "our story",
    ],

    "weak": [
        "latest updates",
        "coming soon",
        "now available",
        "available now",
        "explore our",
        "discover our",
        "learn more",
        "find out more",
        "community",
        "event",
        "workshop",
        "guide",
        "blog",
        "campaign",
        "collection",
        "experience",
        "get inspired",
    ]
},
    "privacy" : {
    "strong": [
        "gdpr",
        "general data protection regulation",
        "data protection",
        "privacy policy",
        "privacy notice",
        "privacy statement",
        "subject access request",
        "right to erasure",
        "right to access",
        "updated privacy policy",
        "changes to our privacy",
        "changes to data practices",
    ],

    "weak": [
        "data processing",
        "processing your personal data",
        "processing of your data",
        "legal basis",
        "data subject",
        "delete my data",
        "request my data",
    ]
},
    "newsletter" : {
    "strong": [
        "newsletter",
        "monthly newsletter",
        "weekly newsletter",
        "news letter",
        "edition",
        "daily digest",
        "weekly digest",
        "monthly digest",
        "roundup",
    ],

    "weak": [
        "monthly update",
        "weekly update",
        "latest news",
        "highlights",
        "what's new",
        "this month",
        "this week's",
        "articles",
        "stories",
        "insights",
        "tips and tricks",
        "community update",
        "from our blog",
        "manage subscription",
        "email preferences",
    ]
},
    "notification" : {
    "strong": [
        "mentioned you",
        "tagged you",
        "commented on",
        "liked your",
        "reacted to",
        "new follower",
        "new friend request",
        "friend request",
        "verification code",
        "two-factor authentication",
        "2fa code",
        "one time code",
        "password reset",
        "new sign-in",
        "login attempt",
        "suspicious activity",
        "device signed in",
        "went live",
        "uploaded a new video",
        "new subscriber",
    ],

    "weak": [
        "security alert",
        "new device",
        "people you may know",
        "someone shared",
        "new video",
        "channel update",
        "premiere",
        "notification",
        "alert",
        "reminder",
    ]
}
}

#====================
#helpers
#====================

def detect_keywords(*email_sections: str, keyword_dict: dict) -> int:
    """Counts keyword matches using weighted strong/weak keywords"""

    count = 0

    for section in email_sections:
        section = section.lower()

        #strong words are worth 2 points
        for keyword in keyword_dict["strong"]:
            count += len(re.findall(re.escape(keyword.lower()),section)) * 2

        #weak words are worth one point
        for keyword in keyword_dict["weak"]:
            count += len(re.findall(re.escape(keyword.lower()),section))


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

    #new categories can be added above
    counts: dict[str, int] = {}
    max_value = 0

    for label, keywords in LABEL_KEYWORDS.items():
        counts[f"{label}_count"] = detect_keywords(sender,subject,body,keyword_dict=keywords)

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


#====================
#logic
#===================