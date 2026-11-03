"""COMP262 Team 7 — Phase 2 sentiment classification (Kekelani Dayo).
"""
from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import csv
import json
import random

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from project_starter import audit_and_clean, read_reviews, normalize_text, rating_to_label, write_csv, save_json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
SEED = 7
TRAIN_SIZE = 3500
TEST_SIZE = 1500
PHASE1_SIZE = 1000
LABELS = ["negative", "neutral", "positive"]


def largest_remainder_quotas(counts, total):
    """Allocate exactly total items proportionally across star ratings."""
    size = sum(counts.values())
    raw = {k: total * v / size for k, v in counts.items()}
    quotas = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: (-(raw[k] - quotas[k]), k))[:total - sum(quotas.values())]:
        quotas[k] += 1
    return quotas


def read_phase1():
    path = OUT / "reviews_sample_1000.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != PHASE1_SIZE:
        raise ValueError(f"Expected {PHASE1_SIZE} Phase 1 rows, found {len(rows)}")
    return rows


def build_split():
    """Create a 70/30 rating-stratified split with Phase 1 reserved for testing."""
    full = ROOT / "data" / "Gift_Cards.json.gz"
    if not full.exists():
        raise FileNotFoundError(f"Missing full category archive: {full}")
    clean, audit = audit_and_clean(read_reviews(full))

    # Some Phase 1 reviews were removed during duplicate cleaning.
    # Check these reviews against the original dataset.
    # Keep the original Phase 1 reviews for a fair comparison.
    raw_full = read_reviews(full)
    raw_keys = set()
    for r in raw_full:
        t = r.get('reviewText')
        if isinstance(t, str) and t.strip():
            digest = hashlib.sha256(normalize_text(t).encode('utf-8')).hexdigest()
            raw_keys.add((str(r.get('reviewerID')), str(r.get('asin')),
                          str(r.get('unixReviewTime')), digest, str(int(r.get('overall')))))
    phase1 = read_phase1()
    reserved, seen = [], set()
    absent_after_cleaning = 0
    clean_hashes = {r['text_sha256'] for r in clean}
    for p in phase1:
        text_key = p['text_sha256']
        key = (p['reviewerID'], p['asin'], p['unixReviewTime'], text_key, p['overall'])
        if key not in raw_keys or rating_to_label(float(p['overall'])) != p['label']:
            raise ValueError(f"Phase 1 record not verifiable in FULL raw archive: {key}")
        if text_key in seen:
            raise ValueError(f"Repeated Phase 1 text hash: {text_key}")
        reserved.append({**p, 'overall': int(p['overall']), 'split': 'test_phase1'})
        absent_after_cleaning += text_key not in clean_hashes
        seen.add(text_key)

    # Split the 5,000 reviews by their original star ratings.
    # Make sure the Phase 1 reviews fit into the test set.
    full_counts = Counter(r['overall'] for r in clean)
    total_quota = largest_remainder_quotas(full_counts, TRAIN_SIZE + TEST_SIZE)
    test_quota = largest_remainder_quotas(total_quota, TEST_SIZE)
    train_quota = {star: total_quota[star] - test_quota[star] for star in total_quota}
    reserved_counts = Counter(r['overall'] for r in reserved)
    for star in sorted(total_quota):
        if reserved_counts[star] > test_quota[star]:
            raise ValueError(f"Infeasible split: rating {star} has {reserved_counts[star]} reserved Phase 1 "
                             f"reviews but only {test_quota[star]} test slots. Revise the sample plan explicitly.")

    # Exclude Phase 1 review text from training to avoid data leakage.
    candidates = defaultdict(list)
    for r in clean:
        if r['text_sha256'] not in seen:
            candidates[r['overall']].append(r)
    rng = random.Random(SEED)
    train, test = [], list(reserved)
    for star in sorted(total_quota):
        needed_test = test_quota[star] - reserved_counts[star]
        needed_train = train_quota[star]
        if len(candidates[star]) < needed_test + needed_train:
            raise ValueError(f"Insufficient rating-{star} candidates for requested quotas")
        selected = rng.sample(candidates[star], needed_test + needed_train)
        test.extend(dict(r, split="test_additional") for r in selected[:needed_test])
        train.extend(dict(r, split="train") for r in selected[needed_test:])
    rng.shuffle(train)
    rng.shuffle(test)
    assert len(train) == TRAIN_SIZE and len(test) == TEST_SIZE
    assert len({r['text_sha256'] for r in train} & {r['text_sha256'] for r in test}) == 0
    assert sum(r['split'] == 'test_phase1' for r in test) == PHASE1_SIZE
    # Save the exact rows used so our results can be reproduced.
    manifest = train + test
    fields = ["source_row", "reviewerID", "asin", "unixReviewTime", "overall", "label",
              "reviewText", "word_count", "text_sha256", "split"]
    write_csv(OUT / "phase2_split_manifest.csv", manifest, fields)
    split_info = {
        "seed": SEED, "full_archive": str(full.relative_to(ROOT)),
        "full_raw_rows": audit['raw_rows'], "full_clean_rows": len(clean),
        "phase1_rows_not_retained_by_full_cleaning": absent_after_cleaning,
        "train_rows": len(train), "test_rows": len(test), "reserved_phase1_test_rows": PHASE1_SIZE,
        "train_rating_counts": dict(sorted(Counter(r['overall'] for r in train).items())),
        "test_rating_counts": dict(sorted(Counter(r['overall'] for r in test).items())),
        "phase1_reserved_rating_counts": dict(sorted(reserved_counts.items())),
        "full_clean_rating_counts": dict(sorted(full_counts.items())),
        "sampling_note": "The 1000 Phase 1 rows are fixed in the test set; the remaining rows are "
                         "sampled within rating quotas. Phase 1 rows are verified in the raw full archive "
                         "even if full-archive deduplication removed them. This is constrained sampling, not an independent "
                         "random stratified split. Identical normalized texts are excluded from training.",
        "audit": audit,
    }
    save_json(OUT / "phase2_split_info.json", split_info)
    return train, test, split_info


def summarize_model(y_true, y_pred):
    report = classification_report(y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0)
    return {
        "accuracy": report['accuracy'], "macro_precision": report['macro avg']['precision'],
        "macro_recall": report['macro avg']['recall'], "macro_f1": report['macro avg']['f1-score'],
        "weighted_f1": report['weighted avg']['f1-score'],
        "per_class": {label: report[label] for label in LABELS},
        "confusion_matrix_labels": LABELS,
        "confusion_matrix_actual_rows_predicted_columns": confusion_matrix(y_true, y_pred, labels=LABELS).tolist(),
    }


def train_and_compare_models():
    OUT.mkdir(parents=True, exist_ok=True)
    train, test, split_info = build_split()
    x_train = [r['reviewText'] for r in train]
    y_train = [r['label'] for r in train]
    x_test = [r['reviewText'] for r in test]
    y_test = [r['label'] for r in test]
    # Use stratified folds so each training fold includes all sentiment classes.
    minimum_class = min(Counter(y_train).values())
    if minimum_class < 2:
        raise ValueError("Too few training samples in a class for stratified cross-validation")
    folds = min(3, minimum_class)
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=SEED)
    # TF-IDF converts the reviews into features for both classifiers.
    models = {
        "logistic_regression": (
            Pipeline([('tfidf', TfidfVectorizer()),
                      ('model', LogisticRegression(max_iter=1000, random_state=SEED))]),
            {'tfidf__ngram_range': [(1, 1), (1, 2)], 'model__C': [0.1, 1, 10],
             'model__class_weight': [None, 'balanced']}),
        "multinomial_naive_bayes": (
            Pipeline([('tfidf', TfidfVectorizer()), ('model', MultinomialNB())]),
            {'tfidf__ngram_range': [(1, 1), (1, 2)], 'model__alpha': [0.1, 1.0],
             'model__fit_prior': [True, False]}),
    }
    results = {"split": split_info, "cv_folds": folds,
               "majority_class_accuracy_test": max(Counter(y_test).values()) / len(y_test),
               "majority_class_accuracy_phase1": max(Counter(r['label'] for r in test if r['split'] == 'test_phase1').values()) / PHASE1_SIZE,
               "models": {}}
    phase1 = [r for r in test if r['split'] == 'test_phase1']
    predictions = []
    # Tune parameters using training data only, then evaluate on held-out reviews.
    for name, (pipeline, parameters) in models.items():
        print(f"Training {name} with {folds}-fold stratified CV...", flush=True)
        search = GridSearchCV(pipeline, parameters, scoring='f1_macro', cv=cv, n_jobs=-1, refit=True)
        search.fit(x_train, y_train)
        test_predictions = search.predict(x_test)
        phase1_predictions = search.predict([r['reviewText'] for r in phase1])
        results['models'][name] = {
            'best_parameters': search.best_params_,
            'training_cv_best_macro_f1': float(search.best_score_),
            'test_1500': summarize_model(y_test, test_predictions),
            'phase1_same_1000': summarize_model([r['label'] for r in phase1], phase1_predictions),
        }
        for r, pred in zip(test, test_predictions):
            predictions.append({'model': name, 'source_row': r['source_row'], 'split': r['split'],
                                'overall': r['overall'], 'actual': r['label'], 'predicted': pred,
                                'correct': r['label'] == pred, 'reviewText': r['reviewText']})
        print(name, 'test macro F1:', round(results['models'][name]['test_1500']['macro_f1'], 4),
              'phase1 macro F1:', round(results['models'][name]['phase1_same_1000']['macro_f1'], 4))

    # Compare both models with Phase 1 results on the same 1,000 reviews.
    baseline_path = OUT / 'lexicon_metrics.json'
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
        results['lexicon_phase1_same_1000'] = baseline.get('phase1_all_1000', {})
    write_csv(OUT / 'phase2_predictions.csv', predictions,
              ['model', 'source_row', 'split', 'overall', 'actual', 'predicted', 'correct', 'reviewText'])
    # Save misclassified reviews to help explain model weaknesses.
    errors = [r for r in predictions if not r['correct']]
    write_csv(OUT / 'phase2_errors.csv', errors[:100],
              ['model', 'source_row', 'split', 'overall', 'actual', 'predicted', 'correct', 'reviewText'])
    results['limitations'] = [
        'Star ratings are proxy sentiment labels; text can disagree with the assigned star.',
        'Positive ratings dominate, so macro F1 and minority-class recall matter more than accuracy alone.',
        'Rating-stratified review split does not prevent overlap of users/products across train and test.',
        'The fixed Phase 1 reservation constrains sampling and is not an independent random holdout.',
    ]
    save_json(OUT / 'phase2_metrics.json', results)
    print('Saved split manifest, metrics, predictions and error examples to outputs/.')
    return results


def sentiment_aware_recommendation_design():
    """Shared team task: implement after selecting a method from the assigned paper."""
    raise NotImplementedError('Team recommender task is separate from Phase 2 ML classification.')


if __name__ == '__main__':
    train_and_compare_models()
