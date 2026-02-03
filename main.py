from database import get_summary, init_db, add_transaction, get_all_transactions, delete_transaction

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
    print("Type 'add' to add a transaction or 'exit' to quit or 'view' to see all transactions or 'delete' to delete a transaction or 'summary' to see a summary of transactions." )
    x = input("Enter your choice: ").strip().lower()
    if x.lower() == 'exit':
        break
    elif x.lower() == 'summary':
        print("Displaying summary of transactions below:")
        summary = get_summary()
        for item in summary:
            print(item)
    elif x.lower() == 'add':
      print("Adding a new transaction:")
      print("Please provide the following details.")
      name = input("Enter name: ").strip().lower()
      date = input("Enter date (YYYY-MM-DD): ").strip().lower()
      amount = float(input("Enter amount: "))
      ttype = input("Enter type (income/expense): ") .strip().lower()
      if(ttype == "income"): category = input("Enter source: ").strip().lower()   
      elif(ttype == "expense"): category = input("Enter category: ").strip().lower()
      else:
          print("Invalid type. Please enter 'income' or 'expense'.")
          continue
      description = input("Enter description (optional): ").strip().lower()
      add_transaction(name, date, amount, ttype, category, description)
      print("Inserted one transaction")
    elif x.lower() == 'view':
      print("Listing all transactions:")
      rows = get_all_transactions()
      for row in rows:
          print(row) 
    elif x.lower() == 'delete':
      id = input("Enter the ID of the transaction to delete: ").strip().lower()
    print("Looking for transaction with ID:{id}")
    row = delete_transaction(int(id))
    if row == 1:
           print("Transaction deleted.")
    else:
           print("Transaction not found.")
   

