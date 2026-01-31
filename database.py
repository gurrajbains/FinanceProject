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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    print("Database initialized successfully.")
    conn.close


  


def add_transaction(date, amount, type, category, description=""):
    """
    Add a transaction to the database.
    TODO: Insert row into transactions table
    """
    conn =get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (date, amount, type, category, description)
        VALUES (?, ?, ?, ?, ?)
    """, (date, amount, type, category, description))
    conn.commit()
    conn.close()

def get_all_transactions():
    """
    Return all transactions.
    TODO: Query transactions table
    """
    pass
