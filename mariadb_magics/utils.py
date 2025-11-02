import pandas as pd
from typing import Any, Iterable, Tuple

def rows_to_dataframe(cursor) -> pd.DataFrame:
    cols = [c[0] for c in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=cols)

def execute_and_fetch(conn_wrapper, sql: str, params: Iterable = None, to_df: bool = True):
    cur = conn_wrapper.cursor()
    try:
        cur.execute(sql, params or ())
    except Exception:
        # try executing as multi-statement
        cur.execute(sql) 
    if to_df:
        df = rows_to_dataframe(cur)
        cur.close()
        return df
    else:
        results = cur.fetchall()
        cur.close()
        return results
