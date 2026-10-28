# MariaDB Magics Studio

A Google-inspired, responsive web workspace based on Jatin Aggarwal's MariaDB Magics Jupyter project. This is a standalone web adaptation of its four workflows, not a Jupyter frontend or a Google product. The original project and its credentials were not modified or copied.

## Start with Docker

From this folder, run:

```sh
docker compose up --build -d
```

Open http://localhost:8080. Docker Desktop must be running. The default demo uses an in-memory SQLite dataset, rebuilt per request. SQL, charts, schema browsing, CSV export, and browser-local saved queries work in demo mode. Native vector and temporal operations require live MariaDB and return clear errors in demo mode.

## Start without Docker

Python 3.12 or newer:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install 'Flask>=3.1,<4' 'waitress>=3.0.2,<4'
waitress-serve --host=127.0.0.1 --port=8080 server:app
```

For live mode also install requirements.txt (the official MariaDB connector requires MariaDB Connector/C development libraries). The Dockerfile installs these libraries automatically on Linux.

## Connect a real database

The deployed [self-setup guide](https://mariadb-magics-studio.onrender.com/docs) explains how each reader runs their own Studio and MariaDB 11.8 locally with `compose.live.yaml`, or connects their own separate Studio installation to an existing database. The public deployment remains a sample-data demo. It does not provision cloud databases, collect visitors' database credentials, or grant database compute through sign-in. Downloadable `static/setup.sql` creates the tutorial vector and system-versioned tables in a fresh schema. Run it once as the schema owner using an admin SQL client; Studio is read-only.

Copy `.env.example` to `.env` for Docker Compose. Set STUDIO_MODE=live, STUDIO_TOKEN to a random string of at least 24 characters, and DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD. Generate a token with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Sign in using Connection in the UI; sign out ends the session. HttpOnly, SameSite=Strict cookies hold the signed session, with Secure enabled on Render. The default signing key changes when STUDIO_TOKEN rotates; optionally configure SESSION_SECRET independently. Bearer tokens remain supported for API clients. The single-process login limiter permits 10 attempts per minute per observed client address. Database credentials never enter the browser. Local Python startup reads environment variables, not .env files.

Use a dedicated database account granted SELECT only on the chosen schema. Do not grant FILE, EXECUTE, administrative privileges, or access to unrelated schemas. The SQL prefix filter is a convenience guard, not a SQL security parser. Read-only transactions and database permissions enforce access. Connections are isolated per request, closed afterward, and limited to 10 seconds per statement. Results are capped at 500 rows. CTEs and writes are intentionally outside this read-only editor's scope.

To expose the service beyond localhost, use a TLS reverse proxy in front of port 8080 and retain token authentication. This is a single trusted-workspace application, not a multi-user authorization system. Configure DB_SSL_CA and mount a CA file into the container for verified TLS to a remote database. Do not expose the MariaDB port publicly. Rotate the shared workspace token when access changes.

## Workflows

- SQL workspace: edit and execute SELECT, use Ctrl/Cmd+Enter, browse table columns, load examples, save queries locally, export CSV.
- Visualizations: choose label/value columns for a horizontal bar chart of the first 20 result rows. Negative values are red and lengths represent magnitude.
- Vector search: use native VECTOR columns and VEC_DISTANCE_COSINE with parameterized VEC_FromText. Provide a numeric query vector, or install requirements-embeddings.txt for text input. The optional model is paraphrase-MiniLM-L3-v2, matching the original project; override EMBED_MODEL to match your indexed data. Initial text use downloads model weights. Install optional dependencies in a derived Docker image if using containers. Model dimensions must match stored vectors; use a cosine VECTOR INDEX for index-assisted cosine search.
- Time travel: a table must have WITH SYSTEM VERSIONING enabled. Input is interpreted in the database session time zone. Uses an exact, parameterized FOR SYSTEM_TIME AS OF TIMESTAMP query; it fixes the original code's one-second offset and string substitution.

## MariaDB alignment — checked October 28, 2026

GitHub's server releases currently include 13.0.2, 13.1.1 RC, 12.3.3, and 11.8.9. This app targets **11.8 LTS as its conservative feature baseline**, not the newest rolling release. It checks VERSION() and probes native vector support on the actual connected server instead of assuming all versions expose it. No live-server compatibility claim is implied by the demo.

Connector/Python GitHub releases identify **1.1.14 as stable** and **2.0.0rc2 as prerelease**. The dependency is pinned to 1.1.14; the app does not depend on prerelease async or pooling APIs. Native vector functions are available in Community 11.7+ (and Enterprise 11.4.5-3+); 11.8 provides an LTS baseline. The original Windows DLL path and heavyweight notebook imports are absent from this portable adapter. There is no silent client-side vector fallback that could hide server incompatibilities.

Sources:

- https://github.com/MariaDB/server/releases
- https://github.com/mariadb-corporation/mariadb-connector-python/releases
- https://github.com/mariadb-corporation/mariadb-docs/blob/main/release-notes/community-server/11.8/what-is-mariadb-118.md
- https://mariadb.com/docs/server/reference/sql-functions/vector-functions/vec_distance_cosine
- https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/system-versioned-tables

Before upgrading an existing database, follow MariaDB's upgrade procedure: 11.8 changes timestamp ranges and upgrades to system-versioned tables can require rewriting rows and indexes. This application never upgrades your database.

## Validation

```sh
python -m unittest discover -s tests -v
node --check static/app.js
```

Unit tests cover real demo SQL execution, write/multi-statement rejection, authentication, schema, explicit demo limitations, and parameterized temporal/vector query generation. Mocked live-query tests are not live MariaDB integration tests. Docker build and live database validation require a running Docker engine and a configured MariaDB instance.

The setup-guide update was also verified against an isolated MariaDB 12.0.2 server: tutorial SQL, native cosine ranking (IDs 1, 2, 3), historical salary 100000 versus current 125000, microsecond timestamp round-trip, and session login/logout using a SELECT-only account. This does not verify an individual MariaDB Cloud account or its default server version. The local Compose file validates; its complete Docker stack was not run because the Docker engine was stopped.

MIT license; original attribution retained in LICENSE.
