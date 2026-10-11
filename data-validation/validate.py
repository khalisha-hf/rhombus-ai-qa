import sys
from pathlib import Path

import pandas as pd

EXPECTED_COLUMNS = {
    "order_id", "customer_name", "email", "state", "order_date",
    "quantity", "unit_price", "email_valid", "line_total",
}
EXPECTED_ROWS = 176
EXPECTED_EMAIL_VALID = {True: 161, False: 15}
STATE_CODES = {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"}
EMAIL_PATTERN = r"[^@\s]+@[^@\s]+\.[^@\s]+"
PRICE_MIN, PRICE_MAX = 5, 500

results = []


def check(name, passed, detail=""):
    results.append((name, bool(passed), detail))


def run_checks(df):
    cols = set(df.columns)
    check("Columns match expected", cols == EXPECTED_COLUMNS,
          f"missing={sorted(EXPECTED_COLUMNS - cols)}, extra={sorted(cols - EXPECTED_COLUMNS)}")
    check("Row count", len(df) == EXPECTED_ROWS, f"expected {EXPECTED_ROWS}, got {len(df)}")
    check("No duplicate rows", not df.duplicated().any(), f"{df.duplicated().sum()} duplicates")
    if "order_id" in cols:
        repeated = int(df["order_id"].duplicated().sum())
        check("order_id is unique", repeated == 0, f"{repeated} repeated order_ids")

    if not EXPECTED_COLUMNS.issubset(cols):
        check("Rule checks", False, "skipped because required columns are missing")
        return

    names = df["customer_name"].astype(str)
    check("Names trimmed", (names == names.str.strip()).all())
    check("Names in title case", (names == names.str.title()).all())

    bad_states = sorted(set(df["state"]) - STATE_CODES)
    check("State uses the 8 codes only", not bad_states, f"unexpected values: {bad_states}")

    qty = pd.to_numeric(df["quantity"], errors="coerce")
    check("Quantity is a number above 0", qty.notna().all() and (qty > 0).all())

    price = pd.to_numeric(df["unit_price"], errors="coerce")
    check("No missing unit_price", price.notna().all())
    check(f"unit_price between {PRICE_MIN} and {PRICE_MAX}",
          price.between(PRICE_MIN, PRICE_MAX).all(),
          f"min={price.min()}, max={price.max()}")

    dates = df["order_date"].astype(str)
    parsed = pd.to_datetime(dates, format="%Y-%m-%d", errors="coerce")
    check("order_date is YYYY-MM-DD", dates.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all() and parsed.notna().all())

    valid = df["email_valid"].astype(str).str.lower().map({"true": True, "false": False})
    check("email_valid only true/false", valid.notna().all())
    counts = {True: int((valid == True).sum()), False: int((valid == False).sum())}
    check("email_valid counts", counts == EXPECTED_EMAIL_VALID,
          f"expected {EXPECTED_EMAIL_VALID}, got {counts}")
    check("Invalid emails are blank", df.loc[valid == False, "email"].isna().all())
    check("Valid emails look valid",
          df.loc[valid == True, "email"].astype(str).str.fullmatch(EMAIL_PATTERN).all())

    line_total = pd.to_numeric(df["line_total"], errors="coerce")
    expected_total = (qty * price).round(2)
    check("line_total = quantity x unit_price", ((line_total - expected_total).abs() < 0.005).all())


def main():
    if len(sys.argv) != 2:
        print("Usage: python data-validation/validate.py <output.csv>")
        sys.exit(2)

    path = Path(sys.argv[1])
    df = pd.read_csv(path)
    run_checks(df)

    print(f"Validating {path}\n")
    for name, passed, detail in results:
        mark = "PASS" if passed else "FAIL"
        extra = f"  ({detail})" if detail and not passed else ""
        print(f"[{mark}] {name}{extra}")

    failed = sum(1 for _, passed, _ in results if not passed)
    print(f"\n{len(results) - failed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()