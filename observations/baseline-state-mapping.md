# Baseline finding: "Western Australia" silently becomes an empty state

## Summary
On clean baseline data, the AI-built pipeline turned every "Western Australia" into an empty state value. The run reported success with no warnings. The chatbot's first fix reported success but did not change the code that runs. Regenerating the node's code fixed it.

## What happened
- Manual run 1 (11 Oct 2026, 11:21 AM) reported 0 warnings and 0 errors.
- The validation script failed one check: 3 of 176 rows (orders 1080, 1184, 1058) had an empty state. All 3 were "Western Australia" in the input.

## Root cause (from the AI-generated node code)
The state step removed all spaces and converted to uppercase before looking up each value, so "Western Australia" became "WESTERNAUSTRALIA". The lookup list had "WESTERN AUSTRALIA" (with a space, which can never match) and "WESTAUSTRALIA" (a typo), but not "WESTERNAUSTRALIA". The code used `.map()`, which silently replaces any value not in the list with an empty value.

Contributing factor: my prompt said "Remove spaces", which the AI took to mean all spaces, not only leading and trailing ones.

## Chatbot fix (prompt 2, 5 credits)
- I described the problem without giving the cause.
- The chatbot replied that the compile succeeded and the step was patched.
- Only the node's prompt text changed. The code was unchanged. Manual run 2 had the same 3 empty states, and its output was byte-identical to run 1 (same md5).
- Result: the chatbot reported a fix that did not take effect.

## Fix that worked: Regenerate Code (0 credits)
- On the node, Regenerate Code opens a "Regenerate With Feedback" window. I described the cause.
- The new code trims only outer spaces, uses a consistent lookup list, and keeps unmatched values with `.fillna()`.
- Manual run 3 passed all validation checks. Compared with run 2, exactly 3 cells changed (the 3 states, from empty to WA) and nothing else.

## Severity
High. Wrong data was produced with no warning, and the chatbot's fix reported success without working. The impact was limited to 3 rows in one column.

## Suggestions for Rhombus
1. Warn when a step turns non-empty values into empty ones.
2. When the chatbot updates a node's prompt, regenerate its code too, or clearly say that the code was not changed.
3. Make the free Regenerate Code option easier to find, since it worked where the paid chat fix did not.

## How to reproduce
1. Build the pipeline with prompt 1 (see build-and-run-log.md) on datasets/orders_baseline.csv.
2. Run it and check the state column for orders 1080, 1184 and 1058.

## Evidence
- outputs/manual-run-1.csv, manual-run-2.csv, manual-run-3.csv (local, not committed)
- evidence/run1-state-node-code.png
- evidence/regenerate-state-node-code.png
- Full details: build-and-run-log.md