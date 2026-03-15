from xml.parsers.expat import model

import torch
import torch.nn as nn
from datetime import datetime
from flask import Flask, jsonify
from database import get_connection 


SCALE_AMOUNT = 600.0 # codee has been refactored tyo use two differen t m,doels fo rincom,e and expenses as the nature of the training data is fundermentally different. 
class BasicModel(nn.Module):
    def __init__(self, input_size=8, hidden_size=32):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1),
        )

    def forward(self, x):
        return self.network(x)

# Separate models
income_model = BasicModel()
expense_model = BasicModel()


def load_model(model, path):
    try:
        state_dict = torch.load(path, map_location="cpu")
        model.load_state_dict(state_dict)
        model.eval()
    except (FileNotFoundError, RuntimeError):
        print(f"Saved model missing or incompatible at {path}. Using fresh model.")


def save_model(model, path):
    torch.save(model.state_dict(), path)


def train_model(model, X, y, save_path, epochs=600, lr=0.001): #epochs=300, lr=0.001 , 15 training clicks pri=accuracy": 64.43848833441734"actual_next_amount": "expense_prediction": -38.663093000650406,"income_prediction": 2453.169286251068
    
    
    perm = torch.randperm(X.size(0))
    X = X[perm]
    y = y[perm]
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=0.0005)
    loss_fn = nn.MSELoss()

    model.train()

    for epoch in range(epochs):
        optimizer.zero_grad()
        preds = model(X)
        loss = loss_fn(preds, y)

        loss.backward()
        optimizer.step()

        if epoch % 100 == 0:
            print("Epoch", epoch, "Loss:", loss.item())

    save_model(model, save_path)

def predict(model, input_values):
    model.eval()
    with torch.no_grad():
        x = torch.tensor(input_values, dtype=torch.float32)

        if x.dim() == 1:
            x = x.unsqueeze(0)

        if x.shape[1] != 7:
            raise ValueError("features must be a list of 7 numbers")

        out = model(x)
        return out.squeeze(1).tolist()


def build_features(rows, amounts, i):
    date_str = rows[i][0]
    dt = datetime.strptime(date_str, "%Y-%m-%d")

    month = dt.month / 12.0
    day = dt.day / 31.0
    day_of_week = dt.weekday() / 6.0
    is_weekend = 1.0 if dt.weekday() >= 5 else 0.0

    current_amount = float(rows[i][1]) / SCALE_AMOUNT
    previous_amount = float(rows[i - 1][1]) / SCALE_AMOUNT
    avg_last_3 = (
        amounts[i - 1] + amounts[i - 2] + amounts[i - 3]
    ) / 3.0 / SCALE_AMOUNT
    avg_last_7 = sum(amounts[i-7:i]) / 7 / SCALE_AMOUNT if i >= 7 else avg_last_3
    return [
        month,
        day,
        day_of_week,
        is_weekend,
        current_amount,
        previous_amount,
        avg_last_3,
        avg_last_7
    ]


def make_expense_training_tensors():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount FROM finance ORDER BY date;")
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 8:
        return None, None

    X = []
    y = []
    amounts = [float(row[1]) for row in rows]

    for i in range(3, len(rows) - 1):
        next_amount_raw = float(rows[i + 1][1])

        # Only train on expenses
        if next_amount_raw >= 0:
            continue

        features = build_features(rows, amounts, i)
        X.append(features)
        y.append([next_amount_raw / SCALE_AMOUNT])

    if not X:
        return None, None

    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

def make_income_training_tensors():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount FROM finance ORDER BY date;")
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 8:
        return None, None

    X = []
    y = []
    amounts = [float(row[1]) for row in rows]

    for i in range(3, len(rows) - 1):
        next_amount_raw = float(rows[i + 1][1])

        # Only train on income
        if next_amount_raw <= 0:
            continue

        features = build_features(rows, amounts, i)
        X.append(features)
        y.append([next_amount_raw / SCALE_AMOUNT])

    if not X:
        return None, None

    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)