# database.py
import csv
import sqlite3
from turtle import st
from flask import g, render_template
import torch
from datetime import datetime

DB_NAME = "finance.db"
valid_categories = [" fast food", "rent", "salary", "entertainment", "transportation", "healthcare", "zelle", "technology", "car bills", "Utilities bills", "other", "miscellaneous", "groceries", "subscriptions", "insurance", "education", "travel", "gifts", "donations", "personal care", "clothing", "savings", "investments"]

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

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
def categorize_transaction(description):
    desc = description.lower().strip()
    rules = {
        "groceries": ["walmart","target","costco","kroger","safeway","trader joe","whole foods","foodmaxx"],
        "gas": ["shell","chevron","exxon","76","arco","valero","gas"],
        "food": ["mcdonald","starbucks","chipotle","doordash","ubereats","grubhub","restaurant","cafe","pizza"],
        "shopping": ["amazon","ebay","best buy","walmart online","target online","nike","apple","store"],
        "transport": ["uber","lyft","bus","train","bart","metro"],
        "income": ["deposit","payroll","salary","paycheck","zelle","venmo","refund","bonus"]
    }
    for category, keywords in rules.items():
        for word in keywords:
            if word in desc:
                return category
    
    scores = {key:0 for key in rules.keys()}
    words = desc.split()
    for w in words:
        for category, keywords in rules.items():
            for k in keywords:
                if w in k or k in w:
                    scores[category] += 1
    best_category = max(scores, key=scores.get)
    if scores[best_category] > 0:
        return best_category
    return "other"

def add_transaction(name, date, amount, ttype, category, description=""):
    converted_date = split_date(date)
    if not converted_date:
        print("Skipping invalid date:", date)       
        return
    category = category.strip().lower()
    if category not in valid_categories:
        if(description):
            category = categorize_transaction(description)
        else:
            category = "other"

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

    start_range = end_range = None
    if timeRange:
        try:
            start_range, end_range = [x.strip() for x in timeRange.split("to")]
        except ValueError:
            start_range = end_range = None

    base_query = "FROM finance WHERE 1=1"
    params = []

    if start_range and end_range:
        base_query += " AND date BETWEEN ? AND ?"
        params.extend([start_range, end_range])

    if metric in ["income", "expense"]:
        base_query += " AND ttype=?"
        params = [metric] + params

        if timeframe == "Monthly":
            query = "SELECT strftime('%Y-%m', date), SUM(amount) " + base_query + " GROUP BY 1 ORDER BY 1"
        elif timeframe == "Yearly":
            query = "SELECT strftime('%Y', date), SUM(amount) " + base_query + " GROUP BY 1 ORDER BY 1"
        elif timeframe == "Quarterly":
            query = "SELECT strftime('%Y', date)||'-Q'||((CAST(strftime('%m',date) AS INTEGER)-1)/3+1), SUM(amount) " + base_query + " GROUP BY 1 ORDER BY 1"
        else:
            conn.close()
            return []

        cursor.execute(query, params)

    elif metric in ["earn_rate", "spend_rate"]:
        factor = 1 if metric == "spend_rate" else 0

        if timeframe == "Monthly":
            query = f"""
            SELECT strftime('%Y-%m', date),
            SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) +
            SUM(CASE WHEN ttype='expense' THEN amount ELSE 0 END)*{factor}
            {base_query}
            GROUP BY 1 ORDER BY 1
            """
        elif timeframe == "Yearly":
            query = f"""
            SELECT strftime('%Y', date),
            SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) +
            SUM(CASE WHEN ttype='expense' THEN amount ELSE 0 END)*{factor}
            {base_query}
            GROUP BY 1 ORDER BY 1
            """
        elif timeframe == "Quarterly":
            query = f"""
            SELECT strftime('%Y', date)||'-Q'||((CAST(strftime('%m',date) AS INTEGER)-1)/3+1),
            SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END) +
            SUM(CASE WHEN ttype='expense' THEN amount ELSE 0 END)*{factor}
            {base_query}
            GROUP BY 1 ORDER BY 1
            """
        else:
            conn.close()
            return []

        cursor.execute(query, params)

    else:
        conn.close()
        return []

    rows = cursor.fetchall()
    conn.close()
    return rows
def get_insights():
    conn = get_connection()
    cursor = conn.cursor()

    insights = []


    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount)
        FROM finance
        WHERE ttype='expense'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 2
    """)
    rows = cursor.fetchall() 
    #omapre the last two months & then we print into insights and if - or pos different message 
    if len(rows) == 2:
        current, previous = rows[0][1], rows[1][1]
        if previous > 0:
            change = ((current - previous) / previous) * 100
            if change > 0:
                insights.append(f"Spending increased by {change:.1f}% compared to last month")
            else:
                insights.append(f"Spending decreased by {abs(change):.1f}% compared to last month")

  
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM finance
        WHERE ttype='expense'
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        insights.append(f"Top spending category: {row[0]}")

    
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount)
        FROM finance
        WHERE ttype='income'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 2
    """)
    rows = cursor.fetchall()

    if len(rows) == 2:
        current, previous = rows[0][1], rows[1][1]
        if current > previous:
            insights.append("Your income is increasing")
        elif current < previous:
            insights.append("Your income decreased recently")

    conn.close()
    return insights
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

    valid_sort = {"date", "amount", "id"}
    if sort_by not in valid_sort:
        sort_by = "date"
    query = f"""
    SELECT id, name, date, amount, ttype, category, description FROM finance WHERE ttype=? ORDER BY {sort_by} DESC """
    cursor.execute(query, (ttype,))
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
