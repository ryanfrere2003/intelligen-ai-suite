import sqlite3

DATABASE_SCHEMA = {

    "Emails": """
    CREATE TABLE IF NOT EXISTS Emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        message_id TEXT UNIQUE,

        subject TEXT NOT NULL,

        sender_name TEXT,

        sender_email TEXT NOT NULL,

        sender_domain TEXT,

        received_date DATETIME,

        body TEXT NOT NULL,

        is_read INTEGER DEFAULT 0,

        classification TEXT,

        confidence REAL,

        processed INTEGER DEFAULT 0,

        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,

    "Companies": """
    CREATE TABLE IF NOT EXISTS Companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        domain TEXT UNIQUE NOT NULL,

        company_name TEXT NOT NULL,

        industry TEXT,

        country TEXT,
        
        contact_email TEXT,

        privacy_email TEXT,
        
        privacy_url TEXT,
        
        website TEXT,

        privacy_score REAL,

        cluster INTEGER,

        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,

    "SearchResults": """
    CREATE TABLE IF NOT EXISTS SearchResults (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        search_engine TEXT NOT NULL,

        search_query TEXT NOT NULL,

        url TEXT NOT NULL UNIQUE,

        domain TEXT,

        page_title TEXT,

        snippet TEXT,

        result_rank INTEGER,

        discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        crawl_status TEXT DEFAULT 'pending',

        last_crawled DATETIME,

        crawl_attempts INTEGER DEFAULT 0
    );
    """,

    "PIIEntities": """
    CREATE TABLE IF NOT EXISTS PIIEntities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        page_id INTEGER NOT NULL,
    
        entity_type TEXT NOT NULL,
    
        entity_value TEXT NOT NULL,
    
        confidence REAL,
    
        analysed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
        FOREIGN KEY (page_id)
            REFERENCES CrawledPages(id)
            ON DELETE CASCADE
    );
    """,

    "CrawledPages": """
    CREATE TABLE IF NOT EXISTS CrawledPages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        search_result_id INTEGER NOT NULL UNIQUE,
    
        http_status INTEGER,
    
        content_type TEXT,
    
        page_title TEXT,
    
        description TEXT,
    
        keywords TEXT,
    
        html TEXT,
    
        extracted_text TEXT,
    
        content_hash TEXT,
    
        verification_status TEXT DEFAULT 'pending',
        
        risk_score REAL DEFAULT 0,
        
        match_score REAL DEFAULT 0,
    
        crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        company_id INTEGER,

        FOREIGN KEY (company_id)
            REFERENCES Companies(id)
    
        FOREIGN KEY (search_result_id)
            REFERENCES SearchResults(id)
    );
    """,

    "PageEmails": """
    CREATE TABLE IF NOT EXISTS PageEmails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        page_id INTEGER NOT NULL,
    
        email TEXT NOT NULL,
    
        FOREIGN KEY (page_id)
            REFERENCES CrawledPages(id)
            ON DELETE CASCADE
    );
    """,

    "PageImages": """
    CREATE TABLE IF NOT EXISTS PageImages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        page_id INTEGER NOT NULL,
    
        image_url TEXT NOT NULL,
    
        FOREIGN KEY (page_id)
            REFERENCES CrawledPages(id)
            ON DELETE CASCADE
    );
    """,

    "PageLinks": """
    CREATE TABLE IF NOT EXISTS PageLinks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        page_id INTEGER NOT NULL,
    
        url TEXT NOT NULL,
    
        link_type TEXT NOT NULL,
    
        FOREIGN KEY (page_id)
            REFERENCES CrawledPages(id)
            ON DELETE CASCADE
    );
    """,

    "GDPRRequests": """
    CREATE TABLE GDPRRequests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        company_id INTEGER,
    
        email_id INTEGER,
    
        page_id INTEGER,
    
        generated_request TEXT NOT NULL,
    
        tone TEXT,
    
        recipient_email TEXT,
    
        status TEXT DEFAULT 'Draft',
    
        sent_date DATETIME,
    
        response_date DATETIME,
    
        notes TEXT,
    
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
        FOREIGN KEY (company_id)
            REFERENCES Companies(id),
    
        FOREIGN KEY (email_id)
            REFERENCES Emails(id),
    
        FOREIGN KEY (page_id)
            REFERENCES CrawledPages(id)
    );
    """,

    "TrainingData" : """
    CREATE TABLE IF NOT EXISTS TrainingData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        sender_name TEXT NOT NULL,

        sender_email_username TEXT NOT NULL,

        sender_email_domain TEXT NOT NULL,

        original_sender_string TEXT NOT NULL,

        subject TEXT NOT NULL,
        
        body TEXT NOT NULL,

        date TEXT NOT NULL,

        advertising_count INTEGER DEFAULT 0,

        marketing_count INTEGER DEFAULT 0,

        privacy_count INTEGER DEFAULT 0,

        newsletter_count INTEGER DEFAULT 0,

        label TEXT DEFAULT 'unlabelled'
    );
    """
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
    Returns True if the specified table exists.
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    )

    return cursor.fetchone() is not None


def verify_schema(connection: sqlite3.Connection) -> bool:
    """
    Checks that all required tables exist.
    Returns True if the schema is valid.
    """
    return all(
        table_exists(connection, table_name)
        for table_name in DATABASE_SCHEMA.keys()
    )