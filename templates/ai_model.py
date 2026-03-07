import torch
import torch.nn as nn
from datetime import datetime

class BasicModel(nn.Module):
    def __init__(self, input_size=6, hidden_size=16):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, x):
        return self.network(x)

model = BasicModel()

def load_model(path="model.pt"):
    try:
        model.load_state_dict(torch.load(path, map_location="cpu"))
        model.eval()
    except FileNotFoundError:
        print("No saved model found. Using fresh model.")

def save_model(path="model.pt"):
    torch.save(model.state_dict(), path)

def train_model(X, y, epochs=200, lr=0.01):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        preds = model(X)
        loss = loss_fn(preds, y)
        loss.backward()
        optimizer.step()

    save_model()

def predict(input_values):
    model.eval()
    with torch.no_grad():
        x = torch.tensor(input_values, dtype=torch.float32)

        if x.dim() == 1:
            x = x.unsqueeze(0)

        if x.shape[1] != 6:
            raise ValueError("features must be a list of 6 numbers")

        out = model(x)
        return out.squeeze(1).tolist()

def make_training_tensors():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT date, amount FROM finance ORDER BY date;")
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 4:
        return None, None

    X = []
    y = []

    amounts = [float(row[1]) for row in rows]

    for i in range(3, len(rows) - 1):
        date_str = rows[i][0]
        current_amount = float(rows[i][1])
        previous_amount = float(rows[i - 1][1])
        avg_last_3 = (amounts[i - 1] + amounts[i - 2] + amounts[i - 3]) / 3.0
        next_amount = float(rows[i + 1][1])

        dt = datetime.strptime(date_str, "%Y-%m-%d")

        month = float(dt.month)
        day = float(dt.day)
        year = float(dt.year)

        X.append([month, day, year, current_amount, previous_amount, avg_last_3])
        y.append([next_amount])

    X = torch.tensor(X, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.float32)

    return X, y