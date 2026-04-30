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

    VALID_TYPES = {"income", "expense"}

    def clean_amount(value):
        if value is None:
            return 0.0

        value = str(value).replace("$", "").replace(",", "").strip()

        try:
            return float(value)
        except:
            return 0.0

    imported = 0
    skipped = 0
    duplicates = 0

    try:
        stream = (line.decode("utf-8-sig") for line in file.stream)
        reader = csv.DictReader(stream)

        if not reader.fieldnames:
            return redirect(url_for("main.house"))

        conn = get_connection()
        cursor = conn.cursor()

        existing = set()

        cursor.execute("SELECT name, date, amount, type, source FROM finance")

        for row in cursor.fetchall():
            existing.add(tuple(row))

        rows_to_insert = []

        for row in reader:
            try:
                normalized = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items()}

                name = normalized.get("name", "")
                date = normalized.get("date", "")
                amount = clean_amount(normalized.get("amount"))
                ttype = normalized.get("type", "").lower()
                category = normalized.get("category", "")
                description = normalized.get("description", "")

                if not date or ttype not in VALID_TYPES:
                    skipped += 1
                    continue

                transaction_key = (name, date, amount, ttype, category)

                if transaction_key in existing:
                    duplicates += 1
                    continue

                existing.add(transaction_key)

                rows_to_insert.append((name, date, amount, ttype, category, description))

            except:
                skipped += 1
                continue

        if rows_to_insert:
            cursor.executemany(
                "INSERT INTO finance (name, date, amount, type, source, description) VALUES (?, ?, ?, ?, ?, ?)",
                rows_to_insert
            )

            conn.commit()
            imported = len(rows_to_insert)

        conn.close()

        if imported >= 10:
            retrain_models()

        print(f"Imported: {imported} | Skipped: {skipped} | Duplicates: {duplicates}")

    except Exception as e:
        print("CSV Import Error:", e)

    return redirect(url_for("main.house"))