from .utils import execute_and_fetch
from .connection import get_connection
from typing import Optional
import pandas as pd

def plot_query(conn_name: str, sql: str, engine: str = "matplotlib", index_col: Optional[str] = None, plot_kind: str = "line", **plot_kwargs):
    """
    Execute SQL and plot results inline. Returns the dataframe as well.

    - engine: "matplotlib" or "plotly"
    - index_col: if provided, set DataFrame index for plotting
    - plot_kind: any pandas plot kind: "line", "bar", "scatter" (for scatter, pass x and y in plot_kwargs)
    """
    cw = get_connection(conn_name)
    df = execute_and_fetch(cw, sql)
    if df.empty:
        return df

    if index_col:
        if index_col not in df.columns:
            raise ValueError(f"index_col '{index_col}' not in query result columns.")
        df = df.set_index(index_col)

    # plotting without specifying colors/styles (per notebook style guidelines)
    if engine == "matplotlib":
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 5))
        if plot_kind == "scatter":
            x = plot_kwargs.get("x")
            y = plot_kwargs.get("y")
            if not x or not y:
                raise ValueError("scatter requires x and y in plot_kwargs")
            plt.scatter(df[x], df[y])
            plt.xlabel(x); plt.ylabel(y)
        else:
            getattr(df.plot, plot_kind)(**plot_kwargs)
        plt.tight_layout()
        plt.show()
    elif engine == "plotly":
        import plotly.express as px
        if plot_kind == "scatter":
            fig = px.scatter(df, x=plot_kwargs.get("x"), y=plot_kwargs.get("y"))
        else:
            fig = getattr(px, plot_kind)(df)
        fig.show()
    else:
        raise ValueError("unknown plotting engine")

    return df
