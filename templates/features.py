from datetime import datetime
import torch

SCALE_AMOUNT = 600.0

CATEGORY_MAP = {
    "groceries": 0,
    "gas": 1,
    "food": 2,
    "shopping": 3,
    "transport": 4,
    "income": 5,
    "other": 6
}

ALL_KEYWORDS = [
    "walmart","target","costco","kroger","safeway","trader joe","whole foods",
    "mcdonald","burger king","starbucks","chipotle","doordash","ubereats",
    "uber","lyft","taxi","bus","train","metro",
    "shell","chevron","exxon","gas",
    "amazon","ebay","best buy","etsy","shopping",
    "paypal","venmo","rent","utilities","subscription",
    "salary","deposit","paycheck","income","bonus"
]


def text_to_features(text):
    text = (text or "").lower()

    features = [int(word in text) for word in ALL_KEYWORDS]

    features += [
        len(text),
        sum(c.isdigit() for c in text),
        sum(c.isalpha() for c in text)
    ]

    return features


def encode_category(cat):
    if not cat:
        return CATEGORY_MAP["other"]
    return CATEGORY_MAP.get(cat.lower().strip(), CATEGORY_MAP["other"])


def build_features(rows, amounts, i):
    dt = datetime.strptime(rows[i][0], "%Y-%m-%d")

    # time
    month = dt.month / 12
    day = dt.day / 31
    dow = dt.weekday() / 6
    weekend = 1.0 if dt.weekday() >= 5 else 0.0
    month_start = 1.0 if dt.day <= 5 else 0.0
    month_end = 1.0 if dt.day >= 25 else 0.0

    # amounts
    curr = amounts[i] / SCALE_AMOUNT
    prev = amounts[i-1] / SCALE_AMOUNT if i > 0 else curr
    prev2 = amounts[i-2] / SCALE_AMOUNT if i > 1 else prev

    avg3 = sum(amounts[max(0,i-3):i+1]) / max(1,len(amounts[max(0,i-3):i+1])) / SCALE_AMOUNT
    avg5 = sum(amounts[max(0,i-5):i+1]) / max(1,len(amounts[max(0,i-5):i+1])) / SCALE_AMOUNT

    # trends
    trend1 = curr - prev
    trend2 = curr - prev2
    rolling_diff3 = curr - avg3
    rolling_diff5 = curr - avg5

    # volatility
    window = torch.tensor(amounts[max(0,i-3):i+1], dtype=torch.float32)
    std3 = float(window.std()) / SCALE_AMOUNT if len(window) > 1 else 0.0

    # behavior
    is_expense = 1.0 if amounts[i] < 0 else 0.0
    is_income = 1.0 if amounts[i] > 0 else 0.0

    # category (safe fallback)
    category_encoded = 0.0

    features = [
        month, day, dow, weekend,
        month_start, month_end,

        curr, prev, prev2,
        avg3, avg5,

        trend1, trend2,
        rolling_diff3, rolling_diff5,

        std3,
        is_expense, is_income,

        category_encoded
    ]

    return [0.0 if f != f or f == float("inf") or f == float("-inf") else f for f in features]