from pyexpat import features

from flask import Flask, jsonify, render_template, request, redirect, send_file, url_for
from database import get_connection, init_db, add_transaction, get_all_transactions, delete_all_transactions, export_to_csv, get_summary, search_transactions, sort_transactions
from templates.ai_model import (
    SCALE_AMOUNT,
    build_features,
    load_model,
    make_expense_training_tensors,
    make_income_training_tensors,
    predict,
    train_model,
    expense_model,
    income_model
)
Features = 26
appp = Flask(__name__)

load_model(expense_model, "expense_model.pt")
load_model(income_model, "income_model.pt")
FEATURE_COUNT = 26


def retrain_models(): #helper fucntion such that 
    X_exp, y_exp = make_expense_training_tensors()
    if X_exp is not None and y_exp is not None and X_exp.shape[0] >= 5:
        train_model(expense_model, X_exp, y_exp, "expense_model.pt", epochs=300, lr=0.001)

    X_inc, y_inc = make_income_training_tensors()
    if X_inc is not None and y_inc is not None and X_inc.shape[0] >= 5:
        train_model(income_model, X_inc, y_inc, "income_model.pt", epochs=300, lr=0.001)
        
@appp.route("/api/trainExpenses", methods=["POST"])
def api_trainExpenses():
    X, y = make_expense_training_tensors()

    if X is None or y is None or X.shape[0] < 5:
        return jsonify({"error": "Not enough expense data to train."}), 400

    train_model(expense_model, X, y, "expense_model.pt", epochs=300, lr=0.001)
    return jsonify({"status": "expense model trained", "rows_used": int(X.shape[0])})

@appp.route("/api/trainIncomes", methods=["POST"])
def api_trainIncomes():
    X, y = make_income_training_tensors()
    if X is None or y is None or X.shape[0] < 5:
        return jsonify({"error": "Not enough income data to train."}), 400
    train_model(income_model, X, y, "income_model.pt", epochs=300, lr=0.001)
    return jsonify({"status": "income model trained", "rows_used": int(X.shape[0])})


@appp.route("/api/ai_comments", methods=["GET"])
def api_ai_comments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, amount FROM finance ORDER BY date DESC LIMIT 4")
    rows = cursor.fetchall()
    conn.close()
    if len(rows) < 4: # determiens how many rowsd we need
        return jsonify({"error": "Not enough data"}), 400

    rows = rows[::-1]

    amounts = [float(r[1]) for r in rows] # grabs the amounts in the r in rows and then makes a list of thouse in amoutns a
    features = [build_features(rows, amounts, 3)] #features are thge last 4 transactions
    expense_prediction = predict(expense_model, features) * SCALE_AMOUNT
    income_prediction = predict(income_model, features) * SCALE_AMOUNT

    comments = []
    if (abs(expense_prediction) > income_prediction):
        comments.append("Your expenses are predicted to be higher than your income. Consider reviewing your spending habits.")
    else:
        comments.append("Your income is predicted to be higher than your expenses. Keep up the good work!")

    return jsonify({"comments": comments})


@appp.route("/api/prediction_accuracy", methods=["GET"])
def api_prediction_accuracy():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount FROM finance ORDER BY date DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 5: # use less than 5 as the preidction we used for output is based off the last 4 thus we need at least 5 to have a real next amount to compare it to
        return jsonify({"error": "Not enough data"}), 400
    rows = rows[::-1]
    amounts = [float(r[1]) for r in rows]

    features = [build_features(rows, amounts, 3)]

    expense_prediction = predict(expense_model, features)[0] * SCALE_AMOUNT
    income_prediction = predict(income_model, features)[0] * SCALE_AMOUNT

    actual_next_amount = amounts[-1]

    if actual_next_amount < 0:
        error = abs(expense_prediction - actual_next_amount)
        accuracy = max(0, 100 - (error / abs(actual_next_amount)) * 100)
    else:
        error = abs(income_prediction - actual_next_amount)
        accuracy = max(0, 100 - (error / abs(actual_next_amount)) * 100)
    print("Expense Prediction:", expense_prediction)
    print("Income Prediction:", income_prediction)
    print("Actual Next Amount:", actual_next_amount)
    print("Prediction Accuracy:", accuracy)

    return jsonify({
        "expense_prediction": expense_prediction,
        "income_prediction": income_prediction,
        "actual_next_amount": actual_next_amount,
        "accuracy": accuracy
    })


@appp.route("/api/predict_next_expense", methods=["GET"])
def predict_next_expense():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount FROM finance ORDER BY date DESC LIMIT 4")
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 4:
        return jsonify({"error": "Not enough data"}), 400

    rows = rows[::-1]
    amounts = [float(r[1]) for r in rows]
    features = [build_features(rows, amounts, 3)]
    prediction = predict(expense_model, features)
    prediction = prediction * SCALE_AMOUNT
    return jsonify({"prediction": prediction})


@appp.route("/api/predict_next_income", methods=["GET"])
def predict_next_income():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount FROM finance ORDER BY date DESC LIMIT 4")
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 4:
        return jsonify({"error": "Not enough data"}), 400

    rows = rows[::-1]
    amounts = [float(r[1]) for r in rows]

    features = [build_features(rows, amounts, 3)]
    prediction = predict(income_model, features)
    prediction = prediction * SCALE_AMOUNT
    return jsonify({"prediction": prediction})


@appp.route("/api/predictIncomes", methods=["POST"])
def api_predictIncomes():
    data = request.get_json()
    features = data.get("features")

    if not features:
        return jsonify({"error": "Missing features"}), 400

    if len(features[0]) != FEATURE_COUNT:
        return jsonify({"error": f"Input must contain {FEATURE_COUNT} values"}), 400
    prediction = predict(income_model, features)
    prediction = prediction * SCALE_AMOUNT

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
    retrain_models()   

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
@appp.route("/api/make_graph")
def make_graph():
    graphic = request.args.get("graphic", "line")
    metric = request.args.get("metric", "income")   # ✅ FIXED
    timeframe = request.args.get("timeFrame", "Monthly")

    # ✅ Proper timeRange handling
    timeRange = request.args.get("timeRange")

    if not timeRange or timeRange.strip() == "":
        timeRange = None

    print("GRAPH DEBUG ->", graphic, timeframe, metric, timeRange)

    rows = get_summary(metric, timeframe, timeRange)

    labels = [r[0] for r in rows]
    values = [float(r[1]) for r in rows]

    return jsonify({
        "labels": labels,
        "values": values,
        "chart": graphic,
        "timeframe": timeframe
    })

@appp.route("/import", methods=["POST"])
def import_csv():
    file = request.files.get("file")

    if not file or file.filename == "":
        return redirect(url_for("house"))

    import csv

    def clean_amount(value):
        if value is None:
            return 0.0
        value = str(value).strip().replace("$", "").replace(",", "")
        if value == "":
            return 0.0
        try:
            return float(value)
        except ValueError:
            return 0.0

    try:
        stream = file.stream.read().decode("utf-8-sig").splitlines()
        reader = csv.DictReader(stream)

        if not reader.fieldnames:
            return redirect(url_for("house"))

        print("CSV headers:", reader.fieldnames)

        imported_count = 0
        skipped_count = 0

        for row in reader:
            print("ROW:", row)

            name = (row.get("Name") or "").strip()
            date = (row.get("Date") or "").strip()
            amount = clean_amount(row.get("Amount"))
            ttype = (row.get("Type") or "").strip()
            category = (row.get("Category") or "").strip()
            description = (row.get("Description") or "").strip()

            if not date:
                
                skipped_count += 1
                continue

            add_transaction(name, date, amount, ttype, category, description)
            imported_count += 1

        if imported_count > 0:
            retrain_models()

       
    except Exception as e:
        print("Error importing CSV:", e)

    return redirect(url_for("house"))
if(__name__ == '__main__'):
    init_db()
    appp.run(debug=True) #v \Scripts\activate venv  to activate virtual environment