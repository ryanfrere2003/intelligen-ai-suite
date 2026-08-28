""" contains functions that run on the mailbox csv to count events"""

import re
import pandas as pd

#====================
#detection lists
#====================
LABEL_KEYWORDS = {
    "advertising": {
        "strong": [
            "buy now",
            "shop now",
            "discount code",
            "promo code",
            "coupon",
            "voucher code",
            "limited time offer",
            "free shipping",
            "free delivery",
            "save %",
            "clearance",
            "flash sale",
            "exclusive offer",
            "exclusive deal",
            "offer ends",
            "last chance",
            "order now",
            "claim your"
            ],

        "weak": [
        "sale",
        "discount",
        "deal",
        "special price",
        "reduced price",
        "save money",
        "lowest price",
        "bundle offer",
        "gift card",
        "free trial"
        ]
    },
    "marketing": {
        "strong": [
            "introducing",
            "announcing",
            "launching",
            "new product",
            "new service",
            "new feature",
            "new features",
            "product update",
            "platform update",
            "upgrade",
            "upgrade now",
            "try our",
            "start your free",
            "free trial",
            "get started",
            "customer success",
            "customer story",
            "case study",
            "success story",
            "webinar",
            "whitepaper",
            "ebook",
            "request a demo",
            "book a demo",
            "schedule a demo",
            "see what's new"
        ],

        "weak": [
            "coming soon",
            "now available",
            "available now",
            "learn more",
            "discover",
            "explore",
            "announcement",
            "release",
            "campaign",
            "collection",
            "experience",
            "marketing preferences"
        ]
    },
    "privacy" : {
        "strong": [
            "gdpr",
            "general data protection regulation",
            "data protection",
            "updated our privacy policy",
            "our privacy policy",
            "terms of service and privacy policy",
            "terms of use and privacy policy",
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
    "newsletter": {
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
            "top stories",
            "latest stories",
            "more new posts",
            "switch to weekly",
            "switch to daily",
            "get the latest"
        ],

        "weak": [
            "digest",
            "monthly update",
            "weekly update",
            "daily update",
            "daily email",
            "latest news",
            "highlights",
            "what's new",
            "this month",
            "this week's",
            "from our blog",
            "community update",
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
            "is now live",
            "is live now",
            "is live streaming",
            "is livestreaming"
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
            "new posts"
        ]
    }
}

#====================
#helpers
#====================

def detect_keywords(*email_sections: str, keyword_dict: dict) -> int:
    """Counts keyword matches using weighted strong/weak keywords"""

    count = 0
    strong_match = False

    for section in email_sections:
        section = section.lower()

        #strong words are worth 2 points
        for keyword in keyword_dict["strong"]:
            matches = len(re.findall(re.escape(keyword.lower()),section))
            if matches > 0:
                strong_match = True
            count += matches * 2

        #weak words are worth one point
        for keyword in keyword_dict["weak"]:
            count += len(re.findall(re.escape(keyword.lower()),section))

    #if a score is low set it to 0, this improves the quality of training data
    if count <= 1 and not strong_match:
        count = 0

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
