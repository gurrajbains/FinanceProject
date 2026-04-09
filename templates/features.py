from datetime import datetime
import torch

SCALE_AMOUNT = 600.0

CATEGORY_MAP = {
    "groceries":0,
    "gas":1,
    "food":2,
    "shopping":3,
    "transport":4,
    "income":5,
    "other":6
}

ALL_KEYWORDS = [
    "walmart","target","costco","kroger","safeway","trader joe","whole foods",
    "mcdonald","burger king","starbucks","chipotle","doordash","ubereats",
    "uber","lyft","taxi","bus","train","metro","shell","chevron","exxon","gas",
    "amazon","ebay","best buy","etsy","aliexpress","shopping",
    "paypal","venmo","bill","payment","rent","utilities","subscription","pay",
    "salary","deposit","paycheck","income","bonus","transfer"
]

def text_to_features(text):
    text = text.lower()
    features = [int(word in text) for word in ALL_KEYWORDS]
    features.append(len(text))
    features.append(sum(c.isdigit() for c in text))
    features.append(sum(c.isalpha() for c in text))
    return features

def encode_category(category):
    if not category:
        return CATEGORY_MAP["other"]
    category = category.lower().strip()
    return CATEGORY_MAP.get(category, CATEGORY_MAP["other"])

def build_features(rows, amounts, i):
    dt = datetime.strptime(rows[i][0], "%Y-%m-%d")

    month = dt.month / 12.0
    day = dt.day / 31.0
    day_of_week = dt.weekday() / 6.0
    is_weekend = 1.0 if dt.weekday() >= 5 else 0.0

    is_month_start = 1.0 if dt.day <= 5 else 0.0
    is_month_end = 1.0 if dt.day >= 25 else 0.0
    week_of_month = (dt.day - 1) // 7 / 4.0

    current = amounts[i] / SCALE_AMOUNT
    prev = amounts[i-1] / SCALE_AMOUNT if i >= 1 else current
    prev2 = amounts[i-2] / SCALE_AMOUNT if i >= 2 else prev

    avg_last_3 = sum(amounts[i-3:i])/3 / SCALE_AMOUNT if i >= 3 else current
    avg_last_5 = sum(amounts[i-5:i])/5 / SCALE_AMOUNT if i >= 5 else avg_last_3

    trend1 = current - prev
    trend2 = current - prev2

    rolling_diff_3 = current - avg_last_3
    rolling_diff_5 = current - avg_last_5

    abs_amount = abs(amounts[i]) / SCALE_AMOUNT
    is_expense = 1.0 if amounts[i] < 0 else 0.0
    is_income = 1.0 if amounts[i] > 0 else 0.0

    std_last_3 = (
        float(torch.tensor(amounts[i-3:i]).std()) / SCALE_AMOUNT
        if i >= 3 else 0.0
    )
    std_last_5 = (
        float(torch.tensor(amounts[i-5:i]).std()) / SCALE_AMOUNT
        if i >= 5 else 0.0
    )

    days_since_last = (
        (dt - datetime.strptime(rows[i-1][0], "%Y-%m-%d")).days / 30.0
        if i >= 1 else 0.0
    )

    features = [
        month, day, day_of_week, is_weekend,
        is_month_start, is_month_end, week_of_month,
        current, prev, prev2,
        avg_last_3, avg_last_5,
        trend1, trend2,
        rolling_diff_3, rolling_diff_5,
        abs_amount, is_expense, is_income,
        std_last_3, std_last_5,
        days_since_last
    ]

    features = [
        0.0 if (f != f or f == float("inf") or f == float("-inf")) else f
        for f in features
    ]

    return features