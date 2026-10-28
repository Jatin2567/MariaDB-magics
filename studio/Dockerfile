FROM python:3.12-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libmariadb-dev pkg-config && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m studio
USER studio
EXPOSE 8080
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "server:app"]
