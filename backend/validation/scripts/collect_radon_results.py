import csv
import json
import os
import statistics
import subprocess


def run_radon(command: str) -> dict:
    cmd = f"python -m radon {command} -j validation/benchmark"
    result = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from command: {cmd}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        return {}


def main():
    print("Running radon raw...")
    raw_data = run_radon("raw")
    print("Running radon mi...")
    mi_data = run_radon("mi")
    print("Running radon cc...")
    cc_data = run_radon("cc")

    results = []

    for i in range(1, 21):
        filename = f"sample{i:02d}.py"

        # Match keys since radon output keys might have varying path separators
        raw_key = next(
            (k for k in raw_data.keys() if k.replace("\\", "/").endswith(filename)),
            None,
        )
        mi_key = next(
            (k for k in mi_data.keys() if k.replace("\\", "/").endswith(filename)), None
        )
        cc_key = next(
            (k for k in cc_data.keys() if k.replace("\\", "/").endswith(filename)), None
        )

        if not (raw_key and mi_key and cc_key):
            print(
                f"Missing data for {filename}. Raw: {bool(raw_key)}, MI: {bool(mi_key)}, CC: {bool(cc_key)}"
            )
            continue

        loc = raw_data[raw_key]["loc"]

        mi_value = mi_data[mi_key]["mi"]
        mi_grade = mi_data[mi_key]["rank"]

        cc_list = cc_data[cc_key]

        total_cc = 0
        func_count = 0

        # cc_list might be an error string if radon failed to parse, though tests confirmed valid syntax
        if isinstance(cc_list, list):
            for block in cc_list:
                total_cc += block.get("complexity", 0)
                if block.get("type") in ("function", "method"):
                    func_count += 1
        else:
            print(f"Warning: CC output for {filename} is not a list: {cc_list}")

        if func_count > 0:
            avg_cc = total_cc / func_count
        else:
            avg_cc = total_cc

        results.append(
            {
                "file": filename,
                "loc": loc,
                "maintainability_index": mi_value,
                "maintainability_grade": mi_grade,
                "total_cyclomatic_complexity": total_cc,
                "function_count": func_count,
                "average_cyclomatic_complexity": avg_cc,
            }
        )

    if len(results) != 20:
        print(f"Warning: Expected 20 rows, got {len(results)}")
    else:
        print("Successfully analyzed exactly 20 files.")

    results_dir = os.path.join("validation", "results")
    os.makedirs(results_dir, exist_ok=True)

    csv_path = os.path.join(results_dir, "radon_results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "loc",
                "maintainability_index",
                "maintainability_grade",
                "total_cyclomatic_complexity",
                "function_count",
                "average_cyclomatic_complexity",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"Wrote {csv_path}")

    mi_values = [r["maintainability_index"] for r in results]
    total_cc_values = [r["total_cyclomatic_complexity"] for r in results]
    avg_cc_values = [r["average_cyclomatic_complexity"] for r in results]

    summary_path = os.path.join(results_dir, "radon_summary.txt")
    with open(summary_path, "w", newline="") as f:
        f.write(f"Number of analyzed files: {len(results)}\n")
        f.write(f"min MI: {min(mi_values):.2f}\n")
        f.write(f"max MI: {max(mi_values):.2f}\n")
        f.write(f"mean MI: {statistics.mean(mi_values):.2f}\n")

        f.write(f"min complexity: {min(total_cc_values)}\n")
        f.write(f"max complexity: {max(total_cc_values)}\n")
        f.write(f"mean complexity: {statistics.mean(total_cc_values):.2f}\n")

        f.write(f"min average complexity: {min(avg_cc_values):.2f}\n")
        f.write(f"max average complexity: {max(avg_cc_values):.2f}\n")
        f.write(f"mean average complexity: {statistics.mean(avg_cc_values):.2f}\n")

    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
