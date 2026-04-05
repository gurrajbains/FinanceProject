import torch
import torch.nn as nn


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

            nn.Linear(hidden_size // 2, 1)  # ❗ removed ReLU
        )

    def forward(self, x):
        return self.network(x)



class CategoryModel(nn.Module):
    def __init__(self, input_size, num_classes):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        return self.network(x)