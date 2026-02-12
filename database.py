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
    """
    Add a transaction to the database.
    TODO: Insert row into finance table
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO finance (name, date, amount, ttype, category, description)
        VALUES (?,?, ?, ?, ?, ?)
    """, (name, date, amount, ttype, category, description))
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