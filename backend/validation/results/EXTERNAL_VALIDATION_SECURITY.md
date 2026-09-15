# External Empirical Validation: Security (CodePilot Static Engine)

## 1. Objective
To externally validate CodePilot v2.0's Security Score by correlating it against an independently defined, qualitative severity ground truth (`ground_truth.csv`), utilizing a controlled 20-file benchmark containing both explicitly rule-matched and conceptually complex vulnerabilities.

## 2. Dataset
- **Ground Truth**: `backend/validation/benchmark/ground_truth.csv`. Qualitative severity levels were ordinally encoded: `none`=0, `low`=1, `medium`=2, `high`=3, `critical`=4.
- **CodePilot Results**: `backend/validation/results/codepilot_results.csv`. 
- **N = 20**: The primary benchmark samples (`sample01.py` through `sample20.py`). Model property files were explicitly excluded.

## 3. Ground-Truth Methodology
The `expected_security_level` labels were independently assigned during the creation of the benchmark, prior to running CodePilot. The ordinal encoding serves exclusively to rank the relative severity of vulnerabilities (i.e., `critical` > `high` > `medium` > `low` > `none`); it is not a linear severity multiplier. CodePilot's results were not used to determine or revise these labels.

## 4. Spearman Method
The two datasets were joined on `file`. A statistically correct tied-rank Spearman correlation was calculated. Since a higher ground-truth severity (e.g., `critical` = 4) corresponds to more dangerous code, we expect the CodePilot Security Score (where 100 is best, 0 is worst) to decrease. Thus, the expected correlation direction is **negative**.

## 5. Result
- **n**: 20
- **Spearman rho**: -0.385272
- **p-value**: 9.352510e-02 (0.0935)

## 6. Ranking Comparison

- **Highest Severity Benchmark Cases (Ground Truth)**: `sample17.py` (critical), `sample19.py` (critical), `sample20.py` (critical), `sample13.py` (high), `sample15.py` (high).
- **Lowest Severity Benchmark Cases (Ground Truth)**: `sample01.py` through `sample08.py`, `sample10.py`, `sample11.py`, `sample14.py`, `sample18.py` (all scored `none`).
- **Mean Absolute Rank Difference**: 6.00

## 7. Disagreement Analysis

The largest rank disagreements between the expected ground truth and CodePilot's static score highlight the limitations of static analysis:

1. **`sample17.py`** (Diff: 9.5)
   - **Ground Truth**: Critical (Rank 19.0) - SSRF and Path Traversal.
   - **CodePilot Score**: 100.0 (Rank 11.5) | Issues: 0
   - **Analysis**: CodePilot's static analyzer completely missed the SSRF (`requests.get(url)`) and Path Traversal (`open(path)`). Because the `eval` and `exec` keywords were deliberately removed in favor of these conceptual vulnerabilities, the regex-based static engine scored it perfectly.

2. **`sample19.py`** (Diff: 9.5)
   - **Ground Truth**: Critical (Rank 19.0) - Insecure YAML deserialization & O(N³) loops.
   - **CodePilot Score**: 100.0 (Rank 11.5) | Issues: 0
   - **Analysis**: The static analyzer does not recognize `yaml.load(payload, Loader=yaml.Loader)` as a vulnerability, missing the insecure deserialization flaw entirely. 

3. **`sample13.py`** (Diff: 6.5)
   - **Ground Truth**: High (Rank 16.0) - Reflected XSS and weak cryptographic hashing (`hashlib.md5`).
   - **CodePilot Score**: 100.0 (Rank 11.5) | Issues: 0
   - **Analysis**: CodePilot missed the weak MD5 hashing and the unescaped HTML response (Reflected XSS), which require semantic tracking.

4. **`sample15.py`** (Diff: 6.5)
   - **Ground Truth**: High (Rank 16.0) - Unpickling untrusted data, SQL injection.
   - **CodePilot Score**: 100.0 (Rank 11.5) | Issues: 0
   - **Analysis**: CodePilot's static rules missed `pickle.loads()` and the insecure SQL concatenation.

5. **`sample16.py`** (Diff: 6.5)
   - **Ground Truth**: High (Rank 16.0) - XXE vulnerability via `xml.etree`.
   - **CodePilot Score**: 100.0 (Rank 11.5) | Issues: 0
   - **Analysis**: The static analyzer missed the unsafe XML parser initialization, failing to detect the XML External Entity vulnerability.

## 8. Interpretation

The Spearman correlation is **ρ = -0.385**.

Because we expect a higher ground-truth severity to yield a lower CodePilot score, the **negative correlation provides evidence of alignment in the expected direction**. 

However, we must employ conservative interpretation: this weak-to-moderate correlation (and p ~ 0.09) demonstrates that while CodePilot successfully catches standard patterns (like the `os.system` SQL execution in `sample20.py` which scored 0.0), its **Static Engine completely misses conceptually complex, less-tailored vulnerabilities** such as SSRF, XXE, XSS, and insecure deserialization. 

This result does not prove the model is universally correct, nor does the correlation automatically validate the engine. Rather, it successfully validates that the benchmark is robust enough to expose the explicit limitations of a static-only regex engine. The full AI-enabled hybrid engine is required to catch these semantic vulnerabilities.

## 9. Limitations

- **n = 20**: The sample size is extremely small, limiting statistical power.
- **Ordinal Ground Truth**: The ground-truth severity is qualitative and ordinal, not a continuous mathematical scale.
- **Static-Only Engine**: CodePilot was run intentionally without its Gemini AI integration. The missed vulnerabilities in the disagreement analysis are precisely the types of issues the Hybrid AI engine is designed to detect.
- **Controlled Benchmark**: The dataset is a synthetic, controlled benchmark and not a massive corpus of production repositories.
