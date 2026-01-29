# database.py
import sqlite3

DB_NAME = "finance.db"


def get_connection():

   
   return sqlite3.connect(DB_NAME)


def init_db():
    """
    Initialize database and tables.
    TODO: Create transactions table
    """
    pass


def add_transaction(date, amount, ttype, category, description=""):
    """
    Add a transaction to the database.
    TODO: Insert row into transactions table
    """
    pass


def get_all_transactions():
    """
    Return all transactions.
    TODO: Query transactions table
    """
    pass
