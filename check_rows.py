import sqlite3

conn = sqlite3.connect("finance.db")
cur = conn.cursor()

cur.execute("SELECT * FROM transactions;")
rows = cur.fetchall()

print(rows)

conn.close()
