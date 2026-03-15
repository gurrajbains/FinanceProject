# database.py
import csv
import sqlite3
from turtle import st
from flask import g, render_template
import torch
from datetime import datetime

DB_NAME = "finance.db"


def get_connection():

   
   return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance (
            name TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            ttype TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    print("Database initialized successfully.")
    conn.close()


def return_HTML_table(rows):
    """
    Return DATA to html   """
    rows = get_all_transactions()
    return render_template("index.html", rows=rows)


def add_transaction(name, date, amount, ttype, category, description=""):
    converted_date = split_date(date)


    if not converted_date:
        print("Skipping invalid date:", date)
        return

    if ttype == "expense" and amount > 0:
        amount = -amount

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO finance (name, date, amount, ttype, category, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, converted_date, amount, ttype, category, description))
    conn.commit()
    conn.close()

def get_all_transactions():
    """
    Return all transactions.
    TODO: Query finance table
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, date, amount, ttype, category, description FROM finance;")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_transaction(transaction_id):
    conn= get_connection()
    cursor = conn.cursor()
    cursor.execute(" DELETE FROM finance WHERE id = ?", (transaction_id,))
    conn.commit()
   
    cursor.rowcount

    rowcount = cursor.rowcount
    conn.close()
    return rowcount
def delete_all_transactions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM finance;")
   
    conn.commit()
   
    deleted = cursor.rowcount
    conn.close()
    return deleted


def make_training_tensors():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount FROM finance ORDER BY date;")
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 8:
        return None, None

    X = []
    y = []

    amounts = [float(row[1]) for row in rows]

    for i in range(3, len(rows) - 1):
        date_str = rows[i][0]
        dt = datetime.strptime(date_str, "%Y-%m-%d")

        month = dt.month / 12.0
        day = dt.day / 31.0
        day_of_week = dt.weekday() / 6.0

        current_amount = float(rows[i][1]) / 3000.0
        previous_amount = float(rows[i - 1][1]) / 3000.0

        avg_last_3 = (
            amounts[i - 1] + amounts[i - 2] + amounts[i - 3]
        ) / 3.0 / 3000.0

        next_amount = float(rows[i + 1][1]) / 3000.0

        X.append([
            month,
            day,
            day_of_week,
            current_amount,
            previous_amount,
            avg_last_3
        ])
        y.append([next_amount])

    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.float32)

    return X, y
def get_summary(metric, timeframe, timeRange=None):
    conn = get_connection()
    cursor = conn.cursor()

    # Parse timeRange
    start_range = end_range = None
    if timeRange:
        try:
            start_range, end_range = [x.strip() for x in timeRange.split("to")]
        except ValueError:
            start_range = end_range = None

    # Helper for time range
    range_clause = ""
    params = []
    if start_range and end_range:
        range_clause = "AND date BETWEEN ? AND ?"
        params = [start_range + "-01", end_range + "-31"]

    if metric in ["income", "expense"]:
        ttype = metric
        if timeframe == "Monthly":
            cursor.execute(f"SELECT strftime('%Y-%m', date) AS period, SUM(amount) FROM finance WHERE ttype=? {range_clause} GROUP BY period ORDER BY period;", [ttype] + params)
        elif timeframe == "Yearly":
            cursor.execute(f"SELECT strftime('%Y', date) AS period, SUM(amount) FROM finance WHERE ttype=? {range_clause} GROUP BY period ORDER BY period;", [ttype] + params)
        elif timeframe == "Quarterly":
            cursor.execute(f"SELECT strftime('%Y', date) || '-Q' || ((CAST(strftime('%m', date) AS INTEGER)-1)/3 +1) AS period, SUM(amount) FROM finance WHERE ttype=? {range_clause} GROUP BY period ORDER BY period;", [ttype] + params)

    elif metric in ["earn_rate", "spend_rate"]:
        factor = 1 if metric == "spend_rate" else 0
        if timeframe == "Monthly":
            cursor.execute(f"SELECT strftime('%Y-%m', date) AS period, SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) + SUM(CASE WHEN ttype='expense' THEN amount ELSE 0 END)*{factor} FROM finance WHERE 1=1 {range_clause} GROUP BY period ORDER BY period;", params)
        elif timeframe == "Yearly":
            cursor.execute(f"SELECT strftime('%Y', date) AS period, SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) + SUM(CASE WHEN ttype='expense' THEN amount ELSE 0 END)*{factor} FROM finance WHERE 1=1 {range_clause} GROUP BY period ORDER BY period;", params)
        elif timeframe == "Quarterly":
            cursor.execute(f"SELECT strftime('%Y', date) || '-Q' || ((CAST(strftime('%m', date) AS INTEGER)-1)/3 +1) AS period, SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) + SUM(CASE WHEN ttype='expense' THEN amount ELSE 0 END)*{factor} FROM finance WHERE 1=1 {range_clause} GROUP BY period ORDER BY period;", params)

    else:
        conn.close()
        return []

    summary = cursor.fetchall()
    conn.close()
    return summary
def get_transactions_by_type(ttype):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, date, amount, ttype, category, description FROM finance WHERE ttype=? ORDER by date DESC, id DESC", (ttype,))
    rows = cursor.fetchall()
    conn.close()
    return rows
def export_to_csv(rows):
    #Need to clean up data , need to clean up ui, need to clean up how data is being dsipalted on the CLI, add abiility to give percentages based on income etc; tax rates ; etc ; total percentage of money used; revenue across a few months etc;
    """
    Export all transactions to a CSV file.
    """
    with open('finance.csv', 'w', newline='') as csvfile:  #open file in write mode 
        columns = ['ID','Name', 'Date', 'Amount', 'Type', 'Category', 'Description'] # define ccollumns  fo rthe csv files
        writer = csv.writer(csvfile)#writer will be write into csv file
        writer.writerow(columns) # write the header rows 
        for row in rows: #go through every single row in rows and put the values intoo the corresponding header 
            writer.writerow(row)


def search_transactions(q, ttype):
    conn = get_connection()
    cursor = conn.cursor()
    if ttype == "all":
        cursor.execute("""
            SELECT  id, name, date, amount, ttype, category, description 
            FROM finance 
            WHERE name LIKE ? OR category LIKE ? OR description LIKE ?
            ORDER BY date DESC, id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cursor.execute("""
            SELECT id, name, date, amount, ttype, category, description 
            FROM finance 
            WHERE (name LIKE ? OR category LIKE ? OR description LIKE ?) AND ttype=?
            ORDER BY date DESC, id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%", ttype))
    rows = cursor.fetchall()
    conn.close()
    return rows

def sort_transactions(sort_by, ttype):
    conn = get_connection() 
    cursor = conn.cursor()

    if sort_by == "date":
        cursor.execute("SELECT id, name, date, amount, ttype, category, description FROM finance WHERE ttype=? ORDER BY date DESC", (ttype,))
    elif sort_by == "amount":
        cursor.execute("SELECT id, name, date, amount, ttype, category, description FROM finance WHERE ttype=? ORDER BY amount DESC", (ttype,))
    else:
        cursor.execute("SELECT id, name, date, amount, ttype, category, description FROM finance WHERE ttype=? ORDER BY id DESC", (ttype,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def return_by_month():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ttype, SUM (amount), date FROM finance GROUP BY date;")  # rows will look like (Ttype SUM(amount) date) want to update with new date
    rows = cursor.fetchall()
    conn.close()
    return rows # ret


def split_date(date_str):
    if not date_str:
        return None

    date_str = date_str.strip()

    formats = [
        "%Y-%m-%d",  "%m/%d/%Y",  "%m/%d/%y",   "%m-%d-%Y",    "%m-%d-%y",  "%Y/%m/%d",  "%Y.%m.%d",   "%d-%m-%Y",    "%d/%m/%Y",    "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    print("Bad date format:", date_str)
    return None

def get_new_Graphic_data(timeFrame, data):
    conn = get_connection()
    cursor = conn.cursor()
    if timeFrame == "Monthly":
        cursor.execute("SELECT ttype, SUM (amount), date FROM finance GROUP BY strftime('%Y-%m', date);")
    elif timeFrame == "Quarterly":
        cursor.execute("SELECT ttype, SUM (amount), date FROM finance GROUP BY strftime('%Y-Q%q', date);")
    elif timeFrame == "Yearly":
        cursor.execute("SELECT ttype, SUM (amount), date FROM finance GROUP BY strftime('%Y', date);")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_versus_data(data):
    if data == "earn rate":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT date, SUM(amount) FROM finance WHERE ttype='income' GROUP BY strftime('%Y-%m', date);")
        rows = cursor.fetchall()
        conn.close()
    elif data == "spend_rate":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT date, SUM(amount) FROM finance WHERE ttype='expense' GROUP BY strftime('%Y-%m', date);")
        rows = cursor.fetchall()
        conn.close()
        return rows
def delete_transaction(transaction_id):
    conn= get_connection()
    cursor = conn.cursor()
    cursor.execute(" DELETE FROM finance WHERE id = ?", (transaction_id,))
    conn.commit()
    cursor.rowcount
    rowcount = cursor.rowcount
    conn.close()
    return rowcount
