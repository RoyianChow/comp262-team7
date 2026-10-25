"""Team 7 Phase 2 workspace -- owner: Kekelani Dayo (editable).

This file is intentionally unfinished. It contains no invented ML scores.
Run project_starter.py first. The local FULL category archive is data/Gift_Cards.json.gz.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def train_and_compare_models():
    """TODO KEKELANI: implement and explain both classifiers.

    1. Load the FULL category archive, audit/clean it, and create a random sample
       of at least 2,000 reviews. Proposed team size: 5,000, with exact 3,500/1,500
       train/test allocation (70/30), stratified by original star rating, seed7.
       Reserve the original Phase1 1,000 inside the 1,500 test rows to allow the
       required direct comparison. Match original rows using reviewerID, asin,
       unixReviewTime and text_sha256; verify every match and its rating.
       Derive per-rating train/test quotas, rounding consistently to exact totals.
       Add 500 disjoint test reviews and 3,500 training reviews to meet those quotas.
       Exclude EVERY Phase1 text hash from train, not just its original record.
       Reject/revise the proposed sample plan if a rating lacks enough candidates
       or the reservation cannot fit its test quota; do not silently change70/30.
       Save the final manifest and document how reserving Phase1 affects sampling.
       This constrained sampling/split is a PLAN, not implemented in this starter.
    2. Use only reviewText as X, and label as y. Do not use overall as a feature:
       it defines the target and would leak the answer.
    3. Make two sklearn Pipeline objects:
       TfidfVectorizer + LogisticRegression(max_iter=1000, random_state=7)
       TfidfVectorizer + MultinomialNB.
    4. Fit each pipeline only on training rows. Select any hyperparameters using
       stratified folds within training rows; check the smallest class first.
       TF-IDF vocabulary and IDF must be fitted separately inside each fold.
    5. Evaluate once on the saved 1,500 heldout test rows. Report accuracy, precision,
       recall, class F1, macro F1, and confusion matrix. Compare against the
       original Phase1 1,000 separately: score BOTH ML models on those same rows
       and compare with lexicon_metrics.json phase1_all_1000. Do not compare the
       full 1,500 test score directly to a different 1,000-review lexicon score.
    6. Add majority-class accuracy to show why accuracy alone is misleading.
       Include an error table and discuss the very small minority-class support.
    7. Save real predictions and metrics under outputs/. Write limitations in
       the report, including star-derived labels and residual user/product overlap.

    Suggested imports (after installing requirements_phase2.txt):
      pandas, sklearn.pipeline.Pipeline,
      sklearn.feature_extraction.text.TfidfVectorizer,
      sklearn.linear_model.LogisticRegression,
      sklearn.naive_bayes.MultinomialNB,
      sklearn.metrics.classification_report, confusion_matrix.

    A rating-stratified review split is the required starter design. It does not
    establish generalization to unseen users, products or future reviews; a grouped
    or chronological split can be discussed as a separate robustness extension.
    """
    raise NotImplementedError("Kekelani workspace: implement and validate both ML pipelines.")


def sentiment_aware_recommendation_design():
    """TODO TEAM: implement and evaluate an enhancement, with a worked example.

    Proposed starting design:
      - Read the assigned paper before selecting and justifying the final design.
      - Starting candidate: map sentiment to [-1,1], then calculate per-review
        enhanced_rating = alpha * star + (1-alpha) * (3 + 2 * sentiment).
      - Choose alpha and fit a recommendation model on TRAINING interactions only;
        exclude heldout review interactions from every fitting/aggregation step.
      - Exclude products already seen by the target user; show top-k candidates.
      - Compare the rating-only baseline and the enhanced ranking with suitable
        heldout interactions. Discuss cold start, popularity bias and sparsity.

    This is a design prompt, not a validated recommender result. Implementation,
    an experiment and a written assessment are still required. Discuss sparse
    user/product histories and the limits of the planned sample's evaluation.
    """
    raise NotImplementedError("Team workspace: implement, evaluate and explain the recommendation enhancement.")


if __name__ == "__main__":
    print("Template only. Edit the two functions and integrate them after the starter audit.")
    print(f"Input: {ROOT / 'outputs' / 'reviews_sample_1000.csv'}")
