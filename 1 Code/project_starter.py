"""COMP 262 Team 7 starter: reproducible data audit and optional lexicon baselines.

Run: python project_starter.py
Optional: python project_starter.py --lexicons
Only the Python standard library is needed for the default run.
Dataset: https://nijianmo.github.io/amazon/index.html (Amazon Reviews 2018).
Team: [Your name] and Kekelani Dayo. This is a starter, not a final submission.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "data" / "Gift_Cards_5.json.gz"
LABELS = ("negative", "neutral", "positive")
SEED = 7
SAMPLE_SIZE = 1000
FIELDS = ["source_row", "reviewerID", "asin", "unixReviewTime", "overall", "label", "reviewText",
          "word_count", "text_sha256", "split"]


def normalize_text(text: str) -> str:
    """Comparison key only; keep original casing/punctuation for sentiment scoring."""
    return re.sub(r"\s+", " ", html.unescape(text)).strip().casefold()


def rating_to_label(rating: float) -> str:
    if rating in (1, 2):
        return "negative"
    if rating == 3:
        return "neutral"
    if rating in (4, 5):
        return "positive"
    raise ValueError(f"Expected an integer star rating 1-5, got {rating!r}")


def read_reviews(path: Path) -> list[dict]:
    """Read line-delimited JSON, including gzip files; never execute dataset text."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [dict(json.loads(line), source_row=i)
                for i, line in enumerate(stream, start=1) if line.strip()]


def audit_and_clean(raw: list[dict]) -> tuple[list[dict], dict]:
    """Remove unusable records and normalize exact-text duplicates before splitting.

    Drop every normalized-text group whose sentiment labels conflict. Where labels
    agree, retain its first source record. Short reviews are valid; long reviews are
    flagged for inspection, not automatically deleted. No label balancing is done.
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    missing, invalid = 0, 0
    for record in raw:
        text = record.get("reviewText")
        if not isinstance(text, str) or not text.strip():
            missing += 1
            continue
        try:
            rating = float(record.get("overall"))
            label = rating_to_label(rating)
        except (TypeError, ValueError):
            invalid += 1
            continue
        key = normalize_text(text)
        if not key:
            missing += 1
            continue
        groups[key].append({
            "source_row": record["source_row"],
            "reviewerID": record.get("reviewerID", ""),
            "asin": record.get("asin", ""), "unixReviewTime": record.get("unixReviewTime", ""),
            "overall": int(rating), "label": label,
            "reviewText": text.strip(), "word_count": len(text.split()),
            "text_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
        })
    clean, conflicts, repeats = [], 0, 0
    for records in groups.values():
        if len({r["label"] for r in records}) > 1:
            conflicts += len(records)
        else:
            clean.append(records[0])
            repeats += len(records) - 1
    lengths = sorted(r["word_count"] for r in clean)
    quartiles = statistics.quantiles(lengths, n=4, method="inclusive")
    upper_fence = quartiles[2] + 1.5 * (quartiles[2] - quartiles[0])
    audit = {
        "raw_rows": len(raw), "missing_or_blank_text_rows_removed": missing,
        "invalid_rating_rows_removed": invalid,
        "conflicting_sentiment_text_group_rows_removed": conflicts,
        "duplicate_text_rows_removed": repeats, "clean_rows": len(clean),
        "raw_rating_counts": dict(sorted(Counter(str(r.get("overall")) for r in raw).items())),
        "clean_label_counts": dict(Counter(r["label"] for r in clean)),
        "missing_reviewer_id_raw": sum(not r.get("reviewerID") for r in raw),
        "missing_product_id_raw": sum(not r.get("asin") for r in raw),
        "clean_word_count_min": min(lengths), "clean_word_count_max": max(lengths),
        "clean_word_count_median": statistics.median(lengths),
        "word_count_upper_iqr_fence": upper_fence,
        "long_review_outlier_flags_retained": sum(n > upper_fence for n in lengths),
        "clean_reviews_over_100_words": sum(n > 100 for n in lengths),
        "outlier_policy": "Flag lengths above Q3+1.5*IQR for inspection; retain all valid lengths.",
        "dedup_policy": "Normalized review text; keep first when sentiment agrees; drop conflicting groups.",
        "status": "Starter audit. Team must inspect examples and justify cleaning choices.",
    }
    assert len(raw) == missing + invalid + conflicts + repeats + len(clean)
    return clean, audit


def sample_phase1(clean: list[dict]) -> list[dict]:
    """Seeded random Phase 1 sample, reserved for later comparison, never training."""
    if len(clean) < SAMPLE_SIZE:
        raise ValueError(f"Need {SAMPLE_SIZE} clean reviews, found {len(clean)}")
    sample = [dict(r) for r in random.Random(SEED).sample(clean, SAMPLE_SIZE)]
    for record in sample:
        record["split"] = "reserved_phase1_comparison"
    assert len({r["text_sha256"] for r in sample}) == len(sample)
    return sample


def classification_metrics(true: list[str], predicted: list[str]) -> dict:
    matrix = {actual: {p: 0 for p in LABELS} for actual in LABELS}
    for actual, prediction in zip(true, predicted):
        matrix[actual][prediction] += 1
    per_class = {}
    for label in LABELS:
        tp = matrix[label][label]
        support = sum(matrix[label].values())
        predicted_count = sum(matrix[actual][label] for actual in LABELS)
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1, "support": support}
    return {"n": len(true), "accuracy": sum(a == p for a, p in zip(true, predicted)) / len(true),
            "macro_precision": sum(c["precision"] for c in per_class.values()) / len(LABELS),
            "macro_recall": sum(c["recall"] for c in per_class.values()) / len(LABELS),
            "macro_f1": sum(c["f1"] for c in per_class.values()) / len(LABELS),
            "per_class": per_class, "confusion_matrix_actual_rows_predicted_columns": matrix}


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def export_hf_inputs(clean: list[dict], out: Path) -> None:
    """Prepare real inputs and empty student workspaces; no LLM output is invented."""
    long_reviews = [r for r in clean if r["word_count"] > 100]
    selected = random.Random(SEED).sample(long_reviews, min(10, len(long_reviews)))
    tasks = [dict(r, task_id=i, include_in_report="yes" if i <= 2 else "no",
                  generated_summary="", summary_word_count="", human_quality_notes="")
             for i, r in enumerate(selected, start=1)]
    summary_path = out / "hf_summary_inputs_TEMPLATE.csv"
    if not summary_path.exists():
        write_csv(summary_path, tasks,
                  ["task_id", "source_row", "asin", "word_count", "reviewText", "include_in_report",
                   "generated_summary", "summary_word_count", "human_quality_notes"])
    question = next((r for r in clean if "?" in r["reviewText"]), None)
    response_path = out / "hf_service_response_TEMPLATE.csv"
    if question and not response_path.exists():
        write_csv(response_path, [dict(question,
                  generated_response="", human_grounding_check="Confirm this review contains a real question.")],
                  ["source_row", "asin", "reviewText", "generated_response", "human_grounding_check"])


def run_lexicons(sample: list[dict], out: Path) -> bool:
    """Actual baseline code; optional packages needed, no package downloads at runtime."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        from textblob import TextBlob
    except ImportError:
        print("Lexicons skipped: install requirements.txt, then rerun with --lexicons.")
        return False
    vader = SentimentIntensityAnalyzer()
    predictions = []
    for r in sample:
        v = vader.polarity_scores(r["reviewText"])["compound"]
        t = float(TextBlob(r["reviewText"]).sentiment.polarity)
        predictions.append(dict(r, vader_compound=v, textblob_polarity=t,
                                vader_prediction="positive" if v >= .05 else "negative" if v <= -.05 else "neutral",
                                textblob_prediction="positive" if t >= .10 else "negative" if t <= -.10 else "neutral"))
    result = {"status": "Computed baseline outputs; team interpretation and error analysis still needed.",
              "environment": {"python": sys.version.split()[0], "vaderSentiment": version("vaderSentiment"),
                              "textblob": version("textblob"), "nltk": version("nltk")},
              "sample_seed": SEED, "label_order": list(LABELS),
              "ground_truth_note": "Star-derived proxy labels, not human sentiment annotations.",
              "thresholds": {"VADER": "compound >= 0.05 positive; <= -0.05 negative; otherwise neutral",
                             "TextBlob": "Proposed heuristic: polarity >= 0.10 positive; <= -0.10 negative; otherwise neutral"}}
    result["phase1_all_1000"] = {name: classification_metrics([r["label"] for r in predictions],
                                                           [r[f"{name}_prediction"] for r in predictions])
                               for name in ("vader", "textblob")}
    write_csv(out / "lexicon_predictions.csv", predictions,
              FIELDS + ["vader_compound", "textblob_polarity", "vader_prediction", "textblob_prediction"])
    save_json(out / "lexicon_metrics.json", result)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    parser.add_argument("--lexicons", action="store_true", help="Run optional VADER and TextBlob baselines")
    args = parser.parse_args()
    if not args.data.is_file():
        parser.error(f"Dataset missing: {args.data}. See data/SOURCE.md.")
    raw = read_reviews(args.data)
    clean, audit = audit_and_clean(raw)
    sample = sample_phase1(clean)
    args.output.mkdir(parents=True, exist_ok=True)
    audit.update({"seed": SEED, "sample_size": len(sample),
                  "sample_label_counts": dict(Counter(r["label"] for r in sample)),
                  "phase2_split_status": "TODO: full-category >=2000, 70/30 stratified by star rating. See phase2_kekelani.py.",
                  "phase1_role": "Reserve all original 1000 as a common evaluation subset; exclude all from Phase 2 training.",
                  "archive_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest()})
    save_json(args.output / "data_audit.json", audit)
    write_csv(args.output / "reviews_clean.csv", clean, FIELDS[:-1])
    write_csv(args.output / "reviews_sample_1000.csv", sample, FIELDS)
    export_hf_inputs(clean, args.output)
    if args.lexicons:
        run_lexicons(sample, args.output)
    print(f"Loaded {len(raw):,}; clean {len(clean):,}; random sample {len(sample):,} (seed {SEED}).")
    print(f"Sample labels: {audit['sample_label_counts']}")
    print(f"Saved audit, reserved comparison sample, and empty HF workspaces in: {args.output}")
    print("NEXT: complete phase2_kekelani.py and phase2_local_hf.py; add evidence to report/slides.")


if __name__ == "__main__":
    main()
