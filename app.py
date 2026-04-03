from flask import Flask
from database import init_db
from templates.ai_model import load_model, expense_model, income_model

from routes.ai_model_routes import ai
from routes.ui_routes import main
from routes.sql_routes import transactions
from routes.analytics import analytics

app = Flask(__name__)
app.register_blueprint(main)
app.register_blueprint(transactions)
app.register_blueprint(analytics)
app.register_blueprint(ai)
load_model(expense_model, "expense_model.pt")
load_model(income_model, "income_model.pt")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)