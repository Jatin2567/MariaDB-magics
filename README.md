# 🧠 MariaDB Magics

**MariaDB Magics** is a powerful Jupyter extension that brings MariaDB directly into your notebooks — combining SQL, vector search, time utilities, and visualization in one clean, magic-driven interface.

> 🚀 Ideal for analytics, embeddings, and temporal insights — all from your MariaDB database.

---

## 🌟 Features

| Magic | Purpose | Example |
|--------|----------|----------|
| `%mariadb` | Run SQL queries directly in notebooks and return Pandas DataFrames | `%mariadb myconn "SELECT * FROM employees LIMIT 10"` |
| `%mariadb_plot` | Generate visualizations directly from query results | `%mariadb_plot myconn "SELECT dept, AVG(salary) FROM employees GROUP BY dept"` |
| `%mariadb_time` | Use MariaDB’s time-series functions and do temporal analysis easily | `%mariadb_time myconn "SELECT * FROM sales" --window week` |
| `%mariadb_vector` | Perform vector similarity search using locally or cloud-embedded models | `%mariadb_vector myconn mytable "Find documents about AI"` |

---

## 🧩 Repository Structure

mariadb-magics/
├── mariadb_magics/
│   ├── api.py             # Orchestrator for API-based calls
│   ├── connection.py      # Connection manager for named MariaDB sessions
│   ├── magics.py          # Registers %mariadb*, line/cell magics
│   ├── plot.py            # Implements %mariadb_plot for instant charts
│   ├── temporal.py        # Implements %mariadb_time for date/time analytics
│   ├── utils.py           # Shared utility functions (execute_and_fetch, logging, etc.)
│   └── vector.py          # Vector embeddings + similarity search logic
│
├── requirements.txt       # All dependencies
├── pyproject.toml         # Package metadata & build config
└── README.md              # You’re here

---

## ⚙️ Installation

### 1️⃣ Clone the repository
git clone https://github.com/jatin2567/mariadb-magics.git
cd mariadb-magics

### 2️⃣ Install dependencies
pip install -r requirements.txt

or in editable dev mode:

pip install -e .

---

## 🧠 Usage

### 1️⃣ Start Jupyter Notebook or Lab
jupyter notebook

### 2️⃣ Register the magics
%load_ext mariadb_magics

### 3️⃣ Connect to MariaDB
%mariadb_connect myconn --user root --password root --host 127.0.0.1 --port 3306 --database testdb
(fill the required values as per your configuration)

You can now use your connection name (`myconn`) in all magics.

---

## 🧮 SQL Magic: %mariadb

Execute SQL directly and return results as Pandas DataFrames:

%mariadb myconn "SELECT * FROM employees WHERE salary > 50000"


---

## 📊 Plot Magic: %mariadb_plot

Generate charts directly from MariaDB queries:

%mariadb_plot myconn "SELECT department, COUNT(*) as emp_count FROM employees GROUP BY department"

Supports:
- Bar, line, scatter (auto-inferred from data)
- Aggregations and grouping
- Inline plotting in notebooks

---

## ⏱️ Time Magic: %mariadb_time

Easily handle temporal analytics and date-based transformations.

%mariadb_time myconn "SELECT timestamp, value FROM metrics" as_of '2025-11-02 13:31:59' 

Supports:
- Time bucketing (`hour`, `day`, `week`)
- Temporal joins
- Sliding windows

---

## 🔍 Vector Magic: %mariadb_vector

Run semantic similarity search directly from your notebook.

%mariadb_vector myconn documents "Find AI and ML research papers" --top_k 5

This:
1. Embeds the query text using a local `sentence-transformers` model  
2. Fetches stored embeddings from MariaDB  
3. Computes cosine similarity (client-side fallback for any storage format)  
4. Returns the most relevant rows as a ranked DataFrame

Embeddings in MariaDB can be stored as:
- JSON arrays ("[0.12, 0.45, ...]")
- Comma-separated strings
- Binary blobs (auto-decoded if possible)

---

## 🧰 Technical Notes

- Compatible with **MariaDB ≥ 11.4**  
- Supports **Jupyter Notebook / Lab / VSCode Notebooks**  
- Local CPU embeddings use `sentence-transformers` (`paraphrase-MiniLM-L3-v2` by default)  
- Connection pooling and retry logic included in `connection.py` and `utils.py`  
- Modular architecture allows standalone imports (you can use `mariadb_magics.vector` separately)

---

## 🎥 Demo Video

📺 **[Watch a short demo on YouTube](https://youtu.be/ga9oiEFNl6s)**  
This shows:
- Connecting to MariaDB  
- Running `%mariadb` queries  
- Creating visualizations  
- Performing semantic vector search  

---

## 🤝 Contributing

Contributions are welcome!

1. Fork this repository  
2. Create a feature branch  
3. Commit and push changes  
4. Open a Pull Request

Please include a clear description and example for any new magic or enhancement.

---

## 📄 License

MIT License © 2025 Jatin Aggarwal

---

