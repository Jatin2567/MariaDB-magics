import threading
import os 
os.add_dll_directory(r"C:\Program Files\MariaDB\MariaDB Connector C 64-bit\lib\mariadb")

import mariadb  # pip install mariadb
import time
from typing import Dict, Optional

class ConnectionWrapper:
    def __init__(self, conn, config):
        self.conn = conn
        self.config = config
        self.last_used = time.time()

    def cursor(self, *args, **kwargs):
        self.last_used = time.time()
        return self.conn.cursor(*args, **kwargs)

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

# A simple thread-safe connection manager supporting named connections
class ConnectionManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._conns: Dict[str, ConnectionWrapper] = {}

    def connect(self, name: str = "default", **db_config) -> ConnectionWrapper:
        """
        Connect and store under `name`. db_config is passed to mariadb.connect(...)
        Example db_config: user, password, host, port, database
        """
        with self._lock:
            if name in self._conns:
                # if alive, return it
                cw = self._conns[name]
                try:
                    cw.conn.ping(reconnect=True)
                    return cw
                except Exception:
                    cw.close()
                    del self._conns[name]

            conn = mariadb.connect(**db_config)
            cw = ConnectionWrapper(conn, db_config)
            self._conns[name] = cw
            return cw

    def get(self, name: str = "default") -> Optional[ConnectionWrapper]:
        with self._lock:
            return self._conns.get(name)

    def close(self, name: str = "default"):
        with self._lock:
            cw = self._conns.pop(name, None)
            if cw:
                cw.close()

    def close_all(self):
        with self._lock:
            names = list(self._conns.keys())
            for n in names:
                self.close(n)

# module-level manager
_mgr = ConnectionManager()

def connect(name: str = "default", **db_config):
    """
    Public function to create/store a connection.
    Returns ConnectionWrapper
    """
    return _mgr.connect(name=name, **db_config)

def get_connection(name: str = "default"):
    cw = _mgr.get(name)
    if cw is None:
        raise RuntimeError(f"No connection named '{name}' — call connect(...) first")
    return cw

def close(name: str = "default"):
    _mgr.close(name)

def close_all():
    _mgr.close_all()
