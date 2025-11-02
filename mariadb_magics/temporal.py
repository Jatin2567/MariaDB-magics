from typing import Optional
from .connection import get_connection
from .utils import execute_and_fetch
import re

def expand_temporal_sql(base_sql: str, as_of: str, temporal_keyword: str = "FOR SYSTEM_TIME AS OF TIMESTAMP"):
    """
    Insert temporal clause into SQL depending on syntax. This function is conservative:
    - If the SQL is a simple SELECT FROM <table>, we inject the temporal clause after the table name.
    - Otherwise, callers can provide full SQL.
    """
    # find FROM <table> or FROM `schema`.`table`
    m = re.search(r"FROM\s+([`\"']?[\w\.]+[`\"']?)", base_sql, flags=re.IGNORECASE)
    if not m:
        # unable to expand — return a wrapper that runs the query in a way DB supports or raise
        raise ValueError("Cannot detect FROM table to inject temporal clause; please write full temporal SQL.")
    table_token = m.group(1)
    injected = base_sql.replace(table_token, f"{table_token} {temporal_keyword}ADD(MICROSECOND, 1000000, '{as_of}')", 1)
    return injected

def temporal_query(conn_name: str, base_sql: str, as_of: str, dialect_override: Optional[dict] =  None):
    """
    base_sql: a SQL string (e.g. "SELECT * FROM experiments WHERE metric > 0.5")
    as_of: 'YYYY-MM-DD' or full timestamp string acceptable to your DB
    If your MariaDB version or table uses different syntax, you can pass dialect_override with keys:
      - temporal_keyword: str  (e.g., "FOR SYSTEM_TIME AS OF TIMESTAMP" or "AS OF")
    """
    kw = "FOR SYSTEM_TIME AS OF TIMESTAMP"
    if dialect_override and "temporal_keyword" in dialect_override:
        kw = dialect_override["temporal_keyword"]
    sql = expand_temporal_sql(base_sql, as_of, temporal_keyword=kw)
    cw = get_connection(conn_name)
    print(sql)
    return execute_and_fetch(cw, sql)
