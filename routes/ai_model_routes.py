from flask import Blueprint, jsonify, request
import torch
from database import get_connection, get_all_transactions
from templates.ai_model import (
    SCALE_AMOUNT, build_features,
    make_expense_training_tensors, make_income_training_tensors,
    predict, train_model, expense_model, income_model,
    category_model, train_category_model, predict_category
)

ai = Blueprint("ai", __name__)
FEATURE_COUNT = 26



def get_recent_features(n):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT date, amount FROM finance ORDER BY date DESC LIMIT {n}")
    rows = cursor.fetchall()
    conn.close()
    if len(rows) < n:
        return None, None
    rows = rows[::-1]
    amounts = [float(r[1]) for r in rows]
    return [build_features(rows, amounts, 3)], amounts


def run_prediction(model, features):
    return predict(model, features) * SCALE_AMOUNT


@ai.route("/api/trainExpenses", methods=["POST"])
def train_expenses():
    X, y = make_expense_training_tensors()
    if X is None or X.shape[0] < 5:
        return jsonify({"error": "Not enough expense data"}), 400
    train_model(expense_model, X, y, "expense_model.pt", epochs=300, lr=0.001)
    return jsonify({"status": "trained expense model"})


@ai.route("/api/trainIncomes", methods=["POST"])
def train_incomes():
    X, y = make_income_training_tensors()
    if X is None or X.shape[0] < 5:
        return jsonify({"error": "Not enough income data"}), 400
    train_model(income_model, X, y, "income_model.pt", epochs=300, lr=0.001)
    return jsonify({"status": "trained income model"})


@ai.route("/api/predict_next/<model_type>")
def predict_next(model_type):
    features, _ = get_recent_features(4)
    if not features:
        return jsonify({"error": "Not enough data"}), 400
    model = expense_model if model_type == "expense" else income_model
    prediction = run_prediction(model, features)
    return jsonify({"prediction": prediction})


@ai.route("/api/ai_comments")
def ai_comments():
    features, _ = get_recent_features(4)
    if not features:
        return jsonify({"error": "Not enough data"}), 400
    expense_pred = run_prediction(expense_model, features)
    income_pred = run_prediction(income_model, features)
    msg = "Expenses predicted higher than income. Reduce spending." \
        if abs(expense_pred) > income_pred else \
        "Income predicted higher than expenses. Good balance."
    return jsonify({"comments": [msg]})


@ai.route("/api/prediction_accuracy")
def prediction_accuracy():
    features, amounts = get_recent_features(5)
    if not features:
        return jsonify({"error": "Not enough data"}), 400
    expense_pred = run_prediction(expense_model, features)[0]
    income_pred = run_prediction(income_model, features)[0]
    actual = amounts[-1]
    if actual == 0:
        accuracy = 100
    elif actual < 0:
        error = abs(expense_pred - actual)
        accuracy = max(0, 100 - (error / abs(actual)) * 100)
    else:
        error = abs(income_pred - actual)
        accuracy = max(0, 100 - (error / abs(actual)) * 100)
    return jsonify({
        "expense_prediction": expense_pred,
        "income_prediction": income_pred,
        "actual": actual,
        "accuracy": accuracy
    })


@ai.route("/api/ai_suggestions")
def ai_suggestions():
    rows = get_all_transactions()
    expenses = [r for r in rows if r[4] == 'expense']
    income = sum(float(r[3]) for r in rows if r[4] == 'income')
    total_expense = abs(sum(float(r[3]) for r in expenses))
    category_totals = {}
    for r in expenses:
        cat = r[5]
        category_totals[cat] = abs(category_totals.get(cat, 0) + float(r[3]))
    suggestions = []
    for cat, total in category_totals.items():
        if income > 0 and total > income * 0.2:
            suggestions.append(f"High spending on {cat}: ${total:.2f}")
    if income > 0 and total_expense > income:
        suggestions.append("Expenses exceed income.")
    return jsonify({"comments": suggestions})


@ai.route("/api/train_category", methods=["POST"])
def api_train_category():
    global category_model
    category_model = train_category_model()
    return jsonify({"status": "Category model trained"})


@ai.route("/api/predict_category", methods=["POST"])
def api_predict_category():
    data = request.get_json()
    if not data or "description" not in data:
        return jsonify({"error": "Missing 'description' field"}), 400
    category = predict_category(data["description"])
    return jsonify({"category": category})