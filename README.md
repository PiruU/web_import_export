# Project Documentation — CSV Import/Export API (FastAPI)

## 1) Overview
This web application implements a simple workflow:
- Import customers and purchases from two CSV files.
- Store them in a lightweight SQLite database.
- Export all customers and their purchases to a remote HTTP endpoint.
- Visualize the exported payload through a demo receiving endpoint.

The source code is organized in the `app/` directory:
- `main.py`: defines the FastAPI routes.
- `impl/import_csv.py`: reads/validates CSV files and performs upsert into SQLite.
- `impl/export_customers.py`: extracts and sends aggregated data to a remote URL.
- `impl/receive_export.py`: simple HTML endpoint to visualize received JSON.
- `impl/customer.py`, `impl/purchase.py`: Pydantic models.
- `impl/customer_db.py`, `impl/purchase_db.py`: SQLite schema and operations.

## 2) Quick Start

### Using Docker
A minimal `Dockerfile` with `uvicorn` is provided.

1. Build:
```bash
docker build -f web_import_export/Dockerfile -t web_import_export:latest .
```

2. Run (exposing port 8000 from the container to 8080 on the host and mounting example CSVs as read-only):
```bash
docker rm -f api 2>/dev/null || true
docker run -d --name api -p 8080:8000   -v "$(pwd)/web_import_export/data:/opt/custexport:ro"   web_import_export:latest
```

3. Swagger / OpenAPI:
- Swagger UI: http://localhost:8080/docs
- OpenAPI JSON: http://localhost:8080/openapi.json

## 3) Expected CSV Files

### `customers.csv`
```
customer_id;title;lastname;firstname;postal_code;city;email
...
```

- Empty fields (`title`, `lastname`, etc.) are converted to `NULL`.
- Primary key: `customers.id` (mapped from `customer_id`).

### `purchases.csv`
```
purchase_identifier;customer_id;product_id;quantity;price;currency;date
...
```
- The Pydantic model accepts alias `purchase_identifier` for `purchase_id`.
- Primary key: `purchases.id` (string, e.g., `2/01`).

## 4) SQLite Data Model

The SQLite file is automatically created (if needed) at `/app/db/db.sqlite3` inside the container.

### Table `customers`
```sql
CREATE TABLE IF NOT EXISTS customers (
  id        INTEGER PRIMARY KEY,
  title     INTEGER,
  lastname  TEXT,
  firstname TEXT,
  zipcode   TEXT,
  city      TEXT,
  email     TEXT
);
```

### Table `purchases`
```sql
CREATE TABLE IF NOT EXISTS purchases (
  id          TEXT    PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  product_id  INTEGER NOT NULL,
  quantity    INT     NOT NULL CHECK (quantity > 0),
  price       REAL    NOT NULL CHECK (price >= 0),
  currency    TEXT    NOT NULL,
  date        TEXT    NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
```

Constraints:
- `quantity > 0`, `price >= 0`
- `customer_id` must exist in `customers`.

## 5) HTTP API Endpoints

### 5.1 `POST /api/import_csv`
Summary: Imports customers and purchases from two CSV files and performs upsert into the database.

Body (JSON):
```json
{
  "customers": "/opt/custexport/customers.csv",
  "purchases": "/opt/custexport/purchases.csv"
}
```
> The paths must be accessible from the process (mount the containing folder in Docker).

Responses:
```json
{ "status": 0, "n_customers": 6, "n_purchases": 8 }
```
- `404 Not Found`: file missing
- `400 Bad Request`: CSV parsing or validation error

Example (curl):
```bash
curl --location 'http://localhost:8080/api/import_csv'   --header 'Content-Type: application/json'   --data '{"customers":"/opt/custexport/customers.csv","purchases":"/opt/custexport/purchases.csv"}'
```

### 5.2 `POST /api/export_customers`
Summary: Loads all customers with their purchases and POSTs the aggregated JSON to a target URL.

Body (JSON):
```json
{
  "target_url": "http://127.0.0.1:8000/api/receive_export",
  "timeout": 15.0
}
```
- `target_url`: remote HTTP(S) endpoint to post to
- `timeout` (optional): request timeout in seconds

Responses:
- `200 OK`
```json
{
  "status": 0,
  "customers": <num_customers>,
  "purchases": <total_purchases>,
  "target_status": 200
}
```
- `500 Internal Server Error`: missing/corrupted database or SQLite error
- `502 Bad Gateway`: HTTP error (connection/timeout) or non-2xx response from target

Example (curl):
```bash
curl --location 'http://localhost:8080/api/export_customers'   --header 'Content-Type: application/json'   --data '{"target_url":"http://127.0.0.1:8000/api/receive_export","timeout":15}'
```

### 5.3 `POST /api/receive_export`
Summary: Demo endpoint that displays the posted content (JSON or text) as HTML.

- Body: any payload (preferably JSON)
- Response: HTML page (`text/html`) showing the escaped payload

Example: after export, open the target URL in your browser to view the displayed content.

## 6) Validations and Behavior
- Pydantic: optional fields for customers are converted to `None` when empty (`""`); `purchase_id` supports alias `purchase_identifier`.
- SQLite: `PRAGMA foreign_keys = ON`; simple constraints on `quantity` and `price`.
- Error handling:
  - Import: `404` for invalid path; `400` for parse/validation errors.
  - Export: `500` for missing DB/SQLite errors; `502` for HTTP/timeout/non-2xx responses.
- Performance: uses SQL `INSERT ... ON CONFLICT(id) DO UPDATE SET ...` for row-level upsert. Fine for small/medium datasets.

## 7) Security and Deployment Considerations
- Test endpoint exposure: `/api/receive_export` is a demo page; do not expose it in production.
- CSV path injection risk: restrict allowed paths and mount CSV directories as read-only.
- SQLite persistence: database stored in `/app/db/db.sqlite3`; use a volume to persist between container runs.
- Timeouts: configurable via `timeout` in export requests.

## 8) Quick Test Recipes

1) Import using the example CSVs mounted under `/opt/custexport`:
```bash
curl -sS 'http://localhost:8080/api/import_csv' -H 'Content-Type: application/json'   --data '{"customers":"/opt/custexport/customers.csv","purchases":"/opt/custexport/purchases.csv"}' | jq .
```

2) Export to the built-in receiver:
```bash
curl -sS 'http://localhost:8080/api/export_customers' -H 'Content-Type: application/json'   --data '{"target_url":"http://127.0.0.1:8000/api/receive_export","timeout":15}' | jq .
```

3) View the payload visually: open `http://localhost:8080/api/receive_export` (or whatever URL you used as target).

## 9) Troubleshooting

- 404 on import: incorrect CSV path (inside container). Mount volume properly and use container path (e.g., `/opt/custexport/...`).
- 500 on export: SQLite database missing or corrupted. Run import first or check file permissions.
- 502 on export: target unreachable or returned non-2xx status.

## 10) File Structure
```
web_import_export/
  app/
    main.py
    impl/
      import_csv.py
      export_customers.py
      receive_export.py
      customer.py
      purchase.py
      customer_db.py
      purchase_db.py
  data/
    customers.csv
    purchases.csv
  Dockerfile
  .dockerignore
  .gitignore
  commands/commands.txt
```