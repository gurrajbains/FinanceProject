# database.py
import csv
import sqlite3
from flask import g, render_template


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
    cursor.execute("SELECT name, date, amount, ttype, category, description FROM finance;")
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



def get_summary(): 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ttype, SUM (amount) FROM finance GROUP BY ttype;")
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
        columns = ['Name', 'Date', 'Amount', 'Type', 'Category', 'Description'] # define ccollumns  fo rthe csv files
        writer = csv.writer(csvfile)#writer will be write into csv file
        writer.writerow(columns) # write the header rows 
        for row in rows: #go through every single row in rows and put the values intoo the corresponding header 
            writer.writerow(row)


def search_transactions(q, ttype):
    conn = get_connection()
    cursor = conn.cursor()
    if ttype == "all":
        cursor.execute("""
            SELECT name, date, amount, ttype, category, description 
            FROM finance 
            WHERE name LIKE ? OR category LIKE ? OR description LIKE ?
            ORDER BY date DESC, id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cursor.execute("""
            SELECT name, date, amount, ttype, category, description 
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
        cursor.execute("SELECT name, date, amount, ttype, category, description FROM finance WHERE ttype=? ORDER BY date DESC", (ttype,))
    elif sort_by == "amount":
        cursor.execute("SELECT name, date, amount, ttype, category, description FROM finance WHERE ttype=? ORDER BY amount DESC", (ttype,))
    else:
        cursor.execute("SELECT name, date, amount, ttype, category, description FROM finance WHERE ttype=? ORDER BY id DESC", (ttype,))
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