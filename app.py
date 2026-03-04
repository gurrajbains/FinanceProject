from cProfile import label
from flask import Flask, app, jsonify, render_template, request, redirect, send_file, url_for
from database import delete_transaction, get_connection, init_db, add_transaction, get_all_transactions, return_HTML_table, delete_all_transactions, export_to_csv, get_summary, return_by_month, search_transactions, sort_transactions
from templates import ai_model
from templates.ai_model import load_model, predict


appp = Flask(__name__)

load_model()
@appp.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json()

    features = data.get("features")

    if not features:
        return jsonify({"error": "Missing features"}), 400

    if len(features[0]) != 6:
        return jsonify({"error": "Input must contain 6 values"}), 400

    prediction = predict(features)

    return jsonify({"prediction": prediction})
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
    mode = request.form.get("delete_mode", "selected")

    if mode == "all":
        delete_all_transactions()
        return redirect(url_for("house"))

    ids = request.form.getlist("delete_ids")
    if not ids:
        return redirect(url_for("house"))
 
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(ids))
    cursor.execute(f"DELETE FROM finance WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()
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
#needs to go
@appp.route("/api/summary", methods=["GET"])
def api_summary():
    summary_data = get_summary()
    labels = []
    values = []
    for item in summary_data:
        labels.append(item[0])
        values.append(item[1])
    return  jsonify({"labels": labels, "values": values}) #if i want to return date i can add naother aarary for the others and then return that in the json as well
#needs to go

@appp.route("/sort", methods=["GET"])
def sort():    
    sort_by = request.args.get("sort_by", "all")
    type = request.args.get("type", "all")
    rows = sort_transactions(sort_by, type)
    return render_template("index.html", rows=rows, sort_by=sort_by, type=type)


@appp.route("/reset_Search", methods=["POST"])
def reset_search():
    return redirect(url_for("house"))
@appp.route("/api/make_graph", methods=["GET"])
def make_graph():
    chart_type = request.args.get("graphic", "line")
    timeframe = request.args.get("timeFrame", "Monthly")
    print(chart_type, timeframe)
    metric = request.args.get("metric","income")
    timeRange = request.args.get("timeRange","")
   
    rows = get_summary(metric, timeframe, timeRange)
    labels = [item[0] for item in rows]
    values = [item[1] for item in rows]
    print(chart_type, timeframe, metric, timeRange)
    return jsonify({"labels": labels, "values": values, "chart": chart_type, "timeframe": timeframe})
if(__name__ == '__main__'):
    init_db()
    appp.run(debug=True)

    #v \Scripts\activate venv  to activate virtual environment