# AI builder prompt log

Every pipeline step was built with the Rhombus AI builder only. No nodes were added or edited by hand. One node's code was later rebuilt with Rhombus's "Regenerate Code" feature, which is also AI-generated (see below).

## Prompt 1: Build the cleaning pipeline

- Date and time (AEDT): 9 Oct 2026, about 6:50 PM
- Mode: Pipeline
- Context attached: input/orders.csv
- Credits: 39 before, 34 after (this prompt cost 5 credits)
- Prompt:

```text
Build a cleaning pipeline for the attached file input/orders.csv. Apply these steps in this order:

1. Remove exact duplicate rows.
2. In customer_name, remove leading and trailing spaces and convert to title case. For example, "HENRY MARTIN " becomes "Henry Martin".
3. Standardise state to one of these codes: NSW, VIC, QLD, WA, SA, TAS, ACT, NT. Remove spaces, use uppercase, and convert full state names to codes. For example, "Victoria" becomes "VIC" and "New South Wales" becomes "NSW".
4. Remove rows where quantity is 0 or less.
5. Remove rows where unit_price is missing.
6. Check each email. A valid email has text, then one @, then a domain that contains a dot. Replace invalid emails with an empty value. Add a column email_valid that is true for valid emails and false for missing or invalid emails. Keep these rows.
7. Convert order_date from MM/DD/YYYY to YYYY-MM-DD.
8. Add a column line_total equal to quantity multiplied by unit_price, rounded to 2 decimal places.

Keep all other columns unchanged.
```

- What the AI did: Built 9 nodes in 1m 23s. One Data Input node (orders_raw) and 8 Custom nodes, one per rule, in the requested order: orders_deduped, orders_clean_name, orders_clean_state, orders_valid_qty, orders_valid_price, orders_email_checked, orders_date_converted, orders_cleaned. Each Custom node contains AI-written Python (pandas) code. Some nodes check that required columns exist and raise an error if they are missing (for example, the line_total node checks for quantity and unit_price).
- Screenshots:
  - evidence/prompt1-canvas.png
  - evidence/prompt1-ai-reply.png
  - evidence/prompt1-line-total-code.png

## Manual run 1 (baseline input, before scheduling)

- Date (AEDT): 11 Oct 2026
- Started: 11:21:54 AM
- Finished: 11:22:03 AM (about 9 seconds)
- Logs: 8 transformations applied, 0 warnings, 0 errors
- Output: outputs/manual-run-1.csv (176 rows, 9 columns)
- Validation: 14 passed, 1 failed
- Failed check: "State uses the 8 codes only". 3 rows (orders 1080, 1184, 1058) had an empty state. All 3 were originally "Western Australia".
- Root cause (from the AI-generated code in the state node): the code removes all spaces and converts to uppercase before looking up the value, so "Western Australia" becomes "WESTERNAUSTRALIA". The lookup list contains "WESTERN AUSTRALIA" (with a space, which can never match) and "WESTAUSTRALIA" (a typo), but not "WESTERNAUSTRALIA". The code uses `.map()`, which silently replaces any value not in the list with an empty value. Rhombus reported no warning or error.
- Contributing factor: the prompt said "Remove spaces", which the AI took to mean removing all spaces, not only leading and trailing ones.
- Screenshots:
  - evidence/run1-preview.png
  - evidence/run1-logs.png
  - evidence/run1-state-node-code.png

## Prompt 2: Fix the state standardisation step

- Date and time (AEDT): 11 Oct 2026, about 1:54 PM 
- Mode: Pipeline
- Reason: Fix the "Western Australia" issue found in manual run 1.
- Prompt:

```text
In the step that standardises state, rows with "Western Australia" end up with an empty state. They should become "WA". Fix this step so that every full state name maps to its code. If a value cannot be mapped, keep the original value instead of replacing it with an empty value. Do not change any other step.
```

- What the AI did: Worked for 11s and replied that the compile succeeded and orders_clean_state was patched. Checking the node showed that only the node's prompt was updated (it now maps "Western Australia" to "WA" and says to keep unmatched values). The node's code was unchanged: it still had "WESTAUSTRALIA" and still used .map() without keeping unmatched values.
- Credits: 34 before, 29 after (5 credits)

## Manual run 2 (after prompt 2)

- Date (AEDT): 11 Oct 2026
- Started: 01:57:10 PM
- Finished: 01:57:17 PM (about 7 seconds)
- Logs: 8 transformations applied, 0 warnings, 0 errors
- Output: outputs/manual-run-2.csv
- Validation: 14 passed, 1 failed. The same 3 rows still had an empty state. The fix reported by the chatbot did not take effect.
- Determinism check: md5sum of manual-run-1.csv and manual-run-2.csv are identical (037203a69c90fdd322aaf36909c6c9e0). Same input and same code gave byte-identical output, which also confirms the reported fix had no effect.

## Regenerate with feedback (state node)

- Date (AEDT): 11 Oct 2026
- How: clicked the state node, then Transform, Edit Prompt, Regenerate Code. This opens a "Regenerate With Feedback" window, and the button stays disabled until feedback is entered.
- Feedback entered:

```text
The current code does not follow the prompt. "Western Australia" still becomes an empty value, because the code removes all spaces before the lookup and the lookup list has "WESTAUSTRALIA" instead of "WESTERNAUSTRALIA". Regenerate the code so it follows the prompt: every full state name maps to its code, and any value that cannot be mapped keeps its original value instead of becoming empty.
```

- Credits: 29 before, 29 after (no credits used)
- Result: the new code trims only leading and trailing spaces, uses a consistent lookup list that includes "WESTERN AUSTRALIA", and keeps unmatched values with `.fillna()`.
- Note: Regenerate Code started a full pipeline run automatically, without pressing play.
- Screenshot: evidence/regenerate-state-node-code.png

## Automatic run after Regenerate Code (output not saved)

- Date (AEDT): 11 Oct 2026
- Started: 03:29:01 PM
- Finished: 03:29:21 PM (about 20 seconds)
- Logs: 8 transformations applied, 0 warnings, 0 errors
- Note: this run started automatically after Regenerate Code. Its output was not downloaded.

## Manual run 3 (after Regenerate Code)

- Date (AEDT): 11 Oct 2026
- Started: 03:30:52 PM
- Finished: 03:31:00 PM (about 8 seconds)
- Logs: 8 transformations applied, 0 warnings, 0 errors
- Output: outputs/manual-run-3.csv
- Validation: 15 passed, 0 failed
- Comparison with manual run 2: same shape (176 x 9). Exactly 3 cells changed, all in the state column: orders 1080, 1184 and 1058 changed from empty to WA. No other cells changed.

## GCS destination setup

- Date (AEDT): 11 Oct 2026
- Added a Data Output node by hand and connected it to the last Custom node. This is configuration, not a data transformation, and saved 5 AI credits.
- Created a Google Cloud Storage destination: bucket khf-rhombus-output (us-central1), service account rhombus-destination with a custom role containing only storage.objects.create and storage.objects.delete, granted on the bucket only.
- Verification succeeded with only those 2 permissions. The in-app dialog lists storage.buckets.get, storage.objects.create, storage.objects.get and storage.objects.list, and says they are typically granted by Storage Admin. The Rhombus docs list only create (plus delete recommended) and advise against Storage Admin. The docs were correct.
- The new destination was not selected automatically. Export format CSV, custom filename orders_cleaned.
- Output file names end with a timestamp in milliseconds (for example orders_cleaned_1791696510449.csv), which is not a readable date.

## Determinism check (baseline input, fixed pipeline)

- Outputs compared: outputs/manual-run-3.csv (downloaded from Rhombus), outputs/gcs-run-a.csv (RhombusAI_output_1791696488611.csv from GCS) and outputs/gcs-run-b.csv (orders_cleaned_1791696510449.csv from GCS)
- md5sum: all three identical (741c5d0e2abdf7b52010b1bdc62475d1)
- Validation of the GCS output: 15 passed, 0 failed