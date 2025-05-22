import sqlite3
from datetime import datetime

from src.utils import DatabaseError


def init_db(DB_PATH:str) -> sqlite3.Connection:
    """Initialize SQLite DB and tables (if not exist)."""
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id TEXT PRIMARY KEY,
            file_name TEXT,
            file_blob BLOB,
            uploaded_at TIMESTAMP,
            model_name TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            id TEXT,
            batch_id TEXT,
            doi_issn TEXT,
            title TEXT,
            authors TEXT,
            summary TEXT,
            processed_at TIMESTAMP,
            model_name TEXT,
            FOREIGN KEY(id) REFERENCES uploads(id),
            FOREIGN KEY(batch_id) REFERENCES outputs(batch_id)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS outputs (
            batch_id TEXT PRIMARY KEY,
            excel_blob BLOB,
            generated_at TIMESTAMP
        )""")

        conn.commit()
        
        return conn

    except sqlite3.Error as e:
        
        raise DatabaseError(f"Failed to initialize database at {DB_PATH}: {e}")

def insert_upload(conn, uid, file_name, file_bytes, llm_model):
    """Insert a raw PDF upload record."""
    try:
        ts = datetime.now()
        conn.execute(
            "INSERT INTO uploads (id, file_name, file_blob, uploaded_at, model_name) VALUES (?,?,?,?,?)",
            (uid, file_name, file_bytes, ts, llm_model)
        )
        conn.commit()
        
    except sqlite3.IntegrityError as e:
        
        raise DatabaseError(f"Upload uid={uid} already exists: {e}")
    except sqlite3.Error as e:
        
        raise DatabaseError(f"Failed to insert upload record for uid={uid}: {e}")

def insert_metadata(conn, uid: str, batch_id: str,
                    doi: str, title: str,
                    authors: str, summary: str, llm_model:str):
    """
    Insert extracted metadata for a given upload and batch.

    Args:
        conn: sqlite3.Connection
        uid: Upload ID
        batch_id: Batch run ID
        doi: DOI or ISSN
        title: Paper title
        authors: Author list
        summary: LLM-generated summary
        llm_model: model used

    Raises:
        DatabaseError: on any sqlite3 failure.
    """
    try:
        # Time in IST
        ts = datetime.now()
        conn.execute(
            """
            INSERT INTO metadata
              (id, batch_id, doi_issn, title, authors, summary, processed_at, model_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (uid, batch_id, doi, title, authors, summary, ts, llm_model)
        )
        conn.commit()
       
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to insert metadata for uid={uid}: {e}")

def insert_output(conn, batch_id, excel_bytes):
    """Insert the final Excel blob of a batch run."""
    try:
        ts = datetime.now()
        conn.execute(
            "INSERT INTO outputs (batch_id, excel_blob, generated_at) VALUES (?,?,?)",
            (batch_id, excel_bytes, ts)
        )
        conn.commit()
        
    except sqlite3.IntegrityError as e:
        
        raise DatabaseError(f"Output batch_id={batch_id} already exists: {e}")
    except sqlite3.Error as e:
        
        raise DatabaseError(f"Failed to insert output for batch_id={batch_id}: {e}")



def fetch_all_uploads(conn):
    """
    Return a list of (id, file_name, uploaded_at) for all uploads.
    """
    try:
        rows = conn.execute(
            "SELECT id, file_name, uploaded_at FROM uploads ORDER BY uploaded_at DESC"
        ).fetchall()
        return rows
    except sqlite3.Error as e:
        
        raise DatabaseError(f"Could not fetch uploads: {e}")

def fetch_metadata(conn, uid):
    """
    Return a dict of metadata for the given upload id, or None if not found.
    Now includes batch_id.
    """
    try:
        row = conn.execute(
            """
            SELECT batch_id, doi_issn, title, authors, summary, processed_at, model_name
              FROM metadata
             WHERE id = ?
            """,
            (uid,)
        ).fetchone()
        if not row:
            return None

        batch_id, doi, title, authors, summary, processed_at, model_name = row
        return {
            "batch_id":    batch_id,
            "doi_issn":    doi,
            "title":       title,
            "authors":     authors,
            "summary":     summary,
            "processed_at": processed_at,
            "model_name" : model_name
        }
    except sqlite3.Error as e:
        raise DatabaseError(f"Could not fetch metadata for {uid}: {e}")


def fetch_upload_blob(conn, uid):
    """
    Return the PDF blob for the given upload id, or None if not found.
    """
    try:
        row = conn.execute(
            "SELECT file_blob, file_name FROM uploads WHERE id = ?", (uid,)
        ).fetchone()
        if not row:
            return None, None
        blob, file_name = row
        return blob, file_name
    except sqlite3.Error as e:
        
        raise DatabaseError(f"Could not fetch upload blob for {uid}: {e}")

def fetch_output_blob(conn, batch_id):
    """
    Return the Excel blob for the given batch id, or None if not found.
    """
    try:
        row = conn.execute(
            "SELECT excel_blob FROM outputs WHERE batch_id = ?", (batch_id,)
        ).fetchone()
        if not row:
            return None
        blob = row[0]
        return blob
    except sqlite3.Error as e:
        
        raise DatabaseError(f"Could not fetch output blob for {batch_id}: {e}")