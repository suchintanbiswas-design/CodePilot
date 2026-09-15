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
    denom_x = sum((x[i] - mean_x)**2 for i in range(n))
    denom_y = sum((y[i] - mean_y)**2 for i in range(n))
    
    denominator = math.sqrt(denom_x * denom_y)
    
    if denominator == 0:
        return 0.0
    return numerator / denominator

def t_distribution_tail_probability(t, df):
    step = 0.001
    x = abs(t)
    area = 0.0
    
    def pdf(val):
        return math.gamma((df+1)/2) / (math.sqrt(df * math.pi) * math.gamma(df/2)) * (1 + (val**2)/df)**(-(df+1)/2)
    
    while x < abs(t) + 20: 
        area += pdf(x) * step
        x += step
    return area * 2

def main():
    ground_truth_csv = os.path.join("validation", "benchmark", "ground_truth.csv")
    codepilot_csv = os.path.join("validation", "results", "codepilot_results.csv")
    
    gt_map = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    
    gt_data = {}
    with open(ground_truth_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = row["file"]
            if fname.startswith("sample") and len(fname) == 11:
                lvl = row["expected_performance_level"].lower()
                gt_data[fname] = {
                    "level_str": lvl,
                    "level_num": gt_map.get(lvl, 0),
                    "summary": row["known_issue_summary"]
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
        joined.append({
            "file": f,
            "expected_performance_level_str": gt_data[f]["level_str"],
            "expected_performance_level": gt_data[f]["level_num"],
            "codepilot_performance_score": float(cp_data[f]["performance_score"]),
            "issue_count": int(cp_data[f].get("issue_count", 0)),
            "loc": int(cp_data[f].get("loc", 0)),
            "complexity": float(cp_data[f].get("average_complexity", 0.0)),
            "summary": gt_data[f]["summary"]
        })
        
    gt_values = [x["expected_performance_level"] for x in joined]
    cp_values = [x["codepilot_performance_score"] for x in joined]
    
    gt_ranks = assign_ranks(gt_values)
    cp_ranks = assign_ranks(cp_values)
    
    N = len(joined)
    
    for i in range(N):
        joined[i]["expected_performance_rank"] = gt_ranks[i]
        joined[i]["codepilot_performance_rank"] = cp_ranks[i]
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
    out_csv = os.path.join("validation", "results", "performance_comparison.csv")
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "file", "expected_performance_level", "expected_performance_rank",
            "codepilot_performance_score", "codepilot_performance_rank", "rank_difference"
        ])
        writer.writeheader()
        for x in joined:
            writer.writerow({
                "file": x["file"],
                "expected_performance_level": x["expected_performance_level"],
                "expected_performance_rank": x["expected_performance_rank"],
                "codepilot_performance_score": x["codepilot_performance_score"],
                "codepilot_performance_rank": x["codepilot_performance_rank"],
                "rank_difference": x["rank_difference"]
            })
            
    print(f"Wrote {out_csv}")
    print(f"N = {N}")
    print(f"Spearman rho = {rho:.6f}")
    print(f"p-value (approx) = {p_val:.6e}")
    
    mean_abs_diff = sum(x["abs_rank_difference"] for x in joined) / N
    print(f"Mean absolute rank difference: {mean_abs_diff:.2f}")
    
    print("\n--- Highest Severity Benchmark Cases (Ground Truth) ---")
    for x in sorted(joined, key=lambda x: x["expected_performance_rank"], reverse=True)[:5]:
        print(f"{x['file']}: {x['expected_performance_level_str']} (Rank {x['expected_performance_rank']})")

    print("\n--- Lowest Severity Benchmark Cases (Ground Truth) ---")
    lowest_rank = min(x["expected_performance_rank"] for x in joined)
    for x in [j for j in joined if j["expected_performance_rank"] == lowest_rank]:
        print(f"{x['file']}: {x['expected_performance_level_str']} (Rank {x['expected_performance_rank']})")

    print("\n--- Top Disagreements ---")
    # Aligned rank difference to reflect expected inverse correlation:
    # GT Rank N (critical) should correspond to CP Rank 1 (lowest score).
    for x in joined:
        aligned_cp = (N + 1) - x["codepilot_performance_rank"]
        x["true_disagreement"] = abs(x["expected_performance_rank"] - aligned_cp)
        
    for x in sorted(joined, key=lambda x: x["true_disagreement"], reverse=True)[:5]:
        print(f"{x['file']}: Diff={x['true_disagreement']} | GT={x['expected_performance_level_str']} (Rank {x['expected_performance_rank']}) vs "
              f"CP Score={x['codepilot_performance_score']} (Aligned Rank {x['codepilot_performance_rank']})")
        print(f"   LOC: {x['loc']}, Issues: {x['issue_count']}, Complexity: {x['complexity']}")
        print(f"   Summary: {x['summary']}")

if __name__ == "__main__":
    main()
