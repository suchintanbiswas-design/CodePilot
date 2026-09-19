import csv
import math
import os
import sys


def assign_ranks(values):
    """Assign average ranks to handle ties properly."""
    sorted_with_idx = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0] * len(values)
    n = len(values)
    i = 0
    while i < n:
        j = i
        while j < n and sorted_with_idx[j][1] == sorted_with_idx[i][1]:
            j += 1
        avg_rank = sum(range(i + 1, j + 1)) / (j - i)
        for k in range(i, j):
            original_idx = sorted_with_idx[k][0]
            ranks[original_idx] = avg_rank
        i = j
    return ranks


def pearson_correlation(x, y):
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = math.sqrt(
        sum((x[i] - mean_x) ** 2 for i in range(n))
        * sum((y[i] - mean_y) ** 2 for i in range(n))
    )

    if denominator == 0:
        return 0.0
    return numerator / denominator


def t_distribution_tail_probability(t, df):
    """Simple normal approximation for p-value (since N=20 is okayish, but we'll use a better approximation if possible).
    Using simple numeric integration for Student's T CDF is easy enough for our purpose.
    """

    # We will use simple numeric integration for the PDF
    def pdf(x):
        return (
            math.gamma((df + 1) / 2)
            / (math.sqrt(df * math.pi) * math.gamma(df / 2))
            * (1 + (x**2) / df) ** (-(df + 1) / 2)
        )

    # Integrate from t to infinity
    # Or just use normal approx since this is just for a rough p-value report
    # Actually, let's just use normal approximation for simplicity if needed, or exact numeric integration
    step = 0.001
    x = abs(t)
    area = 0.0
    while x < abs(t) + 20:  # 20 std devs is enough
        area += pdf(x) * step
        x += step
    return area * 2  # two tailed


def main():
    codepilot_csv = os.path.join("validation", "results", "codepilot_results.csv")
    radon_csv = os.path.join("validation", "results", "radon_results.csv")

    cp_data = {}
    with open(codepilot_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (
                "sample" in row["file"]
                and "model_properties" not in row["file"]
                and row["file"].startswith("sample")
            ):
                # Make sure it's sample01.py to sample20.py
                fname = os.path.basename(row["file"])
                if fname.startswith("sample") and len(fname) == 11:
                    cp_data[fname] = row

    radon_data = {}
    with open(radon_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = os.path.basename(row["file"])
            radon_data[fname] = row

    # Validate
    cp_files = set(cp_data.keys())
    radon_files = set(radon_data.keys())

    if len(cp_files) != 20 or len(radon_files) != 20:
        print("ERROR: Not exactly 20 primary benchmark files.")
        print(f"CodePilot: {len(cp_files)}, Radon: {len(radon_files)}")
        sys.exit(1)

    if cp_files != radon_files:
        print("ERROR: Filenames do not match.")
        sys.exit(1)

    # Join
    joined = []
    for f in sorted(cp_files):
        joined.append(
            {
                "file": f,
                "loc": (
                    int(cp_data[f]["loc"])
                    if "loc" in cp_data[f]
                    else int(radon_data[f]["loc"])
                ),
                "codepilot_maintainability": float(cp_data[f]["maintainability_score"]),
                "radon_maintainability_index": float(
                    radon_data[f]["maintainability_index"]
                ),
                "issue_count": int(cp_data[f].get("issue_count", 0)),
                "complexity": float(cp_data[f].get("average_complexity", 0.0)),
            }
        )

    # We want higher maintainability score to be "better", same for Radon MI.
    # We rank them such that higher score gets a HIGHER rank value (or lower rank number, e.g. Rank 1 is best)
    # Let's assign ranks (1 = lowest score). To get 1 = best score, we invert values.
    # Actually, standard Spearman correlates the raw values, so assigning 1 = lowest is mathematically identical for rho.
    cp_scores = [x["codepilot_maintainability"] for x in joined]
    radon_scores = [x["radon_maintainability_index"] for x in joined]

    cp_ranks = assign_ranks(cp_scores)
    radon_ranks = assign_ranks(radon_scores)

    # We want rank 1 to be the BEST (highest score).
    # Current assign_ranks gives 1 to the lowest. So we invert it: N - rank + 1
    N = len(joined)
    cp_ranks = [N - r + 1 for r in cp_ranks]
    radon_ranks = [N - r + 1 for r in radon_ranks]

    for i in range(N):
        joined[i]["codepilot_rank"] = cp_ranks[i]
        joined[i]["radon_rank"] = radon_ranks[i]
        joined[i]["rank_difference"] = cp_ranks[i] - radon_ranks[i]
        joined[i]["abs_rank_difference"] = abs(cp_ranks[i] - radon_ranks[i])

    # Calculate Rho
    # Since we inverted both, the pearson correlation is identical.
    rho = pearson_correlation(cp_ranks, radon_ranks)

    # P-value
    if abs(rho) == 1.0:
        p_val = 0.0
    else:
        t = rho * math.sqrt((N - 2) / (1 - rho**2))
        p_val = t_distribution_tail_probability(t, N - 2)

    # Write output
    out_csv = os.path.join("validation", "results", "maintainability_comparison.csv")
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "loc",
                "codepilot_maintainability",
                "radon_maintainability_index",
                "codepilot_rank",
                "radon_rank",
                "rank_difference",
            ],
        )
        writer.writeheader()
        for x in joined:
            writer.writerow(
                {
                    "file": x["file"],
                    "loc": x["loc"],
                    "codepilot_maintainability": x["codepilot_maintainability"],
                    "radon_maintainability_index": x["radon_maintainability_index"],
                    "codepilot_rank": x["codepilot_rank"],
                    "radon_rank": x["radon_rank"],
                    "rank_difference": x["rank_difference"],
                }
            )

    print(f"Joined datasets. Wrote {out_csv}")
    print(f"N = {N}")
    print(f"Spearman rho = {rho:.6f}")
    print(f"p-value (approx) = {p_val:.6e}")

    # Ranking analysis
    agree_exact = sum(1 for x in joined if x["abs_rank_difference"] == 0)
    mean_abs_diff = sum(x["abs_rank_difference"] for x in joined) / N
    max_diff_item = max(joined, key=lambda x: x["abs_rank_difference"])

    print(f"Exact rank agreements: {agree_exact}")
    print(f"Mean absolute rank difference: {mean_abs_diff:.2f}")
    print(
        f"Largest rank disagreement: {max_diff_item['file']} (diff={max_diff_item['abs_rank_difference']})"
    )

    # Top 5 and Bottom 5
    print("\n--- CodePilot Top 5 ---")
    for x in sorted(joined, key=lambda x: x["codepilot_rank"])[:5]:
        print(
            f"  Rank {x['codepilot_rank']}: {x['file']} (Score {x['codepilot_maintainability']})"
        )

    print("\n--- CodePilot Bottom 5 ---")
    for x in sorted(joined, key=lambda x: x["codepilot_rank"])[-5:]:
        print(
            f"  Rank {x['codepilot_rank']}: {x['file']} (Score {x['codepilot_maintainability']})"
        )

    print("\n--- Radon Top 5 ---")
    for x in sorted(joined, key=lambda x: x["radon_rank"])[:5]:
        print(
            f"  Rank {x['radon_rank']}: {x['file']} (MI {x['radon_maintainability_index']:.2f})"
        )

    print("\n--- Radon Bottom 5 ---")
    for x in sorted(joined, key=lambda x: x["radon_rank"])[-5:]:
        print(
            f"  Rank {x['radon_rank']}: {x['file']} (MI {x['radon_maintainability_index']:.2f})"
        )

    print("\n--- Top Disagreements ---")
    for x in sorted(joined, key=lambda x: x["abs_rank_difference"], reverse=True)[:5]:
        print(
            f"{x['file']}: diff={x['abs_rank_difference']} "
            f"(CP Rank {x['codepilot_rank']} vs Radon Rank {x['radon_rank']}) "
            f"CP Score={x['codepilot_maintainability']} Radon MI={x['radon_maintainability_index']:.2f} "
            f"LOC={x['loc']} Issues={x['issue_count']} AvgComplx={x['complexity']}"
        )


if __name__ == "__main__":
    main()
