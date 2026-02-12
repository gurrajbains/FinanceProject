from flask import Flask, app, render_template, request, redirect, send_file, url_for
from database import delete_transaction, init_db, add_transaction, get_all_transactions, return_HTML_table, delete_all_transactions, export_to_csv, get_summary, get_transactions_by_type

appp = Flask(__name__)


@appp.route('/')
def house():
    rows = get_all_transactions()
    return render_template('index.html', rows = rows)
@appp.route("/add", methods=["POST"])
def add():
    name = request.form["name"].strip()
    date = request.form["date"].strip()
    amount = float(request.form["amount"])
    ttype = request.form["ttype"].strip().lower()
    category = request.form["category"].strip()
    description = request.form.get("description", "").strip()

    add_transaction(name, date, amount, ttype, category, description)

    return redirect(url_for("house"))
@appp.route("/delete", methods=["POST"])
def delete():
    delete_all_transactions()
    return redirect(url_for("house"))



@appp.route("/export", methods=["GET"])
def export():
    rows = get_all_transactions()
    export_to_csv(rows)
    
    return send_file("finance.csv", as_attachment=True, download_name="finance.csv")
    return redirect(url_for("house"))
if(__name__ == '__main__'):
    init_db()
    appp.run(debug=True)

    #v \Scripts\activate venv  to activate virtual environment