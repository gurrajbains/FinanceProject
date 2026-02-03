# database.py
import sqlite3


DB_NAME = "finance.db"


def get_connection():

   
   return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
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


  


def add_transaction(name, date, amount, ttype, category, description=""):
    """
    Add a transaction to the database.
    TODO: Insert row into transactions table
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (name, date, amount, ttype, category, description)
        VALUES (?,?, ?, ?, ?, ?)
    """, (name, date, amount, ttype, category, description))
    conn.commit()
    conn.close()

def get_all_transactions():
    """
    Return all transactions.
    TODO: Query transactions table
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, date, amount, ttype, category, description FROM transactions;")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_Database():
    """
    Clear the database files
    """ 
    pass
def cleanPrint(rows):
    """
    Print the rows in a clean format
    """
    pass

def delete_transaction(transaction_id):
    conn= get_connection()
    cursor = conn.cursor()
    cursor.execute(" DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
   
    cursor.rowcount

    rowcount = cursor.rowcount
    conn.close()
    return rowcount

def get_summary(): 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ttype, SUM (amount) FROM transactions GROUP BY ttype;")
    summary = cursor.fetchall() 
    conn.close()
    return summary  