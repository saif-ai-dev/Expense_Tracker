# 💰 Expense Tracker

A modern, secure and feature-rich personal Expense Tracker web application — built with Flask and SQLite, with a clean indigo-violet design and dark mode support.

## 🛠 Built With

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript
- **Charts:** Chart.js
- **Alerts:** SweetAlert2
- **Security:** Werkzeug password hashing, Flask sessions

## ✨ Features

### Core
- 🔐 Secure user registration & login (hashed passwords, session-based auth)
- 📊 Dashboard with live income, expense and balance summary
- 💰 Add income with source and date
- 💸 Add expense with category, description and date
- 📜 Transaction history — search, filter by type, edit and delete any entry
- 📈 Reports page — category breakdown (doughnut chart) and income vs expense (bar chart)

### Extra
- 🎯 **Monthly Budgets** — set a spending limit per category, track progress with a live progress bar, get warned when you go over
- 📅 **Date tracking** on every transaction
- 📥 **CSV Export** — download your full transaction history as a spreadsheet-ready file
- 🌙 **Dark Mode** — toggle with one click, preference remembered across visits
- 👤 **Profile management** — update your name, email, and change your password securely

### Design
- Fully responsive, mobile-friendly layout
- Consistent indigo-violet theme across every page
- Smooth hover animations and transitions
- Colour-coded income (green) vs expense (red) throughout

## 🚀 Getting Started

### 1. Clone or download the project

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux