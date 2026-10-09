# AI builder prompt log

Every pipeline step was built with the Rhombus AI builder only. No nodes were added or edited by hand.

## Prompt 1: Build the cleaning pipeline

- Date and time (AEDT):
- Mode: Pipeline
- Context attached: input/orders.csv
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

- What the AI did:
- Screenshot: evidence/