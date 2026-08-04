from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "expense_tracker_secret"

def create_database():
    conn = sqlite3.connect("Expense_Tracker.db")
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

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("Expense_Tracker.db")
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    total_income = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
    total_expense = cursor.fetchone()[0]

    conn.close()

    if total_income is None:
        total_income = 0

    if total_expense is None:
        total_expense = 0

    balance = total_income - total_expense

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )

@app.route("/add_income", methods=["GET", "POST"])
def add_income():

    if request.method == "POST":
        source = request.form["source"]
        amount = request.form["amount"]

        conn = sqlite3.connect("Expense_Tracker.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
        """, (1, "Income", amount, source, source))

        conn.commit()
        conn.close()

        flash("Income Added Successfully!")
        return redirect(url_for("dashboard"))

    return render_template("add_income.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("Expense_Tracker.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            flash("Login Successful!")
            return redirect(url_for("dashboard"))

        else:
            flash("Invalid Email or Password!")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("Expense_Tracker.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

if __name__ == "__main__":
    create_database()
    app.run(debug=True)