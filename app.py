from cProfile import label
from flask import Flask, app, jsonify, render_template, request, redirect, send_file, url_for
from database import delete_transaction, init_db, add_transaction, get_all_transactions, return_HTML_table, delete_all_transactions, export_to_csv, get_summary, return_by_month, search_transactions, sort_transactions

appp = Flask(__name__)


@appp.route('/')
def house():
    rows = get_all_transactions()
    return render_template('index.html', rows = rows)
#house is the basic route which gives all the rows the user hada made 
@appp.route("/add", methods=["POST"])
def add():
    name = request.form["name"].strip()
    date = request.form["date"].strip()
    amount = float(request.form["amount"])
    ttype = request.form["type"].strip()
    category = request.form["source"].strip()
    description = request.form.get("description", "").strip()

    add_transaction(name, date, amount, ttype, category, description)

    return redirect(url_for("house")) # one its been added go back to home page and update the table with the new rows 
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
    q = request.args.get("query", "")
    ttype = request.args.get("type", "all")
    rows = search_transactions(q=q, ttype=ttype)
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

@appp.route("/api/get_by_month", methods=["GET"])
def get_by_month(): 
    rows = return_by_month()
    labels = []
    values = []
    #get the type of chart the user wants to see
    for item in rows:
        labels.append(item[2]) 
        values.append(item[1]) 
        values.append(item[0])

    return jsonify({"labels": labels, "values": values,})

@appp.route("/sort", methods=["GET"])
def sort():    
    sort_by = request.args.get("sort_by", "all")
    type = request.args.get("type", "all")
    rows = sort_transactions(sort_by, type)
    return render_template("index.html", rows=rows, sort_by=sort_by, type=type)


@appp.route("/reset_Search", methods=["POST"])
def reset_search():
    return redirect(url_for("house"))


@appp.route("/update_graphics", methods=["POST"])
def update_graphics():
    chart_type = request.form.get("graphic", "line")
    time_frame = request.form.get("timeFrame", "Monthly")
    data = request.form.get("data", "income")
    return render_template("graphic_Settings.html", chart_type=chart_type, time_frame=time_frame, data=data)
if(__name__ == '__main__'):
    init_db()
    appp.run(debug=True)

    #v \Scripts\activate venv  to activate virtual environment