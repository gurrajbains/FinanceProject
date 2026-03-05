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
    if(ttype == "expense" and amount > 0):
        amount = -amount
    """

    Add a transaction to the database.
    TODO: Insert row into finance table
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO finance (name, date, amount, ttype, category, description)
        VALUES (?,?, ?, ?, ?, ?)
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

def make_training_tensors(limit=None):
    conn = get_connection()
    cur = conn.cursor()

    q = "SELECT date, amount, ttype, category, IFNULL(description,'') FROM finance"
    if limit:
        q += " LIMIT ?"
        cur.execute(q, (limit,))
    else:
        cur.execute(q)

    rows = cur.fetchall()
    conn.close()

    X_list = []
    y_list = []

    for date_str, amount, ttype, category, desc in rows:
        # date is stored as "YYYY-MM-DD" in your db
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month = dt.month / 12.0
        day = dt.day / 31.0
        year = (dt.year - 2000) / 50.0  # rough scaling for 2000-2050

        ttype_num = 1.0 if ttype == "income" else 0.0

        # simple stable numeric encoding for category
        cat_num = (abs(hash(category)) % 1000) / 1000.0

        desc_len = min(len(desc), 120) / 120.0

        features = [month, day, year, ttype_num, cat_num, desc_len]
        X_list.append(features)
        y_list.append([float(amount)])

    X = torch.tensor(X_list, dtype=torch.float32)
    y = torch.tensor(y_list, dtype=torch.float32)
    return X, y

def get_summary(metric, timeframe, timeRange=None):
    conn = get_connection()
    cursor = conn.cursor()
    timeRange = timeRange.strip() if timeRange else None

    if metric == "spend_rate":
        if timeframe == "Monthly":
            cursor.execute("SELECT strftime('%Y-%m', date), SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) - SUM(CASE WHEN ttype='expense' THEN -amount ELSE 0 END) FROM finance GROUP BY strftime('%Y-%m', date) ORDER BY strftime('%Y-%m', date);")
        elif timeframe == "Yearly":
            cursor.execute("SELECT strftime('%Y', date), SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) - SUM(CASE WHEN ttype='expense' THEN -amount ELSE 0 END) FROM finance GROUP BY strftime('%Y', date) ORDER BY strftime('%Y', date);")
        elif timeframe == "Quarterly":
            cursor.execute("SELECT strftime('%Y', date) || '-Q' || ((CAST(strftime('%m', date) AS INTEGER) - 1) / 3 + 1), SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) - SUM(CASE WHEN ttype='expense' THEN -amount ELSE 0 END) FROM finance GROUP BY strftime('%Y', date) || '-Q' || ((CAST(strftime('%m', date) AS INTEGER) - 1) / 3 + 1) ORDER BY strftime('%Y', date), ((CAST(strftime('%m', date) AS INTEGER) - 1) / 3 + 1);")

    elif metric == "earn_rate":
        if timeframe == "Monthly":
            cursor.execute("SELECT strftime('%Y-%m', date), SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) FROM finance GROUP BY strftime('%Y-%m', date) ORDER BY strftime('%Y-%m', date);")
        elif timeframe == "Yearly":
            cursor.execute("SELECT strftime('%Y', date), SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) FROM finance GROUP BY strftime('%Y', date) ORDER BY strftime('%Y', date);")
        elif timeframe == "Quarterly":
            cursor.execute("SELECT strftime('%Y', date) || '-Q' || ((CAST(strftime('%m', date) AS INTEGER) - 1) / 3 + 1), SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) FROM finance GROUP BY strftime('%Y', date) || '-Q' || ((CAST(strftime('%m', date) AS INTEGER) - 1) / 3 + 1) ORDER BY strftime('%Y', date), ((CAST(strftime('%m', date) AS INTEGER) - 1) / 3 + 1);")
    if metric == "income":
        if timeframe == "Monthly":
            cursor.execute("""
                SELECT strftime('%Y-%m', date), SUM(amount) FROM finance WHERE ttype='income' GROUP BY strftime('%Y-%m', date)ORDER BY strftime('%Y-%m', date); """)
        elif timeframe == "Yearly":
            cursor.execute("""
                SELECT strftime('%Y', date), SUM(amount)FROM finance WHERE ttype='income'GROUP BY strftime('%Y', date) ORDER BY strftime('%Y', date);""")

        elif timeframe == "Quarterly": cursor.execute("SELECT strftime('%Y', date) || '-Q' || ((cast(strftime('%m', date) as integer) - 1) / 3 + 1) AS year_quarter, SUM(amount) AS total FROM finance WHERE ttype = 'income' GROUP BY year_quarter ORDER BY year_quarter;")
    if metric == "expense":
        if timeframe == "Monthly":
            cursor.execute("""
                SELECT strftime('%Y-%m', date), SUM(amount) FROM finance WHERE ttype='expense' GROUP BY strftime('%Y-%m', date)ORDER BY strftime('%Y-%m', date); """)
        elif timeframe == "Yearly":
            cursor.execute(""" SELECT strftime('%Y', date), SUM(amount)FROM finance WHERE ttype='expense'GROUP BY strftime('%Y', date) ORDER BY strftime('%Y', date);""")

        elif timeframe == "Quarterly": cursor.execute("SELECT strftime('%Y', date) || '-Q' || ((cast(strftime('%m', date) as integer) - 1) / 3 + 1) AS year_quarter, SUM(amount) AS total FROM finance WHERE ttype = 'expense' GROUP BY year_quarter ORDER BY year_quarter;")

    summary = cursor.fetchall()
    for rows in summary[:]:  # Create a copy of the list to avoid modifying it during iteration
        if timeRange:
                    start, end = timeRange.split("to")
                    start = start.strip()
                    end = end.strip()
                    if rows[0] < start or rows[0] > end:
                        summary.remove(rows)
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
        columns = ['ID''Name', 'Date', 'Amount', 'Type', 'Category', 'Description'] # define ccollumns  fo rthe csv files
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
    # ate_str is in the format "mm-DD-yyyy"
    
    parts = date_str.split("-") # take a data string and everytime a dash is seen we split it
    if len(parts) == 3:# for thee parts we have month day and year
        month, day, year= parts #In ordder of partitioning  we assign parts to mdy
        return  f"{year}-{month}-{day}" #return month day and year as separate values
    
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
def delet_transaction(transaction_id):
    conn= get_connection()
    cursor = conn.cursor()
    cursor.execute(" DELETE FROM finance WHERE id = ?", (transaction_id,))
    conn.commit()
    cursor.rowcount
    rowcount = cursor.rowcount
    conn.close()
    return rowcount
