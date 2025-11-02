from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)
from IPython.display import display, Markdown
from .connection import connect, get_connection
from .api import execute_sql, vector_search_api, temporal_query_api, plot_query_api
import shlex,re

print("LOADED mariadb_magics.magics from", __file__)

@magics_class
class MariaDBMagics(Magics):
    @line_magic
    def mariadb_connect(self, line):
        """
        Usage:
          %mariadb_connect name --user USER --password PWD --host HOST --port PORT --database DB
        Example:
          %mariadb_connect default --user alice --password secret --host 127.0.0.1 --port 3306 --database mydb
        """
        parts = shlex.split(line)
        if not parts:
            print("Usage: %mariadb_connect name --user USER --password PWD --host HOST --port PORT --database DB")
            return
        name = parts[0]
        # parse rest as simple --key val
        kv = {}
        i = 1
        while i < len(parts):
            key = parts[i]
            if key.startswith("--"):
                val = parts[i+1] if i+1 < len(parts) else None
                kv[key[2:]] = val
                i += 2
            else:
                i += 1
        if "port" in kv:
            kv["port"] = int(kv["port"])
        print("MAGIC connect args ->", kv) 
        connect(name=name, **kv)
        print(f"Connected as '{name}'")

    @line_cell_magic
    def mariadb(self, line, cell=None):
        """
        %mariadb <conn_name> <sql>         -> run SQL inline (line)
        %%mariadb <conn_name>              -> the cell contains SQL
        """
        parts = shlex.split(line)
        if not parts:
            print("Usage: %mariadb <conn_name> <sql>  (or use cell magic)")
            return
        conn_name = parts[0]
        if cell is None:
            sql = " ".join(parts[1:])
        else:
            sql = cell
        df = execute_sql(conn_name, sql)
        display(df)
        return df

    @line_magic
    def mariadb_vector(self, line):
        """
        %mariadb_vector conn_name table "search text" [--top_k 10] [--embed_column embedding]
        """
        parts = shlex.split(line)
        if len(parts) < 3:
            print("Usage: %mariadb_vector conn_name table \"search text\" [--top_k 10]")
            return
        conn_name = parts[0]
        table = parts[1]
        query_text = parts[2]
        # parse optional flags
        opts = {"top_k": 10, "embed_column": "embedding"}
        i = 3
        while i < len(parts):
            p = parts[i]
            if p.startswith("--"):
                key = p[2:]
                val = parts[i+1]
                opts[key] = int(val) if val.isdigit() else val
                i += 2
            else:
                i += 1
        df = vector_search_api(conn_name=conn_name, table=table, text_query=query_text, top_k=opts["top_k"], embed_column=opts["embed_column"])
        display(df)
        return df

    @line_magic
    def mariadb_time(self, line):
        """
        %mariadb_time conn_name "SELECT ... FROM table" as_of YYYY-MM-DD [--temporal_keyword "FOR SYSTEM_TIME AS OF"]
        Example:
          %mariadb_time default "SELECT * FROM experiments WHERE metric > 0.5" as_of 2024-01-01
        """
        parts = shlex.split(line)
        if "as_of" not in parts:
            print("usage: %mariadb_time conn_name \"<sql>\" as_of YYYY-MM-DD")
            return
        conn_name = parts[0]
        # get SQL between quotes
        # naive parse:
        # find index of 'as_of'
        ai = parts.index("as_of")
        sql = " ".join(parts[1:ai])
        as_of = parts[ai + 1]
        # optionally temporal_keyword
        dialect_override = {}
        if "--temporal_keyword" in parts:
            idx = parts.index("--temporal_keyword")
            dialect_override["temporal_keyword"] = parts[idx + 1]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of):
            as_of = as_of + " 00:00:00"
        df = temporal_query_api(conn_name=conn_name, base_sql=sql, as_of=as_of, dialect_override=dialect_override)
        display(df)
        return df

    @line_magic
    def mariadb_plot(self, line):
        """
        %mariadb_plot conn_name "SELECT date, metric FROM ..." --index_col date --engine matplotlib --kind line
        """
        parts = shlex.split(line)
        if len(parts) < 2:
            print("usage: %mariadb_plot conn_name \"SELECT ...\" [--index_col colname] [--engine matplotlib|plotly] [--kind line]")
            return
        conn_name = parts[0]
        # collect sql inside quotes or remaining
        sql = " ".join(parts[1:])  # naive; good enough for most
        opts = {}
        if "--index_col" in parts:
            idx = parts.index("--index_col")
            opts["index_col"] = parts[idx + 1]
        if "--engine" in parts:
            idx = parts.index("--engine")
            opts["engine"] = parts[idx + 1]
        if "--kind" in parts:
            idx = parts.index("--kind")
            opts["plot_kind"] = parts[idx + 1]
        df = plot_query_api(conn_name=conn_name, sql=sql, **opts)
        display(df)
        return df

def load_ipython_extension(ipython):
    ipython.register_magics(MariaDBMagics)
    print("mariadb-magics loaded. Use %mariadb_connect to create a connection.")

def unload_ipython_extension(ipython):
    # nothing fancy here
    print("mariadb-magics unloaded.")
