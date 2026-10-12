# Rhombus AI QA take-home: a scheduled ETL under schema and semantic drift

I tested Rhombus AI as a scheduled ETL job: a CSV file in Amazon S3, a cleaning pipeline built with the Rhombus AI Builder, output to Google Cloud Storage (GCS), running every 15 minutes. I then sent it 7 kinds of changed ("drifted") input and checked what Rhombus did, what reached GCS, and whether the logs, the chatbot and the schedule helped.

**Demo video:** [add link]

## Top 3 findings

**1. When the data's meaning changes, Rhombus carries on silently and writes wrong data to GCS.**
All three of these runs said "Success" with no warning:
- **Prices in cents:** every price and line total 100 times too big.
- **Dates written day-first:** 64 of 176 orders (36%) got the wrong date. The pipeline expected MM/DD/YYYY, but dates that could not fit that pattern (like `18/09/2026`) were quietly read day-first instead of being flagged. So the format change was hidden, and it happened in Data Input itself, before any cleaning step.
- **An extra column:** 5 duplicate orders slipped through, because the duplicate step compares every column.

When the data's shape breaks (a missing, renamed or retyped column), Rhombus stops. When the meaning changes, it does not notice.

**2. The chatbot says it fixed a step when the code did not change.**
In all three cases where I asked the chatbot to fix a step, it changed only the step's prompt, not its code. In the baseline (a state-mapping bug), the output stayed byte-identical after its fix. In two drift cases (drop column, rename column), it replied that it had "patched" the step and that "this resolves the error", yet both re-runs failed with the **same error and the same `code_sha`**, and the code before and after was identical. Its diagnosis was also wrong for the dropped column (it assumed a rename), it changed the pipeline without a preview or confirm step, and the edited step then showed "Configuration Required" instead of its code.

**3. The schedule does not reliably process a new file on its own.**
Uploading a new file to S3 never triggered a run: the schedule skipped with "unchanged data". It only ran after someone ran the pipeline by hand. Skipped runs leave no record, failed runs are repeated every 15 minutes with the same data, and the same output can be written to GCS twice.

## Results by drift case

| Case | What Rhombus did | What reached GCS | Caught by | Chatbot | Severity |
|---|---|---|---|---|---|
| [Baseline](observations/build-and-run-log.md) | Success | 176 rows, 9 columns, identical across 6 runs | 16 of 16 checks pass | Used once for a state bug: fix not applied ([details](observations/baseline-state-mapping.md)) | n/a |
| [Add column](observations/schema-add-column.md) | Carried on, "Success", no warning | 181 rows: 5 duplicate orders + extra column | `validate.py` (4 fails) and `compare_baseline.py` | Not needed | High |
| [Price in cents](observations/semantic-price-cents.md) | Carried on, "Success", no warning | Prices and line totals 100x | `validate.py` (price range) and `compare_baseline.py` | Not needed | High |
| [Day-first dates](observations/semantic-date-day-first.md) | Carried on, "Success", no warning | 64 of 176 dates swapped | **Only** `compare_baseline.py` (`validate.py` passed 16/16) | Not needed | High |
| [Drop column](observations/schema-drop-column.md) | Stopped, clear message | Nothing | Rhombus | Wrong diagnosis, fix not applied | High |
| [Rename column](observations/schema-rename-column.md) | Stopped, cryptic message (`'customer_name'`) | Nothing | Rhombus | Fix not applied | High |
| [Type change](observations/schema-type-change.md) | Stopped, cryptic Python error | Nothing | Rhombus | Not tested | Medium |
| [All changes at once](observations/schema-combined.md) | Stopped at the first problem only | Nothing | Rhombus (1 of 4 changes reported) | Not tested | Medium |

Cross-case notes:
- [Schedule behaviour](observations/schedule-behaviour.md): skips, repeated failures and duplicate outputs across all cases.
- [S3 setup](observations/setup-s3-connection.md): S3 connection blocked on new-style AWS accounts, with a misleading error.
- [Baseline state mapping](observations/baseline-state-mapping.md): an AI-written step silently blanked "Western Australia" in the first baseline. The chatbot's fix changed only the prompt and the output stayed the same; Regenerate Code fixed it.

## Usability feedback

**Severity scale**
- **High:** blocks the user, or wrong data reaches the output without a warning.
- **Medium:** confusing or misleading, wastes time, but there is a workaround.
- **Low:** small or cosmetic.

| Severity | Issue | Where |
|---|---|---|
| High | S3 connection fails on AWS accounts made with "Sign up for AWS (new)"; the error blames the bucket policy, and the docs do not mention it | [setup-s3-connection.md](observations/setup-s3-connection.md) |
| High | Logs show "Pipeline execution completed successfully" at the same second as every failure | All failing cases |
| Medium | 2 of 3 failing steps give cryptic errors (`'customer_name'`, a Python type error); errors also dump the whole generated code and say "LLM execution failed" for steps that run fixed code | [rename](observations/schema-rename-column.md), [type change](observations/schema-type-change.md) |
| Medium | Executions names a failed step only "Custom" (all 8 steps have that name); canvas labels change between runs to internal IDs or long prompt text, and two steps ended up labelled "Validate the ema..." | [drop column](observations/schema-drop-column.md) |
| Medium | After a chatbot edit, the step shows "Configuration Required: Please ensure previous nodes are configured" instead of its code, although the earlier steps are fine | [drop column](observations/schema-drop-column.md) |
| Medium | A prompt cannot be set back to empty ("Prompt is required"), even though the AI Builder created the step with an empty prompt | [drop column](observations/schema-drop-column.md) |
| Medium | The GCS destination dialog recommends the broad Storage Admin role; the docs (create and delete only) are right, and that is what I used | [build-and-run-log.md](observations/build-and-run-log.md) |
| Medium | A false "Ad Blocker Detected" pop-up, saying third-party integrations may be disabled, appeared in a clean automated browser with no ad blocker | UI tests |
| Medium | The page keeps calling `.../pipeline/healthcare/last-run`, which fails with 403 every time (plus many console errors) | Browser DevTools |
| Medium | API: `page_size=-1` on the executions endpoint returns an HTTP 500 HTML error page instead of a 400 | [api-tests](api-tests/test_rhombus_api.py) |
| Low | Icon buttons (edit, history, alerts, delete) have no accessible names, so screen readers and tests cannot identify them | UI tests |
| Low | "Next run:" is blank right after "Refresh access" or resuming the schedule | [schedule-behaviour.md](observations/schedule-behaviour.md) |
| Low | The S3 file list shows only the modified date, not the time, so you cannot tell which version is loaded | [schedule-behaviour.md](observations/schedule-behaviour.md) |
| Low | Error message and chatbot say "retry", but there is no Retry button ("Connect S3 source") | [setup-s3-connection.md](observations/setup-s3-connection.md) |
| Low | GCS outputs get millisecond timestamps in their names and the content type `application/octet-stream`; downloads get random names | [build-and-run-log.md](observations/build-and-run-log.md) |
| Low | "Regenerate Code" starts a run by itself | [baseline-state-mapping.md](observations/baseline-state-mapping.md) |

**What worked well**
- Output is deterministic: the baseline gave byte-identical output in 6 runs (md5 `741c5d0e2abdf7b52010b1bdc62475d1`), and manual and scheduled runs always matched.
- Failure emails arrive.
- The email step's AI-written code checks for its column and stops with a clear message.
- The Logs panel shows how many rows each step changed.
- Canvas nodes have stable test IDs (`rf__node-...`), which made the UI tests reliable.

## How I tested

**Pipeline under test**
`S3 (khf-rhombus-input/input/orders.csv)` → Data Input → 8 Custom steps built by the AI Builder (one per cleaning rule) → Data Output → `GCS (khf-rhombus-output/orders_cleaned_<timestamp>.csv)`, on a schedule of every 15 minutes (`*/15 * * * *`).

**Method for each drift case**
1. Wrote down the expected result **before** running.
2. Copied the drifted file to `upload/orders.csv`, checked its md5, uploaded it to S3, and checked the S3 ETag matched. (This caught one upload that never reached S3.)
3. Ran the pipeline, recorded the status, failing step and timing, and watched what the schedule did.
4. Downloaded the GCS output and ran both validation scripts.
5. For failures: tested the chatbot (drop and rename cases), saving the step's code first so I could prove what changed.
6. Ran the baseline again at the end: the output was byte-identical to the original.

Because the schedule did not pick up new files by itself (finding 3), most drift runs were started by hand. The schedule's behaviour is recorded separately.

**Data validation** ([`data-validation/`](data-validation/))
- `validate.py` runs 16 checks on an output: columns, row count, duplicates, unique `order_id`, names, state codes, quantity, prices, date format, email rules and `line_total`.
- `compare_baseline.py` matches an output against the baseline output by `order_id` and reports every changed value, missing or extra rows and columns, and repeated ids.
- Both are needed: format checks alone missed the day-first dates (16 of 16 passed); the comparison caught all 64.

**API tests** ([`api-tests/`](api-tests/)): 4 read-only tests with `pytest` and `requests`
- Executions list: status 200, JSON, contains my known run IDs, every run belongs to my project and schedule, newest first.
- No token: refused (401 or 403) and no data returned.
- Fake token: refused (401 or 403) and no data returned.
- `page_size=-1`: should be rejected with a 4xx, but returns 500. Marked as a known bug (`xfail`, strict), so the suite stays green and will flag it if Rhombus fixes it.
- Header values are hidden from test output so tokens cannot leak into logs.

**UI tests** ([`ui-tests/`](ui-tests/)): 4 Playwright tests, read-only, no AI credits used
- The project opens with the full 10-step pipeline.
- The S3 source shows "Connected" with my bucket path.
- The schedule is set to `*/15 * * * *`, with an Active or Inactive status.
- Execution history shows my known runs, with both Success and Failure.
- No fixed sleeps: all waiting uses Playwright's auto-waiting `expect`. The tests use a very wide window because the canvas only draws on-screen steps, and they dismiss the false "Ad Blocker Detected" pop-up automatically.

## Repository layout
| Folder or file | What it holds |
|---|---|
| [`datasets/`](datasets/) | Generator script (seed 42), baseline and drifted CSV files, and a README with the 8 cleaning rules and expected output |
| [`data-validation/`](data-validation/) | `validate.py` and `compare_baseline.py` |
| [`api-tests/`](api-tests/) | API tests (pytest + requests) |
| [`ui-tests/`](ui-tests/) | UI tests (Playwright + pytest) |
| [`observations/`](observations/) | One file per case, plus build log, schedule behaviour and S3 setup |
| [`observations/evidence/`](observations/evidence/) | Screenshots, saved step code, the Executions export and output CSVs |
| `requirements.txt` | Python packages |
| `.env.example` | The two values the API tests need (copy to `.env`) |

## Setup and how to run

**Install** (Git Bash on Windows; on macOS or Linux use `source .venv/bin/activate`):
```
git clone https://github.com/khalisha-hf/rhombus-ai-qa.git
cd rhombus-ai-qa
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python -m playwright install chromium
```

**Datasets:**
```
python datasets/generate_datasets.py
```

**Validate an output:**
```
python data-validation/validate.py observations/evidence/outputs/price_cents_0835.csv
python data-validation/compare_baseline.py observations/evidence/outputs/baseline.csv observations/evidence/outputs/date_day_first.csv
```

**API tests:**
```
cp .env.example .env
```
Fill in the two values from your browser: open Rhombus, press F12, go to Network, click any `api.rhombusai.com` request, and copy the `authorization` and `x-org-id` request headers. Then:
```
pytest api-tests -v
```
Expected: 3 passed, 1 xfailed.

**UI tests:** save a login once (log in, wait for the canvas, then close the browser):
```
python -m playwright codegen --save-storage=secrets/rhombus-auth.json https://rhombusai.com/workflow/5325
pytest ui-tests -v
```
Expected: 4 passed. To watch it run: `pytest ui-tests -v --headed --slowmo 300`.

The project ID, schedule ID and run IDs are set at the top of the test files; change them to point the tests at another project. `.env` and `secrets/` are in `.gitignore`.

**Cloud setup I used**
| Part | Setup |
|---|---|
| S3 | Bucket `khf-rhombus-input` (Sydney), versioning on, Block Public Access on, SSE-S3; Rhombus bucket policy limited to `input/` |
| GCS | Bucket `khf-rhombus-output` (us-central1); a service account with a custom role allowing only `storage.objects.create` and `storage.objects.delete`, on this bucket only |
| Rhombus | Project `etl-amzn-main`; 8 Custom steps built with the AI Builder; Data Output to GCS as CSV; schedule `*/15 * * * *` with failure emails on |

## Limitations
- A small, made-up dataset (200 rows). I did not test speed with large files, or Data Input's fixed 100,000-row sample.
- Most drift cases ran once or twice; the baseline ran 6 times.
- I could not fully work out when the schedule decides to run (see [schedule-behaviour.md](observations/schedule-behaviour.md)).
- The chatbot was tested on 3 fix requests (one baseline bug, two drift cases). I did not use Regenerate Code to apply the prompts it wrote in the drift cases.
- The tests point at my project and need a saved login; the API token expires and must be copied again.
- The false ad-blocker pop-up was seen only in the automated test browser.