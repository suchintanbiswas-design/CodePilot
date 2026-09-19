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
    denom_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    denom_y = sum((y[i] - mean_y) ** 2 for i in range(n))

    denominator = math.sqrt(denom_x * denom_y)

    if denominator == 0:
        return 0.0
    return numerator / denominator


def t_distribution_tail_probability(t, df):
    # Numeric integration for normal approximation / tail calculation
    step = 0.001
    x = abs(t)
    area = 0.0

    # Accurate enough normal approx for t-distribution area
    def pdf(val):
        return (
            math.gamma((df + 1) / 2)
            / (math.sqrt(df * math.pi) * math.gamma(df / 2))
            * (1 + (val**2) / df) ** (-(df + 1) / 2)
        )

    while x < abs(t) + 20:
        area += pdf(x) * step
        x += step
    return area * 2


def main():
    ground_truth_csv = os.path.join("validation", "benchmark", "ground_truth.csv")
    codepilot_csv = os.path.join("validation", "results", "codepilot_results.csv")

    # 1. Verify the ground truth
    gt_map = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

    gt_data = {}
    with open(ground_truth_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = row["file"]
            if fname.startswith("sample") and len(fname) == 11:
                lvl = row["expected_security_level"].lower()
                gt_data[fname] = {
                    "level_str": lvl,
                    "level_num": gt_map.get(lvl, 0),
                    "summary": row["known_issue_summary"],
                }

    cp_data = {}
    with open(codepilot_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = os.path.basename(row["file"])
            if fname.startswith("sample") and len(fname) == 11:
                cp_data[fname] = row

    # Validate
    gt_files = set(gt_data.keys())
    cp_files = set(cp_data.keys())

    if len(gt_files) != 20 or len(cp_files) != 20:
        print(f"ERROR: Expected 20 files. GT: {len(gt_files)}, CP: {len(cp_files)}")
        sys.exit(1)

    joined = []
    for f in sorted(gt_files):
        joined.append(
            {
                "file": f,
                "expected_security_level_str": gt_data[f]["level_str"],
                "expected_security_level": gt_data[f]["level_num"],
                "codepilot_security_score": float(cp_data[f]["security_score"]),
                "issue_count": int(cp_data[f].get("issue_count", 0)),
                "summary": gt_data[f]["summary"],
            }
        )

    # Rank them
    # For GT: 0 = none, 4 = critical. The higher the number, the more severe.
    # For CP Score: The higher the number, the BETTER the code.
    # Standard Spearman will just assign ranks.
    # So if we rank GT (low to high), 4 gets the highest rank value.
    # If we rank CP Score (low to high), 100.0 gets the highest rank value.
    # We expect a negative correlation: higher GT severity -> lower CP score.
    gt_values = [x["expected_security_level"] for x in joined]
    cp_values = [x["codepilot_security_score"] for x in joined]

    gt_ranks = assign_ranks(gt_values)
    cp_ranks = assign_ranks(cp_values)

    N = len(joined)

    for i in range(N):
        joined[i]["expected_security_rank"] = gt_ranks[i]
        joined[i]["codepilot_security_rank"] = cp_ranks[i]
        # Rank difference: to be meaningful for comparison, we usually compare the same direction.
        # i.e., Rank 1 = most severe, vs Rank 1 = worst score.
        # Currently, higher rank = higher value.
        # For GT: highest rank = critical. For CP: highest rank = 100.0 (best).
        # Let's invert GT ranks so 1 = most severe, and CP ranks so 1 = lowest score.
        joined[i]["expected_security_rank_aligned"] = N - gt_ranks[i] + 1
        joined[i]["codepilot_security_rank_aligned"] = cp_ranks[
            i
        ]  # already lower value = lower score = lower rank number, wait.
        # Actually, let's just stick to the literal ranks of the values for the CSV.
        joined[i]["rank_difference"] = gt_ranks[i] - cp_ranks[i]
        joined[i]["abs_rank_difference"] = abs(gt_ranks[i] - cp_ranks[i])

    # Calculate Rho
    rho = pearson_correlation(gt_ranks, cp_ranks)

    # P-value
    if abs(rho) == 1.0:
        p_val = 0.0
    else:
        t = rho * math.sqrt((N - 2) / (1 - rho**2))
        p_val = t_distribution_tail_probability(t, N - 2)

    # Write output CSV
    out_csv = os.path.join("validation", "results", "security_comparison.csv")
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "expected_security_level",
                "expected_security_rank",
                "codepilot_security_score",
                "codepilot_security_rank",
                "rank_difference",
            ],
        )
        writer.writeheader()
        for x in joined:
            writer.writerow(
                {
                    "file": x["file"],
                    "expected_security_level": x["expected_security_level"],
                    "expected_security_rank": x["expected_security_rank"],
                    "codepilot_security_score": x["codepilot_security_score"],
                    "codepilot_security_rank": x["codepilot_security_rank"],
                    "rank_difference": x["rank_difference"],
                }
            )

    print(f"Wrote {out_csv}")
    print(f"N = {N}")
    print(f"Spearman rho = {rho:.6f}")
    print(f"p-value (approx) = {p_val:.6e}")

    mean_abs_diff = sum(x["abs_rank_difference"] for x in joined) / N
    print(f"Mean absolute rank difference: {mean_abs_diff:.2f}")

    print("\n--- Highest Severity Benchmark Cases (Ground Truth) ---")
    for x in sorted(joined, key=lambda x: x["expected_security_rank"], reverse=True)[
        :5
    ]:
        print(
            f"{x['file']}: {x['expected_security_level_str']} (Rank {x['expected_security_rank']})"
        )

    print("\n--- Lowest Severity Benchmark Cases (Ground Truth) ---")
    # lowest severity is "none". Many files tie for this.
    lowest_rank = min(x["expected_security_rank"] for x in joined)
    for x in [j for j in joined if j["expected_security_rank"] == lowest_rank]:
        print(
            f"{x['file']}: {x['expected_security_level_str']} (Rank {x['expected_security_rank']})"
        )

    print("\n--- Top Disagreements ---")
    # Note: Because the relationship is inverse, perfect alignment means GT Rank 20 maps to CP Rank 1.
    # Therefore, we should calculate an aligned difference to see true disagreements.
    # Let aligned_CP_rank = (N + 1) - CP_rank. (So rank 1 lowest score maps to rank 20 highest severity)
    for x in joined:
        aligned_cp = (N + 1) - x["codepilot_security_rank"]
        x["true_disagreement"] = abs(x["expected_security_rank"] - aligned_cp)

    for x in sorted(joined, key=lambda x: x["true_disagreement"], reverse=True)[:5]:
        print(
            f"{x['file']}: Diff={x['true_disagreement']} | GT={x['expected_security_level_str']} (Rank {x['expected_security_rank']}) vs "
            f"CP Score={x['codepilot_security_score']} (Aligned Rank {x['codepilot_security_rank']})"
        )
        print(f"   Summary: {x['summary']}")


if __name__ == "__main__":
    main()
