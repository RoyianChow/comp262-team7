# COMP 262 — Team 7 project starter

Team: **[Your name]** and **Kekelani Dayo**. Replace [Your name] before submission.
Working topic: sentiment analysis and recommendations from Amazon Gift Card reviews.
Status: **editable starting template, not a completed or submission-ready project**.

The small Gift Cards 5-core dataset and full Gift Cards archive are included locally, so the code deliverable
contains real Python files and data. Source links are citations, not substitutes
for the scripts. The 2018 source lists 2,972 reviews for this subset, making it
manageable on an ordinary laptop. Its positive class is dominant; discuss that
limitation and use macro F1 and per-class metrics alongside accuracy.
Phase1 uses the 2,972-row 5-core file; Phase2's unfinished extension uses the
147,194-row full category archive (about11MB compressed).

## Quick start on Windows

Install Python 3.10 or newer. Open PowerShell in this `1 Code` folder.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe project_starter.py
```

That default run requires no third-party packages and no internet connection.
It audits the supplied archive, cleans records, selects 1,000 random reviews with
seed 7, reserves it as the Phase 1 comparison set, and
prepares empty local-model workspaces using real review inputs.

To run the two supplied lexicon baselines:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe project_starter.py --lexicons
```

Installation needs internet access once. VADER uses its bundled lexicon; TextBlob
uses its default Pattern sentiment analyzer. The script does not download corpora
or call an online sentiment service. The included baseline output files were
generated successfully during starter verification. Rerun them in your own
environment, then inspect and interpret results before adding them to the report.
Install `requirements_phase2.txt` when starting the ML extension.

## What is already implemented

- Parse the original local JSON archive and preserve its SHA-256 provenance.
- Inspect missing text/IDs, invalid ratings, normalized-text duplicates and lengths.
- Assign proxy labels: stars 1–2 negative, 3 neutral, 4–5 positive.
- Remove missing/invalid records. For repeated normalized text, keep the first
  review if sentiment agrees and remove groups with conflicting sentiment labels.
  Keep original text for inference; preserve negation, casing and punctuation.
- Flag review-length outliers with the IQR rule and retain them for inspection.
- Export a random 1,000-review sample reserved for common comparison.
- Optional VADER/TextBlob scoring, accuracy, class precision/recall/F1, macro F1
  and confusion matrices on the Phase 1 sample. VADER thresholds are +/-0.05;
  TextBlob thresholds are a proposed +/-0.10 heuristic to justify in the report.
- Select 10 reviews over 100 words and a candidate containing a question mark for
  the unfinished local Hugging Face tasks. No summaries or responses are fabricated.

## Shared work plan — change ownership together

| Work | Proposed lead | Team evidence to add |
|---|---|---|
| Dataset, cleaning, EDA and lexicon methods | [Your name] | EDA charts, inspect flagged examples, method justification, error analysis |
| Phase 2 TF-IDF + logistic regression and Naive Bayes | **Kekelani Dayo** | Implement `phase2_kekelani.py`, evaluate both models, discuss errors |
| Sentiment-enhanced recommendation | Both | Complete design/implementation, baseline comparison and limitations |
| Local Hugging Face tasks | Both | Complete `phase2_local_hf.py`, save 10 summaries and service response |
| Report and presentation | Both | Replace placeholders, add real charts/results, rehearse and review |

The report and slides have dedicated Kekelani work areas. The proposed split is
editable; record actual contributions and review each other's work.

## Fair comparison rules

Phase 2 must use at least 2,000 reviews from the FULL category and a 70/30 split
stratified by star rating. The proposed plan in `phase2_kekelani.py` uses 5,000
reviews (3,500 train / 1,500 test). It reserves all original Phase1 1,000 inside
the test set, fills 500 additional test slots per rating quota, and excludes all
Phase1 text hashes from training. Abort/revise the plan if a rating quota cannot
be met. This plan is a TODO scaffold; the starter does not claim it has been run.

`outputs/reviews_sample_1000.csv` labels every row `reserved_phase1_comparison` in
its `split` column. Keep these rows for direct lexicon-vs-ML comparison. Fit TF-IDF
and all model selection inside Phase2 training data only. Do not use star rating
as an input feature: it defines the target. Do not choose thresholds or settings
from test performance. Compare ML predictions on the original 1,000 to the
`phase1_all_1000` scope in `lexicon_metrics.json`; report Phase2's full1,500 test
metrics separately. Keep minority-class support visible in every results table.

The completed Phase2 split must prevent normalized-text duplicates across train
and test. Reviewer/product overlap may remain: this estimates review classification and does
not establish generalization to unseen users/products or future data. Star labels
are a proxy, not human sentiment ground truth. If the team changes cleaning,
sampling or split design, rerun all methods and replace report/slide evidence.

## Files and outputs

`project_starter.py` is runnable. `phase2_kekelani.py` and `phase2_local_hf.py` are
intentional TODO scaffolds; their main blocks explain next steps without pretending
the models have been implemented. `data/SOURCE.md` records citation/download details.

Generated files under `outputs/`:

- `data_audit.json`: measured row counts, label distributions and outlier audit.
- `reviews_clean.csv`: cleaned review table.
- `reviews_sample_1000.csv`: original Phase1 sample reserved for the common comparison.
- `hf_summary_inputs_TEMPLATE.csv`: real long reviews with empty result columns;
  task IDs 1 and 2 are marked for inclusion in the report.
- `hf_service_response_TEMPLATE.csv`: candidate review with an empty response field.
- `lexicon_predictions.csv` / `lexicon_metrics.json`: created by `--lexicons` only.

These generated inputs contain original review text. Keep citation/provenance with
the working copy. Avoid pasting reviewer identifiers into the public presentation.
Reruns replace generated audit/data/baseline outputs. Existing HF template CSVs are
preserved so your filled result columns remain intact; if you change the input
dataset, archive those workspaces and remove their old copies to regenerate inputs.

## Before final submission

Add the missing implementation and human analysis; create EDA charts; populate all
report/slide placeholders with verified evidence; include exactly ten local-model
summaries exactly 50 words each and the requested first two examples in the report;
document model revision, prompts, settings and hardware; evaluate the service
response; update the contribution record and references; verify the instructor's
current submission directions. Historical dates in the supplied assignment are not
treated as current deadlines.
