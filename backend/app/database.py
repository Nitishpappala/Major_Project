import os
from dotenv import load_dotenv
from databricks.sql import connect as databricks_connect

load_dotenv()

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")


def get_connection():
    """Create and return a Databricks SQL connection."""
    return databricks_connect(
        server_hostname=DATABRICKS_HOST.replace("https://", ""),
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_TOKEN,
    )


def execute_query(query: str, params: dict | None = None) -> list[dict]:
    """Execute a SQL query against Databricks and return results as a list of dicts."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def execute_scalar(query: str, params: dict | None = None):
    """Execute a query and return the first column of the first row."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()
