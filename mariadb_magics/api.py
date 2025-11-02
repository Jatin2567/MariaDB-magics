from .connection import connect, get_connection, close, close_all
from .utils import execute_and_fetch
from typing import Iterable, Optional, Any
from .vector import vector_search
from .temporal import temporal_query
from .plot import plot_query

def execute_sql(conn_name: str, sql: str, params: Iterable = None, to_df: bool = True):
    cw = get_connection(conn_name)
    return execute_and_fetch(cw, sql, params=params, to_df=to_df)

def connect_db(name: str = "default", **db_config):
    return connect(name=name, **db_config)

def vector_search_api(*args, **kwargs):
    return vector_search(*args, **kwargs)

def temporal_query_api(*args, **kwargs):
    return temporal_query(*args, **kwargs)

def plot_query_api(*args, **kwargs):
    return plot_query(*args, **kwargs)
