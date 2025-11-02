from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import warnings , math ,traceback , json 
from .connection import get_connection
from .utils import execute_and_fetch
from sklearn.metrics.pairwise import cosine_similarity

_EMBED_MODEL = os.getenv("MARIADB_MAGICS_EMBED_MODEL", "paraphrase-MiniLM-L3-v2")
_local_encoder = None

def _ensure_local_encoder():
    global _local_encoder
    if _local_encoder is None:
        _local_encoder = SentenceTransformer(_EMBED_MODEL)
    return _local_encoder

def embed_texts(texts: List[str], provider: str = "local", **provider_kwargs) -> List[List[float]]:
    if provider == "local":
        model = _ensure_local_encoder()
        return model.encode(texts, show_progress_bar=False).tolist()
  
    else:
        raise ValueError("unknown provider")
def _normalize(v):
    v = np.asarray(v, dtype=float)
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v

def vector_search(
    conn_name: str,
    table: str,
    text_query: str,
    embed_column: str = "embedding",
    id_column: str = "id",
    top_k: int = 10,
    provider: str = "local",
    **provider_kwargs
):
    """
    1) embed the query (via embed_texts)
    2) try server-side vector distance using VEC_DISTANCE_COSINE (MariaDB)
    3) fallback: SELECT VEC_ToText(embedding) and compute cosine similarity locally
    """

    # 1) embed the query
    vec = embed_texts([text_query], provider=provider, **provider_kwargs)[0]
    vec_json = json.dumps([float(x) for x in vec])   # JSON array string

    cw = get_connection(conn_name)

    # 2) Try server-side vector distance (preferred)
    try:
        # Use VEC_FromText(param) to convert JSON array string into a VECTOR on server side,
        # and use the built-in distance function. Use ASC for distance (small = similar).
        # If your MariaDB exposes a different function name, adapt (VEC_DISTANCE_COSINE/VEC_DISTANCE_L2).
        sql = f"""
        SELECT {id_column} AS id,
               VEC_DISTANCE_COSINE(VEC_FromText(%s), {embed_column}) AS _distance
        FROM {table}
        ORDER BY _distance ASC
        LIMIT %s;
        """
        df = execute_and_fetch(cw, sql, params=(vec_json, top_k), to_df=True)
        # If server returned a dataframe, convert distance to score (higher = more similar)
        if not df.empty:
            df["_score"] = 1.0 - df["_distance"]   # optional: convert distance->similarity proxy
            df = df.sort_values("_score", ascending=False).reset_index(drop=True)
        return df

    except Exception as server_err:
        warnings.warn("Server-side vector search failed; falling back to client-side. "
                      f"Server error: {server_err}")
        # print traceback optionally for debugging
        # traceback.print_exc()

    # 3) Fallback: fetch readable vectors with VEC_ToText(...) and compute cosine locally
    try:
        sql = f"SELECT {id_column} AS id, VEC_ToText({embed_column}) AS emb_text FROM {table};"
        df_all = execute_and_fetch(cw, sql, to_df=True)
        if df_all.empty:
            return df_all

        # parse emb_text (should be a JSON array string like "[0.001, 0.234, ...]")
        def parse_emb_text(x):
            if x is None:
                return None
            # the server should return a string JSON; if bytes, decode
            if isinstance(x, (bytes, bytearray)):
                x = x.decode('utf-8', errors='ignore')
            if isinstance(x, str):
                try:
                    return np.array(json.loads(x), dtype=float)
                except Exception:
                    # sometimes VEC_ToText may return '0.1,0.2,0.3' (rare) -> try split
                    try:
                        return np.array([float(i) for i in x.strip().split(',')], dtype=float)
                    except Exception:
                        raise ValueError(f"Unable to parse embedding text: {x[:200]}")
            if isinstance(x, (list, tuple)):
                return np.array(x, dtype=float)
            raise ValueError("Unknown format for embedding column")

        emb_list = []
        ids = []
        for _, row in df_all.iterrows():
            try:
                v = parse_emb_text(row["emb_text"])
                if v is None:
                    continue
                emb_list.append(v)
                ids.append(row["id"])
            except Exception as e:
                # skip malformed rows but warn
                warnings.warn(f"Skipping id={row['id']} due to parse error: {e}")

        if not emb_list:
            return df_all  # nothing to score

        vectors = np.vstack(emb_list)   # shape (N, dim)
        qvec = np.asarray(vec, dtype=float).reshape(1, -1)
        # normalize to compute cosine
        qn = _normalize(qvec)
        vn = np.vstack([_normalize(v) for v in vectors])
        sims = cosine_similarity(qn, vn)[0]
        # build result DataFrame
        import pandas as pd
        res = pd.DataFrame({"id": ids, "_score": sims})
        res = res.sort_values("_score", ascending=False).head(top_k).reset_index(drop=True)
        return res

    except Exception as fallback_err:
        # worst-case: re-raise so caller sees the error
        traceback.print_exc()
        raise RuntimeError(f"Both server and fallback vector search failed: {fallback_err}") from fallback_err