# ai_model.py
import torch
import torch.nn as nn

class BasicModel(nn.Module):
    def __init__(self, input_size=6, hidden_size=16):
        super(BasicModel, self).__init__()

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
        model.load_state_dict(torch.load(path))
        model.eval()
    except FileNotFoundError:
        print("No saved model found. Using fresh model.")

def save_model(path="model.pt"):
    torch.save(model.state_dict(), path)



def train_model(X, y, epochs=100):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    model.train()

    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(X)
        loss = loss_fn(output, y)
        loss.backward()
        optimizer.step()

    save_model()



def predict(input_values):
    model.eval()
    with torch.no_grad():
        tensor_input = torch.tensor(input_values, dtype=torch.float32)
        result = model(tensor_input)
        return result.tolist()