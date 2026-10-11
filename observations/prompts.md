# AI builder prompt log

Every pipeline step was built with the Rhombus AI builder only. No nodes were added or edited by hand.

## Prompt 1: Build the cleaning pipeline

- Date and time (AEDT): [date and time you sent the prompt]
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

- Date (AEDT): [date of the run]
- Started: 11:21:54
- Finished: 11:22:03 (about 9 seconds)
- Logs: 8 transformations applied, 0 warnings, 0 errors
- Output: downloaded as outputs/manual-run-1.csv (176 rows, 9 columns)
- Validation: 14 passed, 1 failed
- Failed check: "State uses the 8 codes only". 3 rows (orders 1080, 1184, 1058) had an empty state. All 3 were originally "Western Australia".
- Root cause (from the AI-generated code in the state node): the code removes all spaces and converts to uppercase before looking up the value, so "Western Australia" becomes "WESTERNAUSTRALIA". The lookup list contains "WESTERN AUSTRALIA" (with a space, which can never match) and "WESTAUSTRALIA" (a typo), but not "WESTERNAUSTRALIA". The code uses `.map()`, which silently replaces any value not in the list with an empty value. Rhombus reported no warning or error.
- Screenshots:
  - evidence/run1-preview.png
  - evidence/run1-logs.png
  - evidence/run1-state-node-code.png

## Prompt 2: Fix the state standardisation step

- Date and time (AEDT): [fill in]
- Mode: Pipeline
- Reason: Fix the "Western Australia" issue found in manual run 1.
- Credits: [before] before, [after] after
- Prompt:

```text
In the step that standardises state, rows with "Western Australia" end up with an empty state. They should become "WA". Fix this step so that every full state name maps to its code. If a value cannot be mapped, keep the original value instead of replacing it with an empty value. Do not change any other step.
```

- What the AI did: