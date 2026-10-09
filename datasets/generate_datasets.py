import json
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
random.seed(SEED)

N_CLEAN = 190

FIRST_NAMES = ["Olivia", "Liam", "Ava", "Noah", "Mia", "Ethan", "Chloe", "Lucas", "Zoe", "Jack",
               "Isla", "Henry", "Ruby", "Leo", "Grace", "Oscar", "Ella", "James", "Sophie", "Max"]
LAST_NAMES = ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Nguyen", "Johnson",
              "Martin", "White", "Lee", "Walker", "Hall", "Young", "King"]
STATES = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]


def make_clean_rows(n):
    rows = []
    start = date(2026, 1, 1)
    for i in range(n):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        order_date = start + timedelta(days=random.randint(0, 270))
        rows.append({
            "order_id": 1001 + i,
            "customer_name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}{random.randint(1, 99)}@example.com",
            "state": random.choice(STATES),
            "order_date": order_date.strftime("%m/%d/%Y"),
            "quantity": random.randint(1, 10),
            "unit_price": round(random.uniform(5, 500), 2),
        })
    return pd.DataFrame(rows)


STATE_VARIANTS = {
    "NSW": ["nsw", "New South Wales", " NSW "],
    "VIC": ["vic", "Victoria", " VIC "],
    "QLD": ["qld", "Queensland", " QLD "],
    "WA": ["wa", "Western Australia", " WA "],
    "SA": ["sa", "South Australia", " SA "],
    "TAS": ["tas", "Tasmania", " TAS "],
    "ACT": ["act", "Australian Capital Territory", " ACT "],
    "NT": ["nt", "Northern Territory", " NT "],
}
INVALID_EMAILS = ["n/a", "unknown", "missing@", "noah.smith.example.com", "@example.com"]

DEFECT_COUNTS = {
    "messy_name": 15,
    "missing_email": 10,
    "invalid_email": 5,
    "messy_state": 12,
    "bad_quantity": 8,
    "missing_price": 6,
}
N_DUPLICATES = 10


def mess_up_name(name):
    style = random.choice(["lower_lead", "upper_trail", "both_spaces"])
    if style == "lower_lead":
        return "  " + name.lower()
    if style == "upper_trail":
        return name.upper() + " "
    return " " + name + "  "


def plant_defects(df):
    df = df.copy()
    total = sum(DEFECT_COUNTS.values())
    picked = random.sample(list(df.index), total)

    groups = {}
    start = 0
    for defect, n in DEFECT_COUNTS.items():
        groups[defect] = picked[start:start + n]
        start += n

    for i in groups["messy_name"]:
        df.at[i, "customer_name"] = mess_up_name(df.at[i, "customer_name"])
    df.loc[groups["missing_email"], "email"] = None
    for i, bad in zip(groups["invalid_email"], INVALID_EMAILS):
        df.at[i, "email"] = bad
    for i in groups["messy_state"]:
        df.at[i, "state"] = random.choice(STATE_VARIANTS[df.at[i, "state"]])
    for i in groups["bad_quantity"]:
        df.at[i, "quantity"] = random.choice([0, -1, -2, -5])
    df.loc[groups["missing_price"], "unit_price"] = None

    untouched = [i for i in df.index if i not in picked]
    dup_rows = random.sample(untouched, N_DUPLICATES)
    df = pd.concat([df, df.loc[dup_rows]], ignore_index=True)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    return df, groups


OUT_DIR = Path(__file__).resolve().parent


def drop_column(df):
    return df.drop(columns=["email"])


def rename_column(df):
    return df.rename(columns={"customer_name": "name"})


def change_type(df):
    df = df.copy()
    df["quantity"] = df["quantity"].astype(str) + " units"
    return df


def add_column(df):
    df = df.copy()
    rng = random.Random(SEED)
    df["discount_code"] = [rng.choice(["SAVE10", "VIP20", "WELCOME5", "NONE"]) for _ in range(len(df))]
    return df


def combined(df):
    return add_column(change_type(rename_column(drop_column(df))))


def price_in_cents(df):
    df = df.copy()
    df["unit_price"] = (df["unit_price"] * 100).round().astype("Int64")
    return df


def date_day_first(df):
    df = df.copy()
    dates = pd.to_datetime(df["order_date"], format="%m/%d/%Y")
    df["order_date"] = dates.dt.strftime("%d/%m/%Y")
    return df


def save(df, name):
    path = OUT_DIR / f"orders_{name}.csv"
    df.to_csv(path, index=False, lineterminator="\n")
    print(f"Saved {path.name}: {df.shape[0]} rows, {df.shape[1]} columns")


clean = make_clean_rows(N_CLEAN)
messy, groups = plant_defects(clean)

save(messy, "baseline")

drifts = {
    "schema_drop_column": drop_column,
    "schema_rename_column": rename_column,
    "schema_type_change": change_type,
    "schema_add_column": add_column,
    "schema_combined": combined,
    "semantic_price_cents": price_in_cents,
    "semantic_date_day_first": date_day_first,
}
for name, make_drift in drifts.items():
    save(make_drift(messy), name)

summary = {
    "seed": SEED,
    "total_rows": len(messy),
    "defects": {d: clean.loc[rows, "order_id"].tolist() for d, rows in groups.items()},
    "duplicate_order_ids": messy.loc[messy.duplicated(), "order_id"].tolist(),
}
(OUT_DIR / "defects_summary.json").write_text(json.dumps(summary, indent=2))
print("Saved defects_summary.json")