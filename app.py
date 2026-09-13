from functools import wraps
from datetime import date
import csv
import io

from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "expense_tracker_secret"

DB_NAME = "Expense_Tracker.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Migration: add a "date" column for existing databases created before
    # this feature existed. Safe to run every startup — SQLite raises
    # OperationalError if the column is already there, which we ignore.
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN date TEXT")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, category)
        )
    """)

    conn.commit()
    conn.close()


def get_budget_status(user_id):
    """Returns each budget the user has set, along with how much they've
    spent in that category so far this calendar month."""
    conn = get_db()
    cursor = conn.cursor()

    current_month = date.today().strftime("%Y-%m")

    cursor.execute(
        "SELECT id, category, monthly_limit FROM budgets WHERE user_id=? ORDER BY category",
        (user_id,)
    )
    budget_rows = cursor.fetchall()

    status = []
    for b in budget_rows:
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE user_id=? AND type='Expense' AND category=? AND date LIKE ?
        """, (user_id, b["category"], current_month + "%"))
        spent = cursor.fetchone()[0]

        limit_ = b["monthly_limit"]
        percent = min(100, round((spent / limit_) * 100)) if limit_ > 0 else 0

        status.append({
            "id": b["id"],
            "category": b["category"],
            "limit": limit_,
            "spent": spent,
            "percent": percent,
            "over": spent > limit_
        })

    conn.close()
    return status


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    return {"current_user_name": session.get("user_name")}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/learn_more")
def learn_more():
    return render_template("learn_more.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='Income' AND user_id=?", (user_id,))
    total_income = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='Expense' AND user_id=?", (user_id,))
    total_expense = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, type, amount, category, description, date
        FROM transactions
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 5
    """, (user_id,))
    recent = cursor.fetchall()

    conn.close()

    balance = total_income - total_expense
    budget_status = get_budget_status(user_id)

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        recent=recent,
        budget_status=budget_status
    )


@app.route("/reports")
@login_required
def reports():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='Income' AND user_id=?", (user_id,))
    total_income = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='Expense' AND user_id=?", (user_id,))
    total_expense = cursor.fetchone()[0]

    balance = total_income - total_expense

    cursor.execute("""
        SELECT category, COALESCE(SUM(amount),0)
        FROM transactions
        WHERE type='Expense' AND user_id=?
        GROUP BY category
    """, (user_id,))
    category_expenses = cursor.fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        category_expenses=category_expenses
    )


@app.route("/add_income", methods=["GET", "POST"])
@login_required
def add_income():
    if request.method == "POST":
        source = request.form.get("source", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        entry_date = request.form.get("date", "").strip() or date.today().isoformat()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid positive amount.")
            return redirect(url_for("add_income"))

        if not source:
            flash("Please enter a source.")
            return redirect(url_for("add_income"))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session["user_id"], "Income", amount, source, source, entry_date))
        conn.commit()
        conn.close()

        flash("Income added successfully!")
        return redirect(url_for("dashboard"))

    return render_template("add_income.html", today=date.today().isoformat())


@app.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        entry_date = request.form.get("date", "").strip() or date.today().isoformat()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid positive amount.")
            return redirect(url_for("add_expense"))

        if not category:
            flash("Please enter a category.")
            return redirect(url_for("add_expense"))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session["user_id"], "Expense", amount, category, description, entry_date))
        conn.commit()

        # If this category has a monthly budget, check whether this entry
        # (dated in the current month) pushed spending over the limit.
        warning = ""
        current_month = date.today().strftime("%Y-%m")
        if entry_date.startswith(current_month):
            budget_row = cursor.execute(
                "SELECT monthly_limit FROM budgets WHERE user_id=? AND category=?",
                (session["user_id"], category)
            ).fetchone()
            if budget_row:
                spent = cursor.execute("""
                    SELECT COALESCE(SUM(amount),0) FROM transactions
                    WHERE user_id=? AND type='Expense' AND category=? AND date LIKE ?
                """, (session["user_id"], category, current_month + "%")).fetchone()[0]
                if spent > budget_row["monthly_limit"]:
                    warning = f" ⚠️ You've gone over your {category} budget (₹{spent:.0f} / ₹{budget_row['monthly_limit']:.0f})."

        conn.close()

        flash("Expense added successfully!" + warning)
        return redirect(url_for("dashboard"))

    return render_template("add_expense.html", today=date.today().isoformat())


@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    user_id = session["user_id"]

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        limit_raw = request.form.get("monthly_limit", "").strip()

        try:
            monthly_limit = float(limit_raw)
            if monthly_limit <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid positive budget amount.")
            return redirect(url_for("budgets"))

        if not category:
            flash("Please enter a category.")
            return redirect(url_for("budgets"))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO budgets (user_id, category, monthly_limit)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, category) DO UPDATE SET monthly_limit=excluded.monthly_limit
        """, (user_id, category, monthly_limit))
        conn.commit()
        conn.close()

        flash(f"Budget for {category} set to ₹{monthly_limit:.0f}/month.")
        return redirect(url_for("budgets"))

    return render_template("budgets.html", budget_status=get_budget_status(user_id))


@app.route("/delete_budget/<int:budget_id>")
@login_required
def delete_budget(budget_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM budgets WHERE id=? AND user_id=?",
        (budget_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    flash("Budget removed.")
    return redirect(url_for("budgets"))

@app.route("/export_csv")
@login_required
def export_csv():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, type, category, description, amount
        FROM transactions
        WHERE user_id=?
        ORDER BY date DESC, id DESC
    """, (session["user_id"],))
    rows = cursor.fetchall()
    conn.close()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Type", "Category", "Description", "Amount"])
    for r in rows:
        writer.writerow([r["date"] or "", r["type"], r["category"], r["description"] or "", r["amount"]])

    filename = f"expense_tracker_history_{date.today().isoformat()}.csv"

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/transaction_history")
@login_required
def transaction_history():
    search = request.args.get("search", "")
    transaction_type = request.args.get("type", "all")

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, type, amount, category, description, date FROM transactions WHERE user_id=?"
    params = [session["user_id"]]

    if search:
        query += " AND (category LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if transaction_type != "all":
        query += " AND type = ?"
        params.append(transaction_type)

    query += " ORDER BY date DESC, id DESC"

    cursor.execute(query, params)
    transactions = cursor.fetchall()
    conn.close()

    return render_template(
        "transaction_history.html",
        transactions=transactions
    )


@app.route("/edit_transaction/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, type, amount, category, description, date FROM transactions WHERE id=? AND user_id=?",
        (transaction_id, session["user_id"])
    )
    transaction = cursor.fetchone()

    if transaction is None:
        conn.close()
        flash("Transaction not found.")
        return redirect(url_for("transaction_history"))

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        entry_date = request.form.get("date", "").strip() or date.today().isoformat()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid positive amount.")
            conn.close()
            return redirect(url_for("edit_transaction", transaction_id=transaction_id))

        cursor.execute("""
            UPDATE transactions
            SET category=?, amount=?, description=?, date=?
            WHERE id=? AND user_id=?
        """, (category, amount, description, entry_date, transaction_id, session["user_id"]))
        conn.commit()
        conn.close()

        flash("Transaction updated successfully!")
        return redirect(url_for("transaction_history"))

    conn.close()
    return render_template("edit_transaction.html", transaction=transaction)


@app.route("/delete_transaction/<int:transaction_id>")
@login_required
def delete_transaction(transaction_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM transactions WHERE id=? AND user_id=?",
        (transaction_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    flash("Transaction deleted.")
    return redirect(url_for("transaction_history"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Login successful!")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("register"))

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.")
            conn.close()
            return redirect(url_for("register"))

        conn.close()

        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]

    if request.method == "POST":
        form_type = request.form.get("form_type")
        conn = get_db()
        cursor = conn.cursor()

        if form_type == "update_info":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()

            if not name or not email:
                flash("Name and email cannot be empty.")
                conn.close()
                return redirect(url_for("profile"))

            try:
                cursor.execute(
                    "UPDATE users SET name=?, email=? WHERE id=?",
                    (name, email, user_id)
                )
                conn.commit()
                session["user_name"] = name
                flash("Profile updated successfully!")
            except sqlite3.IntegrityError:
                flash("That email is already in use by another account.")

            conn.close()
            return redirect(url_for("profile"))

        elif form_type == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            user = cursor.execute(
                "SELECT password FROM users WHERE id=?", (user_id,)
            ).fetchone()

            if not user or not check_password_hash(user["password"], current_password):
                flash("Current password is incorrect.")
            elif len(new_password) < 6:
                flash("New password must be at least 6 characters.")
            elif new_password != confirm_password:
                flash("New passwords do not match.")
            else:
                cursor.execute(
                    "UPDATE users SET password=? WHERE id=?",
                    (generate_password_hash(new_password), user_id)
                )
                conn.commit()
                flash("Password changed successfully!")

            conn.close()
            return redirect(url_for("profile"))

        conn.close()
        return redirect(url_for("profile"))

    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email FROM users WHERE id=?", (user_id,)
    ).fetchone()
    conn.close()

    return render_template("profile.html", user=user)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))


if __name__ == "__main__":
    create_database()
    app.run(debug=True)