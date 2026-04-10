import torch
import torch.nn as nn
from models import CategoryModel
from database import get_connection
from features import text_to_features, encode_category, CATEGORY_MAP

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def save_model(model, path):
    torch.save({
        "model_state": model.state_dict(),
        "input_size": next(model.parameters()).shape[1]
    }, path)


def load_model(model, path):
    try:
        checkpoint = torch.load(path, map_location=DEVICE)
        model.load_state_dict(checkpoint["model_state"])
        model.to(DEVICE)
        model.eval()
    except Exception as e:
        print(f"Model load failed: {e}. Using fresh model.")

def train_category(save_path="category.pt", epochs=300, lr=0.001, verbose=True):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description, category FROM finance")
    rows = cursor.fetchall()
    conn.close()

    X, y = [], []

    for desc, cat in rows:
        if not desc:
            continue

        features = text_to_features(desc)
        label = encode_category(cat if cat else "other")

        X.append(features)
        y.append(label)

    if len(X) < 15:
        print("Not enough data to train category model.")
        return None

    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.long)

    input_size = X.shape[1]
    num_classes = len(CATEGORY_MAP)

    model = CategoryModel(input_size, num_classes).to(DEVICE)
    X, y = X.to(DEVICE), y.to(DEVICE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    best_loss = float("inf")
    patience = 40
    patience_counter = 0

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()

        logits = model(X)
        loss = loss_fn(logits, y)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        current_loss = loss.item()

        if current_loss < best_loss:
            best_loss = current_loss
            patience_counter = 0
            save_model(model, save_path)
        else:
            patience_counter += 1

        if verbose and epoch % 50 == 0:
            preds = torch.argmax(logits, dim=1)
            acc = (preds == y).float().mean().item()
            print(f"Epoch {epoch}/{epochs} | Loss: {current_loss:.4f} | Acc: {acc:.2f}")

        if patience_counter >= patience:
            if verbose:
                print("Early stopping triggered.")
            break

    if verbose:
        print(f"Model trained. Best loss: {best_loss:.4f}")

    return model

def predict_category(model, text):
    if not text:
        return "other"

    model.to(DEVICE)
    model.eval()

    features = torch.tensor(
        [text_to_features(text)],
        dtype=torch.float32
    ).to(DEVICE)

    with torch.no_grad():
        logits = model(features)
        probs = torch.softmax(logits, dim=1)
        confidence, pred = torch.max(probs, dim=1)

    reverse_map = {v: k for k, v in CATEGORY_MAP.items()}
    predicted_category = reverse_map.get(pred.item(), "other")

    if confidence.item() < 0.4:
        return "other"

    return predicted_category