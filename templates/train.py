import torch
import torch.nn as nn
from models import ImprovedModel, CategoryModel
from features import *
from database import get_connection

def save_model(model, path):
    torch.save(model.state_dict(), path)

def load_model(model, path):
    try:
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
    except:
        print("Model not found, using fresh.")

def train_regression(model, X, y, path):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.MSELoss()

    for epoch in range(300):
        optimizer.zero_grad()
        preds = model(X)
        loss = loss_fn(preds, y)
        loss.backward()
        optimizer.step()

    save_model(model, path)

def train_category():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT description, category FROM finance")
    rows = cursor.fetchall()
    conn.close()

    X, y = [], []

    for desc, cat in rows:
        if not desc:
            continue
        X.append(text_to_features(desc))
        y.append(encode_category(cat))

    if len(X) < 10:
        print("Not enough data")
        return

    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.long)

    model = CategoryModel(len(X[0]), len(CATEGORY_MAP))

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(200):
        optimizer.zero_grad()
        logits = model(X)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()

    save_model(model, "category.pt")


def predict_category(model, text):
    features = torch.tensor([text_to_features(text)], dtype=torch.float32)

    with torch.no_grad():
        logits = model(features)
        pred = torch.argmax(logits, dim=1).item()

    reverse = {v:k for k,v in CATEGORY_MAP.items()}
    return reverse.get(pred, "other")