import torch
import torch.nn as nn



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
    """
    X: torch.FloatTensor shape [N, 6]
    y: torch.FloatTensor shape [N, 1]
    """
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
    """
    input_values can be:
      - [f1, f2, f3, f4, f5, f6]
      - [[...6...], [...6...], ...]
    returns list
    """
    model.eval()
    with torch.no_grad():
        x = torch.tensor(input_values, dtype=torch.float32)

        # If user passed one row [6], make it a batch [1,6]
        if x.dim() == 1:
            x = x.unsqueeze(0)

        if x.shape[1] != 6:
            raise ValueError("features must be a list of 6 numbers")

        out = model(x)             # [N,1]
        return out.squeeze(1).tolist()