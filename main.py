from database import get_summary, init_db, add_transaction, get_all_transactions, delete_transaction, delete_all_transactions, get_transactions_by_type
import csv

init_db()
def export_to_csv(rows):
    """
    Export all transactions to a CSV file.
    """
    with open('transactions.csv', 'w', newline='') as csvfile:  #open file in write mode 
        columns = ['Name', 'Date', 'Amount', 'Type', 'Category', 'Description'] # define ccollumns  fo rthe csv files
        writer = csv.writer(csvfile)#writer will be write into csv file
        writer.writerow(columns) # write the header rows 
        for row in rows: #go through every single row in rows and put the values intoo the corresponding header 
            writer.writerow(row)
    
while True:
    print("What do you want to do?")
    print("Type 'add' to add a transaction or 'exit' to quit or 'list' to see all transactions \n or 'delete' to delete a transaction or 'summary' to see a summary of \n transactions or 'export' to export transactions to a CSV file." )
    x = input("Enter your choice: ").strip().lower()
    
    #logic to exit loop
    if x.lower() == 'exit':
        break
    #logic to view all the tranctions in terminal
    elif x.lower() == 'summary':
        print("Displaying summary of transactions below:")
        summary = get_summary()
        for item in summary:
            print(item)
    #logic to export to csv  << can implment a feature to only print out a specfic data range  / data type later and return percentages etc
    elif x.lower() == 'export':
        rows = get_all_transactions()
        export_to_csv(rows) 
        print("Exported transactions to CSV.")
    #logic for adding a transaction
    elif x.lower() == 'add':
      print("Adding a new transaction:")
      print("Please provide the following details.")
      name = input("Enter name: ").strip().lower()
      date = input("Enter date (MM-DD-YYYY): ").strip().lower()
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
    #logic to view transactions 
    elif x.lower() == 'view':
      print("Listing all transactions:")
      rows = get_all_transactions()
      for row in rows:
          print(row) 
    
    #logic to delete a transaction // add abilitiy to delete all tranctions by typing all? << do later
    elif x.lower() == 'delete':
      id = input("Enter the ID of the transaction to delete or 'all' to delete all transactions: ").strip().lower()
      if id == "all":
        print("Deleting all transactions.")
        delete_all_transactions()
        print("All transactions have been deleted. ")
      else:
        print(f"Looking for transaction with ID: {id}")
        row = delete_transaction((id))
        if row == 1:
              print("Transaction deleted.")
        else:
            print("Transaction not found.")
   

