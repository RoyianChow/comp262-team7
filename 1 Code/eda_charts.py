"""Chart the cleaned Phase 1 review population using the project audit output.

After running project_starter.py, run python eda_charts.py in the same environment.
Matplotlib is listed in requirements_phase2.txt.
"""

import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, StrMethodFormatter


OUTPUTS = Path(__file__).resolve().parent / "outputs"


def group_counts(values, upper_limits):
    """Return exact bin counts, including a final open-ended interval."""
    counts = [0] * (len(upper_limits) + 1)
    for value in values:
        index = next((i for i, upper in enumerate(upper_limits) if value <= upper), len(upper_limits))
        counts[index] += 1
    return counts


def draw_counts(axis, labels, counts, title, unit, color):
    bars = axis.bar(labels, counts, color=color, width=0.71)
    axis.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=9)
    axis.set_ylabel(unit, fontsize=10)
    axis.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
    axis.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    axis.set_ylim(0, max(counts) * 1.19)
    axis.set_axisbelow(True)
    axis.grid(axis="y", color="#d6e2e8", linewidth=0.8)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_color("#afbdc6")
    axis.tick_params(axis="both", length=0, pad=4, labelsize=9)
    axis.bar_label(bars, labels=[f"{n:,}" for n in counts], fontsize=9, padding=3)


def main():
    with (OUTPUTS / "reviews_clean.csv").open(encoding="utf-8-sig", newline="") as source:
        reviews = list(csv.DictReader(source))
    if not reviews:
        raise ValueError("The cleaned review file is empty.")
    ratings = Counter(int(float(row["overall"])) for row in reviews)
    products = Counter(row["asin"] for row in reviews)
    reviewers = Counter(row["reviewerID"] for row in reviews)
    lengths = [int(row["word_count"]) for row in reviews]
    figure, axes = plt.subplots(2, 2, figsize=(10.5, 6.375), layout="constrained")
    draw_counts(axes[0, 0], ["1", "2", "3", "4", "5"], [ratings[n] for n in range(1, 6)],
                "Star rating", "Reviews", "#1b5069")
    draw_counts(axes[0, 1], ["1–5", "6–10", "11–20", "21–50", "51–100", "101+"],
                group_counts(lengths, [5, 10, 20, 50, 100]),
                "Words per review", "Reviews", "#1b5069")
    draw_counts(axes[1, 0], ["1–5", "6–10", "11–20", "21–40", "41+"],
                group_counts(products.values(), [5, 10, 20, 40]),
                "Reviews per product", "Products", "#2f7f75")
    draw_counts(axes[1, 1], ["1–2", "3–4", "5–6", "7–10", "11+"],
                group_counts(reviewers.values(), [2, 4, 6, 10]),
                "Reviews per reviewer", "Reviewers", "#2f7f75")
    target = OUTPUTS / "eda_distributions.png"
    figure.savefig(target, dpi=160, facecolor="white")
    plt.close(figure)
    print(f"Charted {len(reviews):,} reviews across {len(products)} products and {len(reviewers)} reviewers in {target.name}.")


if __name__ == "__main__":
    main()
