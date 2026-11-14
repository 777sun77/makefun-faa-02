import json
import math
import os
from pathlib import Path


INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)
Z = (-1.644854, -0.674490, 0.0, 0.674490, 1.644854)
BASE_SIGMA = 0.0025
LOCAL_WEIGHT = 0.005
SPREAD_MULTIPLIER = 1.3


def price(value):
    return min(1.0, max(0.0, value))


def deviation(prices):
    window = prices[-1440:]
    changes = [b - a for a, b in zip(window, window[1:])]
    if len(changes) < 30:
        return BASE_SIGMA
    mean = sum(changes) / len(changes)
    variance = sum((x - mean) ** 2 for x in changes) / len(changes)
    local = math.sqrt(variance)
    estimate = (1.0 - LOCAL_WEIGHT) * BASE_SIGMA + LOCAL_WEIGHT * local
    return min(0.05, max(0.00015, estimate))


def forecast(market, horizon):
    prices = market["prices"]
    if not prices:
        raise ValueError("market has no prices")
    last = prices[-1]
    sigma = deviation(prices)
    rows = []
    for h in range(1, horizon + 1):
        spread = SPREAD_MULTIPLIER * sigma * math.sqrt(h)
        rows.append([round(price(last + z * spread), 6) for z in Z])
    return rows


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
for path in sorted(INPUT_DIR.glob("*.in")):
    case = json.loads(path.read_text())
    if tuple(case["quantiles"]) != QUANTILES:
        raise ValueError("unexpected quantile levels")
    forecasts = [
        {"id": market["id"], "q": forecast(market, case["horizon_minutes"])}
        for market in case["markets"]
    ]
    (OUTPUT_DIR / (path.stem + ".out")).write_text(
        json.dumps({"forecasts": forecasts}, separators=(",", ":")) + "\n"
    )
