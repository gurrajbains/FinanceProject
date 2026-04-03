from flask import Blueprint, request, redirect, url_for, send_file
from database import (
    add_transaction, delete_all_transactions,
    get_all_transactions, export_to_csv, get_connection
)
from routes.ai_model_routes import retrain_models

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
        cursor.execute(f"DELETE FROM finance WHERE id IN ({','.join(['?']*len(ids))})", ids)
        conn.commit()
        conn.close()

    return redirect(url_for("main.house"))


@transactions.route("/export")
def export():
    export_to_csv(get_all_transactions())
    return send_file("finance.csv", as_attachment=True)