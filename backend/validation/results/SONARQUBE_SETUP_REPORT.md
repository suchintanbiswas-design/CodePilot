# SonarQube Community Build Setup Report

## Setup Attempt Overview

An attempt was made to deploy an isolated SonarQube Community Build instance locally via Docker to analyze the 20-file Python benchmark.

### Intended Configuration
- **SonarQube Version:** Community Edition
- **Docker Image:** sonarqube:community
- **Project Configuration:** Local project codepilot_benchmark using sonar-scanner-cli.
- **Target Files:** ONLY ackend/validation/benchmark/sample01.py through sample20.py. 
  - Explicitly excluded: model_properties/, holdout/, and esults/.

## Setup Problems Encountered

**Analysis Could Not Be Performed.**

The local Docker daemon is unable to pull images from Docker Hub (egistry-1.docker.io). 

**Exact Reason:** 
Docker is failing with a network proxy / TLS handshake timeout. The daemon is configured with a proxy (http.docker.internal:3128), which is blocking or failing to negotiate a TLS connection to Docker Hub. 

`
Error response from daemon: failed to resolve reference "docker.io/library/sonarqube:community": 
failed to do request: Head "https://registry-1.docker.io/v2/library/sonarqube/manifests/community": 
net/http: TLS handshake timeout
`

Because the sonarqube:community (and sonarsource/sonar-scanner-cli) images cannot be pulled into the local Docker daemon, SonarQube cannot be started to analyze the Python code.

---

## Theoretical Metrics Mapping (If Analysis Succeeded)

If the environment permitted the analysis to run, the following SonarQube metrics would have been evaluated for comparability with CodePilot Scoring Engine v2.0:

### 1. Genuinely Comparable Metrics
* **Code Smells / Maintainability Rating:** Corresponds to CodePilot's **Maintainability Score**. Both systems measure technical debt and code smells.
* **Vulnerabilities / Security Rating:** Corresponds to CodePilot's **Security Score**. Both detect hardcoded secrets, injections, and unsafe configurations.
* **Cyclomatic Complexity:** Corresponds directly to CodePilot's **average_complexity** metadata, as both use the standard McCabe complexity definition.
* **Lines of Code (LOC):** Corresponds directly to CodePilot's **LOC_K** sizing normalization.

### 2. Partially Comparable Metrics
* **Bugs / Reliability Rating:** CodePilot detects bugs via CATCH_ALL_PY, PY_MUTABLE_DEFAULT_ARG, etc. However, CodePilot absorbs these into the overall Quality/Tech Debt scores, whereas SonarQube separates them into a strict Reliability rating.

### 3. NOT Directly Comparable
* **Performance:** SonarQube does not have a dedicated Performance score/rating. It classifies inefficiencies as Code Smells. CodePilot has a distinct, isolated **Performance Score** explicitly driven by algorithmic complexity (PY_NESTED_LOOP_COMPLEXITY) and database patterns (PY_N_PLUS_1_QUERY).
* **Technical Debt Ratio:** SonarQube measures debt in minutes/days of remediation time against the total cost to rewrite the file. CodePilot measures normalized severity-impact (1-100 scale). The conceptual goal is identical, but the mathematical formulas cannot be directly correlated.
* **Coverage / Duplications:** CodePilot v2.0 static analysis does not currently measure test coverage or code duplication, while SonarQube does.

## Conclusion

The empirical validation using SonarQube is blocked by the local Docker network environment. Setup was halted as requested, with no modifications made to the scoring engine, benchmark dataset, or ground truth.
