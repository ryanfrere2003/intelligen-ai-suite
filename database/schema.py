import sqlite3

DATABASE_SCHEMA = {

    "Emails": """
              CREATE TABLE IF NOT EXISTS Emails
              (

                  id
                  INTEGER
                  PRIMARY
                  KEY
                  AUTOINCREMENT,

                  message_id
                  TEXT
                  UNIQUE,

                  subject
                  TEXT
                  NOT
                  NULL,

                  sender_name
                  TEXT,

                  sender_email
                  TEXT
                  NOT
                  NULL,

                  sender_domain
                  TEXT,

                  received_date
                  DATETIME,

                  folder
                  TEXT,

                  body
                  TEXT
                  NOT
                  NULL,

                  is_read
                  INTEGER
                  DEFAULT
                  0,

                  classification
                  TEXT,

                  confidence
                  REAL,

                  processed
                  INTEGER
                  DEFAULT
                  0,

                  created_at
                  DATETIME
                  DEFAULT
                  CURRENT_TIMESTAMP
              );
              """,

    "Companies": """
                 CREATE TABLE IF NOT EXISTS Companies
                 (

                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,

                     domain
                     TEXT
                     UNIQUE
                     NOT
                     NULL,

                     company_name
                     TEXT
                     NOT
                     NULL,

                     industry
                     TEXT,

                     country
                     TEXT,

                     privacy_score
                     REAL,

                     cluster
                     INTEGER,

                     created_at
                     DATETIME
                     DEFAULT
                     CURRENT_TIMESTAMP
                 );
                 """,

    "CrawlResults": """
                    CREATE TABLE IF NOT EXISTS CrawlResults
                    (

                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,

                        company_id
                        INTEGER
                        NOT
                        NULL,

                        url
                        TEXT
                        NOT
                        NULL,

                        page_title
                        TEXT,

                        contains_name
                        INTEGER
                        DEFAULT
                        0,

                        contains_email
                        INTEGER
                        DEFAULT
                        0,

                        contains_phone
                        INTEGER
                        DEFAULT
                        0,

                        contains_address
                        INTEGER
                        DEFAULT
                        0,

                        confidence
                        REAL,

                        last_scanned
                        DATETIME,

                        FOREIGN
                        KEY
                    (
                        company_id
                    )
                        REFERENCES Companies
                    (
                        id
                    )
                        );
                    """,

    "GDPRRequests": """
                    CREATE TABLE IF NOT EXISTS GDPRRequests
                    (

                        id
                        INTEGER
                        PRIMARY
                        KEY
                        AUTOINCREMENT,

                        company_id
                        INTEGER
                        NOT
                        NULL,

                        email_id
                        INTEGER,

                        generated_request
                        TEXT
                        NOT
                        NULL,

                        tone
                        TEXT
                        NOT
                        NULL,

                        recipient_email
                        TEXT,

                        status
                        TEXT
                        DEFAULT
                        'Draft',

                        sent_date
                        DATETIME,

                        response_date
                        DATETIME,

                        notes
                        TEXT,

                        created_at
                        DATETIME
                        DEFAULT
                        CURRENT_TIMESTAMP,

                        FOREIGN
                        KEY
                    (
                        company_id
                    )
                        REFERENCES Companies
                    (
                        id
                    ),
                        FOREIGN KEY
                    (
                        email_id
                    )
                        REFERENCES Emails
                    (
                        id
                    )
                        );
                    """,
}


def create_schema(connection: sqlite3.Connection) -> None:
    """
    Creates all database tables if they do not already exist.
    """

    cursor = connection.cursor()

    for table_sql in DATABASE_SCHEMA.values():
        cursor.execute(table_sql)

    connection.commit()


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    """
    Returns True if the table exists.
    """

    cursor = connection.cursor()

    cursor.execute("""
                   SELECT name
                   FROM sqlite_master
                   WHERE type = 'table'
                     AND name = ?
                   """, (table_name,))

    return cursor.fetchone() is not None


def verify_schema(connection: sqlite3.Connection) -> bool:
    """
    Checks that all required tables exist.
    Returns True if valid.
    """

    for table in DATABASE_SCHEMA.keys():
        if not table_exists(connection, table):
            return False

    return True