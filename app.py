from cProfile import label
from flask import Flask, app, jsonify, render_template, request, redirect, send_file, url_for
from database import delete_transaction, init_db, add_transaction, get_all_transactions, return_HTML_table, delete_all_transactions, export_to_csv, get_summary, search_transactions

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
    ttype = request.form["type"].strip()
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

@appp.route("/search", methods=["GET"])
def search():
    q = request.args.get("q", "")
    ttype = request.args.get("type", "all")
    rows = search_transactions(q, ttype)
    return render_template("index.html", rows=rows, q=q, type=ttype)

@appp.route("/api/summary", methods=["GET"])
def api_summary():
    summary_data = get_summary()
    labels = []
    values = []
    for item in summary_data:
        labels.append(item[0])
        values.append(item[1])
    return  jsonify({"labels": labels, "values": values}) #if i want to return date i can add naother aarary for the others and then return that in the json as well

if(__name__ == '__main__'):
    init_db()
    appp.run(debug=True)

    #v \Scripts\activate venv  to activate virtual environment