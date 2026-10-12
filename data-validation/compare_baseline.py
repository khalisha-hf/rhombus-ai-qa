"""Compare a pipeline output with the baseline output, matched by order_id.

Usage: python data-validation/compare_baseline.py <baseline.csv> <new.csv>
Exit code 0 if everything matches, 1 otherwise.
"""
import sys
import pandas as pd

base_path, new_path = sys.argv[1], sys.argv[2]
base = pd.read_csv(base_path, dtype=str, keep_default_na=False).set_index("order_id")
new = pd.read_csv(new_path, dtype=str, keep_default_na=False).set_index("order_id")

problems = 0
print(f"Rows: baseline {len(base)}, new {len(new)}")

dups = new.index[new.index.duplicated()].unique()
if len(dups):
    problems += 1
    print(f"[FAIL] new has {len(dups)} repeated order_ids, comparing the first of each")
    new = new[~new.index.duplicated()]

missing = base.index.difference(new.index)
extra = new.index.difference(base.index)
if len(missing) or len(extra):
    problems += 1
    print(f"[FAIL] order_ids missing from new: {len(missing)}, extra in new: {len(extra)}")

only_base = [c for c in base.columns if c not in new.columns]
only_new = [c for c in new.columns if c not in base.columns]
if only_base or only_new:
    problems += 1
    print(f"[FAIL] columns only in baseline: {only_base}, only in new: {only_new}")

shared = base.index.intersection(new.index)
for col in [c for c in base.columns if c in new.columns]:
    diff = base.loc[shared, col] != new.loc[shared, col]
    if diff.any():
        problems += 1
        print(f"[FAIL] {col}: {diff.sum()} of {len(shared)} rows differ")
        for oid in diff[diff].index[:5]:
            print(f"       order_id {oid}: baseline {base.at[oid, col]!r}, new {new.at[oid, col]!r}")
    else:
        print(f"[PASS] {col}: all {len(shared)} rows match")

sys.exit(1 if problems else 0)