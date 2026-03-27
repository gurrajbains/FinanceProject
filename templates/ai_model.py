from xml.parsers.expat import model
import torch
import torch.nn as nn
from datetime import datetime
from flask import Flask, jsonify
from database import get_connection 

SCALE_AMOUNT = 600.0 # code has been refactored to use two different models for income and expenses as the nature of the training data is fundamentally different. 
class ImprovedModel(nn.Module):
    def __init__(self, input_size=26, hidden_size=64, dropout=0.2):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.LeakyReLU(0.01),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.LeakyReLU(0.01),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.LeakyReLU(0.01),
            nn.Linear(hidden_size // 2, 1),
            nn.ReLU()
        )

    def forward(self, x):
        return self.network(x)

# Separate models
income_model = ImprovedModel()
expense_model = ImprovedModel()
category_model = ImprovedModel(input_size=10, hidden_size=16) 


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

FEATURE_COUNT = 26

def predict(model, features):
    if len(features[0]) != FEATURE_COUNT:
        raise ValueError(f"features must be a list of {FEATURE_COUNT} numbers")

    X = torch.tensor(features, dtype=torch.float32)
    model.eval()
    with torch.no_grad():
        output = model(X).item()

    if output != output:  # NaN check
        return 0.0

    return float(output)

def build_features(rows, amounts, i):
    dt = datetime.strptime(rows[i][0], "%Y-%m-%d")
    month = dt.month / 12.0
    day = dt.day / 31.0
    day_of_week = dt.weekday() / 6.0
    is_weekend = 1.0 if dt.weekday() >= 5 else 0.0

    # Safely get previous amounts
    current_amount = amounts[i] / SCALE_AMOUNT
    previous_amount = amounts[i-1] / SCALE_AMOUNT if i >= 1 else 0.0
    lag2 = amounts[i-2] / SCALE_AMOUNT if i >= 2 else 0.0
    lag3 = amounts[i-3] / SCALE_AMOUNT if i >= 3 else 0.0
    lag4 = amounts[i-4] / SCALE_AMOUNT if i >= 4 else 0.0
    lag5 = amounts[i-5] / SCALE_AMOUNT if i >= 5 else 0.0

    # Rolling averages
    avg_last_3 = sum(amounts[i-3:i])/3 / SCALE_AMOUNT if i >= 3 else current_amount
    avg_last_5 = sum(amounts[i-5:i])/5 / SCALE_AMOUNT if i >= 5 else avg_last_3
    avg_last_7 = sum(amounts[i-7:i])/7 / SCALE_AMOUNT if i >= 7 else avg_last_3

    # Rolling std
    rolling_window = amounts[i-3:i] if i >= 3 else amounts[:i]
    if len(rolling_window) >= 2:
        rolling_std3 = torch.std(torch.tensor(rolling_window, dtype=torch.float32)).item() / SCALE_AMOUNT
    else:
        rolling_std3 = 0.0

    # Start/end month flags
    is_start_month = 1.0 if dt.day <= 3 else 0.0
    is_end_month = 1.0 if dt.day >= 28 else 0.0

    # Quarter and trends
    quarter = ((dt.month - 1) // 3) / 3.0
    diff_prev = (amounts[i] - amounts[i-1]) / SCALE_AMOUNT if i >= 1 else 0.0
    trend = (amounts[i] - amounts[i-3]) / SCALE_AMOUNT if i >= 3 else 0.0

    # Cumulative sum safely
    cumsum = sum(amounts[:i]) / SCALE_AMOUNT if i >= 1 else 0.0

    # Category encoding
    category_encoded = encode_category(rows[i][2] if len(rows[i]) > 2 else "other") / 10.0
    prev_category = encode_category(rows[i-1][2] if i >= 1 and len(rows[i-1]) > 2 else "other") / 10.0
    cat_change = 1.0 if category_encoded != prev_category else 0.0

    # Min/max safely
    last_3_window = amounts[i-3:i] if i >= 3 else amounts[:i]
    max_last_3 = max(last_3_window)/SCALE_AMOUNT if last_3_window else 0.0
    min_last_3 = min(last_3_window)/SCALE_AMOUNT if last_3_window else 0.0

    zero_pad = 0.0

    features = [
        month, day, day_of_week, is_weekend,
        current_amount, previous_amount, avg_last_3, avg_last_7,
        lag2, lag3, rolling_std3, is_start_month, is_end_month,
        quarter, diff_prev, cumsum,
        category_encoded, prev_category, cat_change,
        lag4, lag5, avg_last_5,
        max_last_3, min_last_3, trend, zero_pad
    ]

    # Remove NaNs and infinities
    features = [0.0 if (isinstance(f, float) and (f != f or f == float("inf") or f == float("-inf"))) else f for f in features]

    return features

def categorize_transaction(description):
    if not description:
        return "other"
    desc = description.lower().strip()
    rules = {
        "groceries": ["walmart","target","costco","kroger","safeway","trader joe","whole foods","foodmaxx","raleys","save mart"],
        "gas": ["shell","chevron","exxon","76","arco","valero","gas","fuel"],
        "food": ["mcdonald","starbucks","chipotle","doordash","ubereats","grubhub","restaurant","cafe","pizza","taco","burger"],
        "shopping": ["amazon","ebay","best buy","nike","apple","store","mall","online"],
        "transport": ["uber","lyft","bus","train","bart","metro","taxi"],
        "income": ["deposit","payroll","salary","paycheck","zelle","venmo","refund","bonus","direct dep"]
    }
    for category, keywords in rules.items():
        for word in keywords:
            if word in desc:
                return category
    scores = {key:0 for key in rules.keys()}
    words = desc.split()
    for w in words:
        for category, keywords in rules.items():
            for k in keywords: # checking each row for each keyword and then give it a score & then return cat with highest score then cat as that
                if w in k or k in w:
                    scores[category] += 1
    best_category = max(scores, key=scores.get)
    if scores[best_category] > 0:
        return best_category
    return "other"

CATEGORY_MAP = {
        "groceries":0,
        "gas":1,
        "food":2,
        "shopping":3,
        "transport":4,
        "income":5,
        "other":6
}

def encode_category(category):
    if not category:
        return CATEGORY_MAP["other"]
    category = category.lower().strip()
    if category not in CATEGORY_MAP:
        CATEGORY_MAP[category] = len(CATEGORY_MAP)
    return CATEGORY_MAP[category]

def make_category_training_tensors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description, category FROM finance WHERE description IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    if len(rows) < 10:
        return None, None
    X = []
    y = []
    for desc, cat in rows:
        features = text_to_features(desc)
        label = encode_category(cat)
        X.append(features)
        y.append(label)
    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.long)
    return X, y

def text_to_features(text):
    text = text.lower()
    features = [
        len(text),
        sum(c.isdigit() for c in text),
        sum(c.isalpha() for c in text),
        int("uber" in text),
        int("amazon" in text),
        int("walmart" in text),
        int("gas" in text),
        int("food" in text),
        int("pay" in text),
        int("deposit" in text)
    ]
    return features

def train_category_model():
    X, y = make_category_training_tensors()
    if X is None:
        return
    train_model(category_model, X, y, "category_model.pt", epochs=200, lr=0.001)

def predict_category(description):
    features = [text_to_features(description)]
    pred = predict(category_model, features)
    index = int(round(pred))
    reverse_map = {
        0:"groceries",
        1:"gas",
        2:"food",
        3:"shopping",
        4:"transport",
        5:"income",
        6:"other"
    }
    return reverse_map.get(index, "other")

def make_expense_training_tensors():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount, category FROM finance ORDER BY date;")
    rows = cursor.fetchall()
    conn.close()
    if len(rows) < 8:
        return None, None

    rows = [r for r in rows if float(r[1]) < 0]

    amounts = [abs(float(row[1])) for row in rows]

    X = []
    y = []

    for i in range(3, len(rows) - 1):

        next_amount = abs(float(rows[i+1][1]))

        features = build_features(rows, amounts, i)

        X.append(features)
        y.append([next_amount / SCALE_AMOUNT])

    if not X:
        return None, None
    return (
        torch.tensor(X, dtype=torch.float32),
        torch.tensor(y, dtype=torch.float32)
    )

def make_income_training_tensors():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount, category FROM finance ORDER BY date;")
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 8:
        return None, None

    rows = [r for r in rows if float(r[1]) > 0]

    amounts = [abs(float(row[1])) for row in rows]

    X = []
    y = []

    for i in range(3, len(rows) - 1):
        next_amount = abs(float(rows[i+1][1]))

        features = build_features(rows, amounts, i)

        X.append(features)
        y.append([next_amount / SCALE_AMOUNT])

    if not X:
        return None, None

    return (
        torch.tensor(X, dtype=torch.float32),
        torch.tensor(y, dtype=torch.float32)
    )