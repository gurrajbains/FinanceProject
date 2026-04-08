import torch
import torch.nn as nn
from models import CategoryModel
from database import get_connection
from features import text_to_features, encode_category, CATEGORY_MAP

def save_model(model, path):
    torch.save(model.state_dict(), path)

def load_model(model, path):
    try:
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
    except FileNotFoundError:
        print(f"Model file not found at {path}. Using fresh model.")

def train_category(save_path="category.pt", epochs=200, lr=0.001, verbose=True):
    """
    Trains a category classification model based on descriptions and categories in the finance table.
    Returns the trained model instance.
    """
    
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
        y.append(encode_category(cat if cat else "other"))

    if len(X) < 10:
        print("Not enough data to train category model.")
        return None

    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.long)

   
    input_size = len(X[0])
    num_classes = len(CATEGORY_MAP)
    model = CategoryModel(input_size, num_classes)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    X, y = X.to(device), y.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        logits = model(X)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()

        if verbose and epoch % 50 == 0:
            print(f"Epoch {epoch}/{epochs} | Loss: {loss.item():.4f}")

    save_model(model, save_path)
    if verbose:
        print(f"Category model trained and saved to {save_path}")

    return model

def predict_category(model, text):
    """
    Predicts the category for a single description using a trained model.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    features = torch.tensor([text_to_features(text)], dtype=torch.float32).to(device)
    model.to(device)
    model.eval()

    with torch.no_grad():
        logits = model(features)
        pred = torch.argmax(logits, dim=1).item()

    reverse_map = {v: k for k, v in CATEGORY_MAP.items()}
    return reverse_map.get(pred, "other")