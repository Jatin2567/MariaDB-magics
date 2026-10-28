"""MariaDB Magics Studio: same-origin, read-only web adapter."""
import os, re, json, math, sqlite3, time, secrets
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 65536
MODE = os.getenv('STUDIO_MODE', 'demo')
TOKEN = os.getenv('STUDIO_TOKEN', '')
if MODE not in ('demo', 'live'):
    raise RuntimeError('STUDIO_MODE must be demo or live')
if MODE == 'live' and len(TOKEN) < 24:
    raise RuntimeError('Live mode requires STUDIO_TOKEN of at least 24 characters')

EMPLOYEES = [(1,'Olivia Chen','Engineering',125000,'2025-01-12'),(2,'Liam Patel','Design',98000,'2025-02-18'),(3,'Emma Wilson','Engineering',118000,'2025-03-04'),(4,'Noah Garcia','Marketing',89000,'2025-03-21'),(5,'Ava Johnson','Product',112000,'2025-04-09'),(6,'Ethan Kim','Engineering',132000,'2025-05-16'),(7,'Mia Brown','Design',105000,'2025-06-02'),(8,'Lucas Singh','Marketing',94000,'2025-07-11')]
DOCS = [(1,'Getting started with MariaDB','Connect your application and explore SQL.'),(2,'Native vector search','Find similar embeddings using cosine distance.'),(3,'Travel through your data','System-versioned tables preserve historical records.'),(4,'Visualize your results','Build charts from SQL aggregations.')]

def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}', value):
        raise ValueError('Use a simple table or column name (letters, numbers, underscores).')
    return '`' + value + '`'

@contextmanager
def connection():
    if MODE == 'demo':
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE employees (id INT, name TEXT, department TEXT, salary INT, joined_at TEXT)')
        conn.executemany('INSERT INTO employees VALUES (?,?,?,?,?)', EMPLOYEES)
        conn.execute('CREATE TABLE documents (id INT, title TEXT, content TEXT)')
        conn.executemany('INSERT INTO documents VALUES (?,?,?)', DOCS)
        conn.commit()
        conn.execute('PRAGMA query_only = ON')
        deadline = time.monotonic() + 5
        conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
    else:
        import mariadb
        config = dict(host=os.getenv('DB_HOST','db'), port=int(os.getenv('DB_PORT','3306')), user=os.getenv('DB_USER','studio_reader'), password=os.environ['DB_PASSWORD'], database=os.getenv('DB_NAME','magics'), connect_timeout=5)
        if os.getenv('DB_SSL_CA'):
            config.update(ssl_ca=os.environ['DB_SSL_CA'], ssl_verify_cert=True)
        conn = mariadb.connect(**config)
        cur = conn.cursor()
        cur.execute('SET SESSION max_statement_time=10')
        cur.execute('START TRANSACTION READ ONLY')
        cur.close()
    try:
        yield conn
    finally:
        conn.close()

def execute(sql, params=()):
    with connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(501) if columns else []
            return dict(columns=columns, rows=[[v.hex() if isinstance(v,bytes) else v for v in row] for row in rows[:500]], truncated=len(rows)>500)
        finally:
            cur.close()

@app.before_request
def protect():
    if request.path.startswith('/api/') and TOKEN:
        if not secrets.compare_digest(request.headers.get('Authorization',''), 'Bearer '+TOKEN):
            return jsonify(error='Enter the workspace access token in Connection settings.'), 401
    if request.method == 'POST' and not request.is_json:
        return jsonify(error='JSON content required'), 415

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
    response.headers['Cache-Control']='no-store'
    return response

@app.get('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.get('/healthz')
def health():
    return jsonify(status='ok')

@app.get('/api/status')
def status():
    if MODE == 'demo':
        return jsonify(mode=MODE, version='SQLite sample workspace', database='magics_demo', vector=False)
    version=execute('SELECT VERSION()')['rows'][0][0]
    try:
        execute("SELECT VEC_DISTANCE_COSINE(VEC_FromText('[1,0]'),VEC_FromText('[1,0]'))")
        vector=True
    except Exception:
        vector=False
    return jsonify(mode=MODE,version=version,database=os.getenv('DB_NAME','magics'),vector=vector)

@app.get('/api/schema')
def schema():
    if MODE == 'demo':
        return jsonify(tables=[dict(name='employees',columns=['id','name','department','salary','joined_at']),dict(name='documents',columns=['id','title','content'])])
    result=execute('SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION')
    tables={}
    for table,column in result['rows']:
        tables.setdefault(table,[]).append(column)
    return jsonify(tables=[dict(name=k,columns=v) for k,v in tables.items()])

@app.post('/api/query')
def query():
    sql=request.json.get('sql','').strip().rstrip(';')
    # This is a UX guard; database SELECT-only privileges are the security boundary.
    if not re.match(r'^SELECT\b',sql,re.I) or ';' in sql or re.search(r'\b(INTO|OUTFILE|DUMPFILE|FOR\s+UPDATE|LOCK\s+IN)\b',sql,re.I):
        raise ValueError('Run one read-only SELECT statement at a time.')
    start=time.perf_counter()
    result=execute(sql)
    result['elapsed_ms']=round((time.perf_counter()-start)*1000,1)
    return jsonify(result)

@app.post('/api/temporal')
def temporal():
    if MODE == 'demo':
        raise ValueError('Time travel needs a live MariaDB connection and a system-versioned table. Demo data has no history.')
    table=identifier(request.json.get('table'))
    timestamp=datetime.fromisoformat(request.json.get('as_of','')).isoformat(sep=' ')
    return jsonify(execute(f'SELECT * FROM {table} FOR SYSTEM_TIME AS OF TIMESTAMP ? LIMIT 500',(timestamp,)))

@app.post('/api/vector')
def vector():
    if MODE == 'demo':
        raise ValueError('Native vector search needs live MariaDB. Connect a database with VECTOR columns to run this search.')
    data=request.json
    table=identifier(data.get('table'))
    column=identifier(data.get('column','embedding'))
    key=identifier(data.get('id_column','id'))
    k=int(data.get('top_k',5))
    if not 1<=k<=100:
        raise ValueError('Top K must be between 1 and 100.')
    vec=data.get('vector')
    if data.get('text','').strip():
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ValueError('Text embeddings are optional. Install requirements-embeddings.txt on the server, or paste a query vector.')
        # Model must match the model used to embed stored documents.
        if not hasattr(app,'encoder'):
            app.encoder=SentenceTransformer(os.getenv('EMBED_MODEL','paraphrase-MiniLM-L3-v2'))
        vec=app.encoder.encode(data['text'][:4000]).tolist()
    if not isinstance(vec,list) or not 1<=len(vec)<=16383 or any(type(v) not in (int,float) or not math.isfinite(v) for v in vec) or not any(vec):
        raise ValueError('Provide a nonzero vector of finite numbers, matching the stored embedding dimensions.')
    sql=f'SELECT {key} AS id, VEC_DISTANCE_COSINE({column}, VEC_FromText(?)) AS distance FROM {table} ORDER BY distance ASC LIMIT ?'
    return jsonify(execute(sql,(json.dumps(vec),k)))

@app.errorhandler(Exception)
def error(exc):
    from werkzeug.exceptions import HTTPException
    if isinstance(exc,HTTPException):
        return jsonify(error=exc.description),exc.code
    if isinstance(exc,(ValueError,TypeError,KeyError)) or MODE=='demo':
        return jsonify(error=str(exc)),400
    app.logger.exception('Database operation failed')
    return jsonify(error='Database request failed. Check table names, column types, permissions, and server logs.'),400

if __name__=='__main__':
    app.run(host=os.getenv('HOST','127.0.0.1'),port=int(os.getenv('PORT','8080')))
