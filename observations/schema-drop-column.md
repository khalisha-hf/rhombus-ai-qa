# Schema drift: drop a column

**Severity:** High. The pipeline itself stops safely, which is good, but the logs give mixed signals and the chatbot claims a fix it did not make.

## Summary
The `email` column was removed from the input. Rhombus stopped at the email step with a clear message, and nothing reached GCS. But the logs also said "completed successfully", the schedule kept re-running the broken data every 15 minutes, and the chatbot gave the wrong diagnosis and said it had fixed the node when the code had not changed at all.

## Test input
| Item | Value |
|---|---|
| File | `datasets/orders_schema_drop_column.csv` |
| Change | `email` column removed |
| md5 / S3 ETag | `fd7085af85cc4fd8dec993db1fdeb2c1` |

Note: my first upload attempt did not actually reach S3 (the ETag still showed the add-column file). The md5/ETag check caught this before I recorded any result.

## Expected (written before the run)
The email step fails because its code needs an `email` column. Nothing new reaches GCS.

## What happened
1. **13:59:05:** manual run. It failed at **13:59:13** at the step `orders_email_checked`:
   *"LLM execution failed (code_sha=33462c180a52): Column 'email' does not exist in target_df!"*, followed by a dump of the generated code.
2. At the **same second**, the Logs also showed *"Pipeline execution completed successfully."*
3. The steps after the email step turned red, as if they had failed too, but they never ran.
4. No new file appeared in GCS.
5. The scheduled runs at **14:00, 14:15 and 14:30** all ran with the same data and all failed. I received a failure email.

## Answers to the test questions
| Question | Answer |
|---|---|
| Does it stop, warn or carry on? | Stops at the email step. |
| What reaches GCS? | Nothing new. |
| Are the logs clear? | Mixed. The error message itself is clear (it names the missing column, because the AI-written code checks for it on purpose). But a "completed successfully" line appears at the same time, the full generated code is dumped into the message, it says "LLM execution failed" although this step runs fixed code, and Executions only names the failed step as "Custom". |
| Chatbot | Wrong diagnosis, and its fix was not applied (details below). |
| Schedule | Kept running every 15 minutes with the same data, failing each time (#17970, #17971, #17974). Failure emails were sent. |

## Chatbot test
1. Saved the email step's code first: [`email-node-code-before.py`](evidence/email-node-code-before.py).
2. Clicked **Ask Chatbot** on the error and sent its ready-made message as it was (5 credits, 29 left to 24).
3. The chatbot replied: *"Updated the pipeline on the canvas: patched orders_email_checked so it dynamically locates the email column by searching for a column whose name contains "email" (case-insensitive)... This will resolve the "Column 'email' does not exist" error... You can now re-run the pipeline."* It changed the pipeline by itself, with no preview and no confirm step.
4. Re-ran at **14:23:23**. It failed at 14:23:31 with the **same error and the same `code_sha=33462c180a52`**. The code that ran had not changed.
5. Compared the code after the chatbot with my saved copy: **identical** ([`email-node-code-after-chatbot.py`](evidence/email-node-code-after-chatbot.py)).
6. What the chatbot actually changed was the step's **prompt**, which had been empty: [`email-node-prompt-after-chatbot.txt`](evidence/email-node-prompt-after-chatbot.txt). That prompt says: *"If no such column exists, raise a clear error naming the available columns."* So even its own intended fix would still fail on this file.

| Check | Result |
|---|---|
| Diagnosis | **Wrong.** It assumed the column was renamed. It was removed. |
| Fix applied? | **No.** The prompt changed, the code did not (same code_sha, identical code). |
| Would the fix work if applied? | **No.** There is no column containing "email" to find. |
| Honest about it? | **No.** It said "This will resolve the error". |

## Side effects
- After the chatbot's change, clicking the email step showed *"Configuration Required: Please ensure previous nodes are configured"* instead of its code, until a successful run cleared it.
- Some step labels on the canvas changed to internal IDs (like `llm_92ff37d0ec...`), and the step after the email step was also labelled "Validate the ema...".
- I could not set the prompt back to empty: Rhombus says *"Prompt is required"*, even though its own AI Builder created the step with an empty prompt.
- A baseline run afterwards gave exactly the baseline output again (md5 `741c5d0e2abdf7b52010b1bdc62475d1`), so the pipeline's behaviour was not harmed.

## Why it matters
- The stop is the right behaviour. But a "completed successfully" line next to a failure can mislead anyone scanning the logs.
- Re-running the same broken data every 15 minutes sends repeated failure emails without making progress.
- The chatbot is the main problem: a user would trust "This will resolve the error", re-run, fail again, and not know why.

## Suggestions
- Remove the "completed successfully" line when a step fails, and show skipped steps as "skipped", not red.
- Name the failed step in Executions (for example `orders_email_checked`, not "Custom").
- After a failure, pause or back off instead of re-running the same data every slot.
- Chatbot: check the real columns before diagnosing, show a preview of what it will change, and only say "fixed" when the code has actually changed.

## Evidence
The failure, with the "completed successfully" line at the same second and the later steps shown in red:

![Drop-column failure in Logs](evidence/drop-column-error.png)

The scheduled run at 14:00 also failed; the failed step is shown only as "Custom":

![Scheduled run #17970 failed](evidence/drop-column-scheduled-failure.png)

The chatbot's answer, claiming the error is resolved (credits now 24/50):

![Chatbot answer](evidence/drop-column-chatbot.png)

The re-run at 14:23 fails with the same code_sha as the first failure at 13:59 (both in the Logs), right next to the chatbot saying it patched the step:
![Same code_sha after the chatbot](evidence/drop-column-same-sha.png)

Other evidence:
- Code before and after the chatbot: [`email-node-code-before.py`](evidence/email-node-code-before.py), [`email-node-code-after-chatbot.py`](evidence/email-node-code-after-chatbot.py)
- Prompt written by the chatbot: [`email-node-prompt-after-chatbot.txt`](evidence/email-node-prompt-after-chatbot.txt)
- Executions export: [`executions.csv`](evidence/executions.csv) (runs #17970, #17971, #17974)