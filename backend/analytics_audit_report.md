# Analytics Page Audit Report

## 1. Data Flow for "Issues Fixed"

Currently, the data flow for `Issues Fixed` halts completely at the backend controller level.

- **Frontend:** `AnalyticsPage.tsx` expects an `issuesFixed` field from the `/dashboard/analytics` API response.
- **Backend Endpoint:** `app/controllers/review_controller.py` at `GET /dashboard/analytics` constructs the metrics dictionary.
- **Backend Calculation:** The `issuesFixed` value is completely hardcoded to `0`. 
  - File: `review_controller.py`, Line 408: `"issuesFixed": 0,  # CodePilot does not track "issues fixed"`
- **Database (`Review` Model):** There is absolutely no schema support for issue tracking. Issues are stored as a flat `JSONB` array (`issues`) on isolated `Review` records. 

## 2. Feasibility of Tracking "Issues Fixed"

The current CodePilot architecture **lacks the required information** to legitimately track when an issue is "fixed". Specifically:
1. **No Issue IDs:** Issues are transient JSON dictionaries (`{"severity": "High", "description": "..."}`). They have no unique identifiers.
2. **No Review-to-Review Linkage:** There is no schema relationship connecting a new review to a past review. If a user submits `main.py` twice, they are treated as two independent, completely unrelated reviews in the database.
3. **No State/Resolution Tracking:** There is no `Issue` table, meaning there's no place to set `status = "resolved"`.

## 3. Smallest Reliable Implementation Proposal

To track "issues fixed" reliably without introducing a massive relational database redesign (like splitting the `JSONB` into an `Issue` table), I propose the following lightweight strategy:

1. **Schema Addition:** Add two lightweight fields to the `Review` model:
   - `previous_review_id`: A self-referencing foreign key linking a review to the previous iteration of the same code.
   - `issues_fixed_count`: An integer column storing how many issues were fixed in this specific review compared to its predecessor.
2. **Frontend Linkage:** When the user clicks "Re-Review" or submits new code from the Review Details page, the frontend passes the current `review_id` as `previous_review_id` to the backend.
3. **Backend Matching Strategy (The "Fix" Engine):**
   - During the review pipeline, if `previous_review_id` is provided, fetch the previous review's JSONB `issues`.
   - Implement a stable matching algorithm based on a deterministic signature: `hash(rule_type + severity + normalized_description)`. Line numbers should be ignored in the signature because adding code above an issue shifts the line number but doesn't fix the issue.
   - Subtract the current review's issue signatures from the previous review's issue signatures. The count of missing signatures is written to `issues_fixed_count`.
4. **Analytics Aggregation:** The `/dashboard/analytics` endpoint simply returns `sum(r.issues_fixed_count for r in reviews)`.

## 4. Audit of Other Analytics Cards

I audited the `/dashboard/analytics` endpoint logic for the remaining three metrics.

| Metric | Calculation Mechanism | Hardcoded/Placeholder? | Observation |
|---|---|---|---|
| **Average Score** | `sum(quality_score) / len(valid_scores)` | No | Functioning correctly based on genuine scores. |
| **Critical Alerts** | Loops through every issue in every review ever submitted and adds +1 if `severity == "Critical"` | No | Works, but it is a **cumulative total** across all historical reviews, not a count of currently active alerts. |
| **Reviews Run** | `len(reviews)` for the current user | No | Functioning correctly based on exact database row count. |
