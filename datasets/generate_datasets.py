import random
from datetime import date, timedelta

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


clean = make_clean_rows(N_CLEAN)

print(clean.head(10))
print("Shape:", clean.shape)
print(clean.dtypes)

days = pd.to_datetime(clean["order_date"], format="%m/%d/%Y").dt.day
print("Dates with day > 12:", (days > 12).sum())