# REAL TRADER — Trading Journal

A Flask-based personal trading journal. It records trades and displays simple performance summaries. It does **not** connect to brokers, place orders, generate trading signals, or provide investment advice.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create and activate a virtual environment:
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install packages: `pip install -r requirements.txt`
5. Start: `python app.py`
6. Visit `http://127.0.0.1:5000`.

## Deploy

This project includes a `Procfile` for hosts that support Gunicorn. Configure:
- `SECRET_KEY`: a long, random secret value (required for production).
- `DATABASE_PATH`: path to persistent SQLite storage if your host supports persistent disks.
- `COOKIE_SECURE=1` when served over HTTPS.

SQLite data may be lost on hosts with ephemeral filesystems. Configure persistent storage and backups before relying on the journal. Review security, privacy, and hosting settings before inviting users.

## Project layout

- `app.py` — Flask routes and database
- `templates/` — Jinja HTML templates
- `static/style.css` — styling
- `requirements.txt` — Python dependencies
- `Procfile` — production start command
