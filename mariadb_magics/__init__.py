from .magics import load_ipython_extension, unload_ipython_extension
from .connection import connect, get_connection, close_all
from .api import execute_sql, vector_search, temporal_query, plot_query

__all__ = [
    "load_ipython_extension",
    "unload_ipython_extension",
    "connect",
    "get_connection",
    "close_all",
    "execute_sql",
    "vector_search",
    "temporal_query",
    "plot_query",
]
