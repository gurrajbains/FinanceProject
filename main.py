from database import init_db, add_transaction

init_db()

add_transaction(
    "2026-02-01",
    20.00,
    "expense",
    "Food",
    "Lunch"
)

print("Inserted one transaction")
