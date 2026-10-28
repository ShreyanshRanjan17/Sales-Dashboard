"""Generates a realistic synthetic sales dataset (data/sales_data.csv).

Run directly to regenerate:  python data_generator.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

CATALOG = {
    "Electronics": {"Laptop": 950, "Smartphone": 700, "Headphones": 120, "Smartwatch": 260, "Tablet": 430},
    "Furniture": {"Office Chair": 210, "Standing Desk": 480, "Bookshelf": 150, "Sofa": 820},
    "Clothing": {"Jacket": 110, "Sneakers": 90, "Jeans": 60, "T-Shirt": 25},
    "Home & Kitchen": {"Air Fryer": 100, "Coffee Maker": 85, "Blender": 70, "Cookware Set": 130},
    "Sports": {"Yoga Mat": 35, "Dumbbell Set": 140, "Bicycle": 520, "Treadmill": 900},
}
# (region, weight)
REGIONS = {"North": 0.22, "South": 0.28, "East": 0.20, "West": 0.30}
CHANNELS = {"Online": 0.55, "Retail Store": 0.30, "Wholesale": 0.15}
SEGMENTS = {"Consumer": 0.6, "Corporate": 0.25, "Small Business": 0.15}
# Seasonality by month (1 = Jan)
SEASON = {1: 0.85, 2: 0.85, 3: 0.95, 4: 0.95, 5: 1.0, 6: 1.0,
          7: 0.95, 8: 1.0, 9: 1.05, 10: 1.15, 11: 1.45, 12: 1.6}


def generate(path, start="2024-01-01", end="2025-12-31", seed=42):
    rng = np.random.default_rng(seed)
    days = pd.date_range(start, end, freq="D")
    rows = []
    products = [(c, p, price) for c, items in CATALOG.items() for p, price in items.items()]
    n_days = len(days)

    for i, day in enumerate(days):
        growth = 1 + 0.35 * i / n_days                      # business grows over time
        weekend = 1.2 if day.weekday() >= 5 else 1.0
        lam = 7 * SEASON[day.month] * growth * weekend      # expected orders per day
        for _ in range(rng.poisson(lam)):
            cat, prod, price = products[rng.integers(len(products))]
            region = rng.choice(list(REGIONS), p=list(REGIONS.values()))
            channel = rng.choice(list(CHANNELS), p=list(CHANNELS.values()))
            segment = rng.choice(list(SEGMENTS), p=list(SEGMENTS.values()))
            qty = int(rng.integers(1, 4)) if price < 300 else int(rng.integers(1, 3))
            if channel == "Wholesale":
                qty *= int(rng.integers(2, 6))
            discount = float(rng.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20]))
            unit_price = round(price * rng.uniform(0.95, 1.05), 2)
            revenue = round(unit_price * qty * (1 - discount), 2)
            margin = rng.uniform(0.18, 0.42) - discount * 0.5
            rows.append((day, region, cat, prod, channel, segment, qty, unit_price,
                         discount, revenue, round(revenue * margin, 2)))

    df = pd.DataFrame(rows, columns=["date", "region", "category", "product", "channel",
                                     "segment", "quantity", "unit_price", "discount",
                                     "revenue", "profit"])
    df.insert(0, "order_id", [f"ORD-{100000 + i}" for i in range(len(df))])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    out = Path(__file__).parent / "data" / "sales_data.csv"
    d = generate(out)
    print(f"Generated {len(d):,} orders -> {out}")
