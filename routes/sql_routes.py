from flask import Blueprint, request, redirect, url_for, send_file
from database import (
    add_transaction, delete_all_transactions,
    get_all_transactions, export_to_csv, get_connection
)
from routes.ai_model_routes import retrain_models
import csv

transactions = Blueprint("sql", __name__)


@transactions.route("/add", methods=["POST"])
def add():
    try:
        amount = float(request.form["amount"])
    except:
        return redirect(url_for("main.house"))

    add_transaction(
        request.form["name"].strip(),
        request.form["date"].strip(),
        amount,
        request.form["type"].strip(),
        request.form["source"].strip(),
        request.form.get("description", "").strip()
    )

    if len(get_all_transactions()) % 8 == 0:
        retrain_models()

    return redirect(url_for("main.house"))


@transactions.route("/delete", methods=["POST"])
def delete():
    mode = request.form.get("delete_mode")

    if mode == "all":
        delete_all_transactions()
        return redirect(url_for("main.house"))

    ids = request.form.getlist("delete_ids")

    if ids:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM finance WHERE id IN ({','.join(['?']*len(ids))})",
            ids
        )
        conn.commit()
        conn.close()

    return redirect(url_for("main.house"))


@transactions.route("/export")
def export():
    export_to_csv(get_all_transactions())
    return send_file("finance.csv", as_attachment=True)

# import is very simple minded and doesnt address larger issues with it also ui is trash righht now and needs to be cleaned up as well asn the toolbar bigigest issue right now 
@transactions.route("/import", methods=["POST"])
def import_csv():
    file = request.files.get("file")
    if not file or file.filename == "":
        return redirect(url_for("main.house"))

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
        stream = (line.decode("utf-8-sig") for line in file.stream)
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            return redirect(url_for("main.house"))

        imported_count = 0
        skipped_count = 0
        for row in reader:
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

    return redirect(url_for("main.house"))