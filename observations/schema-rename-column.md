# Schema drift: rename a column

**Severity:** High. The pipeline stops, but with a cryptic message, and the chatbot again claims a fix it did not make.

## Summary
`customer_name` was renamed to `name`. Rhombus stopped at the name-cleaning step, but the only error text was `'customer_name'`. The scheduled run failed the same way. The chatbot said it had fixed the step; the re-run failed with the same code.

## Test input
| Item | Value |
|---|---|
| File | `datasets/orders_schema_rename_column.csv` |
| Change | Column `customer_name` renamed to `name` |
| md5 (dataset file) | `a65da4aa324d626bbc87c12525730f5f` |

## Expected (written before the run)
The name-cleaning step fails. Its code uses `customer_name` directly and, unlike the email step, does not check that the column exists first ([`names-node-code-before.py`](evidence/names-node-code-before.py)). So the error will probably be a raw Python error, not a clear message.

## What happened
1. **14:44:41:** manual run. It failed at **14:44:46** at the step `orders_clean_name`:
   *"LLM execution failed (code_sha=90c4a09a9b69): 'customer_name' --- Generated code..."*
2. The same "Pipeline execution completed successfully" line appeared at the same second, and the later steps turned red.
3. **14:45:12:** the scheduled run #17978 failed the same way (5.1 s, 2 steps completed).
4. Nothing new reached GCS.

## Answers to the test questions
| Question | Answer |
|---|---|
| Does it stop, warn or carry on? | Stops at the name-cleaning step. |
| What reaches GCS? | Nothing new. |
| Are the logs clear? | **No.** The only error text is `'customer_name'`. It does not say the column is missing or what columns the file has. A non-technical user would not know a column was renamed. |
| Chatbot | Its fix was not applied (details below). |
| Schedule | The next scheduled run (14:45) failed the same way. |

## Error messages compared
Both steps were written by the same AI builder, but only one explains the problem:

| Case | Step | Error text |
|---|---|---|
| Drop column | `orders_email_checked` | *"Column 'email' does not exist in target_df!"* (clear) |
| Rename column | `orders_clean_name` | *"'customer_name'"* (cryptic) |

## Chatbot test
1. Saved the step's code first: [`names-node-code-before.py`](evidence/names-node-code-before.py).
2. Clicked **Ask Chatbot** and sent its ready-made message as it was (5 credits, 24 left to 19).
3. The chatbot replied that it had *"patched orders_clean_name to dynamically locate the customer name column (by searching for a column whose name contains both "customer" and "name", case-insensitively)... This resolves the 'customer_name' key error. You can re-run the pipeline now."*
4. After the change, the step showed *"Configuration Required"* instead of its code, and its canvas label changed to "Clean the custo...".
5. Re-ran at **14:49:20**. It failed at 14:49:26 with the **same error and the same `code_sha=90c4a09a9b69`**. The code that ran had not changed.

| Check | Result |
|---|---|
| Diagnosis | **Partly right.** It saw a missing `customer_name` column. |
| Fix applied? | **No.** Same code_sha, same error. |
| Would the fix work if applied? | **Unclear, and risky.** The rule in its message ("contains both customer and name") cannot match `name`. The prompt it wrote also says *"or whose name is closest to 'customer_name'"*, which might pick `name`, but guessing columns by "closest name" could also pick the wrong column without telling anyone. I did not apply it with Regenerate Code. |
| Honest about it? | **No.** It said "This resolves the error". |

This is the second case (after drop column) where the chatbot said it fixed a step while the code stayed the same.

## Why it matters
- A cryptic error makes a simple problem (a renamed column) slow to fix.
- The chatbot's false "resolved" message wastes the user's time and credits.

## Suggestions
- Make every AI-written step check its columns first and raise a clear message, like the email step does.
- Include the file's actual column names in error messages.
- Chatbot: only say "fixed" when the code has changed, and avoid "closest name" guesses without asking the user.

## Evidence
The failure in Logs at 14:44:46: the only error text is `'customer_name'`, with "completed successfully" right below it. On the right, the step's code uses `customer_name` directly, with no check:

![Rename failure in Logs](evidence/rename-error.png)

The chatbot's answer, claiming the error is resolved (worked for 11 s, credits now 19/50):

![Chatbot answer for rename](evidence/rename-chatbot.png)

The re-run at 14:49 fails with the same code_sha as the first failure at 14:44 (both in the Logs). On the right, the step the chatbot edited now shows "Configuration Required" instead of its code:

![Same code_sha after the chatbot](evidence/rename-same-sha.png)

Other evidence:
- Code before the chatbot: [`names-node-code-before.py`](evidence/names-node-code-before.py)
- Executions export: [`executions.csv`](evidence/executions.csv) (run #17978)