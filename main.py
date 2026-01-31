from database import init_db, add_transaction, get_all_transactions

init_db()

add_transaction(
    "Gurraj Bains",
    "2026-02-01",
    20.00,
    "expense",
    "Food",
    "Lunch"
)
while True:
    print("What do you want to do?")
    print("Type 'add' to add a transaction or 'exit' to quit or 'view' to search for a specfic transaction." )
    x = input("Enter your choice: ")
    if x.lower() == 'exit':
        break
    elif x.lower() == 'add':
      print("Adding a new transaction:")
      print("Please provide the following details.")
      name = input("Enter name: ")
      date = input("Enter date (YYYY-MM-DD): ")
      amount = float(input("Enter amount: "))
      ttype = input("Enter type (income/expense): ") 
      if(ttype != "income"): category = input("Enter source: ")   
      else: category = input("Enter category: ")
      description = input("Enter description (optional): ")
      add_transaction(name, date, amount, ttype, category, description)
      print("Transaction added.")


print("Inserted one transaction")
print("All transactions:")

rows = get_all_transactions()
print(rows)