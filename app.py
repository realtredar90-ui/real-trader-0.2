import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-development-key-change-before-deploy")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"
DB_PATH = os.environ.get("DATABASE_PATH", "real_trader.db")


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trade_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL CHECK(side IN ('Buy', 'Sell')),
                setup TEXT DEFAULT '',
                entry REAL NOT NULL,
                exit_price REAL,
                stop_loss REAL,
                target REAL,
                quantity REAL NOT NULL,
                pnl REAL DEFAULT 0,
                fees REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("landing"))


@app.route("/landing")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 8:
            flash("Username must be at least 3 characters and password at least 8 characters.", "error")
        else:
            try:
                with get_db() as con:
                    con.execute(
                        "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                        (username, generate_password_hash(password))
                    )
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That username is already registered.", "error")
    return render_template("auth.html", mode="Register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as con:
            user = con.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("auth.html", mode="Login")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("landing"))


def user_trades():
    with get_db() as con:
        return con.execute(
            "SELECT * FROM trades WHERE user_id = ? ORDER BY trade_date DESC, id DESC",
            (session["user_id"],)
        ).fetchall()


def stats_for(trades):
    closed = [t for t in trades if t["exit_price"] is not None]
    net = sum((t["pnl"] or 0) - (t["fees"] or 0) for t in closed)
    wins = sum(1 for t in closed if (t["pnl"] or 0) - (t["fees"] or 0) > 0)
    losses = sum(1 for t in closed if (t["pnl"] or 0) - (t["fees"] or 0) < 0)
    win_rate = round(wins / len(closed) * 100, 1) if closed else 0
    return {"count": len(trades), "closed": len(closed), "net": round(net, 2),
            "wins": wins, "losses": losses, "win_rate": win_rate}


@app.route("/dashboard")
@login_required
def dashboard():
    trades = user_trades()
    return render_template("dashboard.html", trades=trades[:8], stats=stats_for(trades))


@app.route("/trades")
@login_required
def trades_page():
    return render_template("trades.html", trades=user_trades())


@app.route("/trades/new", methods=["GET", "POST"])
@login_required
def new_trade():
    if request.method == "POST":
        try:
            symbol = request.form.get("symbol", "").strip().upper()
            side = request.form.get("side", "")
            trade_date = request.form.get("trade_date", "")
            entry = float(request.form.get("entry", ""))
            exit_raw = request.form.get("exit_price", "").strip()
            exit_price = float(exit_raw) if exit_raw else None
            quantity = float(request.form.get("quantity", ""))
            stop_raw = request.form.get("stop_loss", "").strip()
            target_raw = request.form.get("target", "").strip()
            stop_loss = float(stop_raw) if stop_raw else None
            target = float(target_raw) if target_raw else None
            pnl = float(request.form.get("pnl", "0") or 0)
            fees = float(request.form.get("fees", "0") or 0)
            if not symbol or side not in ("Buy", "Sell") or not trade_date:
                raise ValueError
            if entry <= 0 or quantity <= 0 or fees < 0:
                raise ValueError
            with get_db() as con:
                con.execute("""
                    INSERT INTO trades
                    (user_id, trade_date, symbol, side, setup, entry, exit_price,
                     stop_loss, target, quantity, pnl, fees, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session["user_id"], trade_date, symbol, side,
                    request.form.get("setup", "").strip(), entry, exit_price,
                    stop_loss, target, quantity, pnl, fees,
                    request.form.get("notes", "").strip()
                ))
            flash("Trade saved successfully.", "success")
            return redirect(url_for("trades_page"))
        except (ValueError, TypeError):
            flash("Please enter valid trade details.", "error")
    return render_template("new_trade.html")


@app.route("/trades/<int:trade_id>/delete", methods=["POST"])
@login_required
def delete_trade(trade_id):
    with get_db() as con:
        con.execute("DELETE FROM trades WHERE id = ? AND user_id = ?",
                    (trade_id, session["user_id"]))
    flash("Trade deleted.", "success")
    return redirect(url_for("trades_page"))


@app.route("/reports")
@login_required
def reports():
    trades = user_trades()
    return render_template("reports.html", stats=stats_for(trades))


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
