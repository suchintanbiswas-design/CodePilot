from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import async_session_maker, get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreateRequest, ReviewListResponse, ReviewResponse
from app.services.review_service import ReviewService


class ReviewController:
    def __init__(self):
        self.router = APIRouter(prefix="/reviews", tags=["Reviews"])
        self.review_repo = ReviewRepository()
        self.review_service = ReviewService(self.review_repo)

        self._register_routes()

    def _register_routes(self):
        @self.router.post("", response_model=ReviewResponse, status_code=202)
        async def create_review(
            background_tasks: BackgroundTasks,
            req_data: str = Form(...),
            file: Optional[UploadFile] = File(None),
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            try:
                req_dict = json.loads(req_data)
                req = ReviewCreateRequest(**req_dict)
            except (json.JSONDecodeError, ValidationError) as e:
                raise HTTPException(
                    status_code=422, detail=f"Invalid request data: {e}"
                )

            review = await self.review_service.submit_review(
                db, current_user.id, req, file
            )

            # Start background processing
            background_tasks.add_task(
                self.review_service.process_review, async_session_maker, review.id
            )

            return review

        @self.router.post("/detect-language")
        async def detect_language(
            req_data: str = Form(...),
            current_user: User = Depends(get_current_user),
        ):
            """Pre-submission language detection for mismatch validation."""
            from app.engine.language_detector import LanguageDetector

            try:
                req_dict = json.loads(req_data)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")

            source_code = req_dict.get("source_code", "")
            selected_language = req_dict.get("language", "Unknown")
            filename = req_dict.get("file_name", None)

            detector = LanguageDetector()
            result = detector.validate_language(selected_language, source_code, filename)

            return {"success": True, "data": result}

        @self.router.get("/{review_id}", response_model=ReviewResponse)
        async def get_review(
            review_id: UUID,
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            review = await self.review_repo.get_with_relations(db, review_id)
            if not review:
                raise HTTPException(status_code=404, detail="Review not found")
            if review.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to access this review"
                )
            return review

        @self.router.get("", response_model=ReviewListResponse)
        async def list_reviews(
            query: Optional[str] = Query(None),
            security_score_min: Optional[int] = Query(None),
            maintainability_grade: Optional[str] = Query(None),
            tech_debt_max: Optional[int] = Query(None),
            ai_confidence_min: Optional[float] = Query(None),
            skip: int = 0,
            limit: int = 10,
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            if any(
                x is not None
                for x in [
                    query,
                    security_score_min,
                    maintainability_grade,
                    tech_debt_max,
                    ai_confidence_min,
                ]
            ):
                items = await self.review_repo.search_reviews(
                    db,
                    current_user.id,
                    query,
                    security_score_min,
                    maintainability_grade,
                    tech_debt_max,
                    ai_confidence_min,
                    skip,
                    limit,
                )
            else:
                items = await self.review_repo.get_paginated_by_user(
                    db, current_user.id, skip, limit
                )

            total = await self.review_repo.count_by_user(db, current_user.id)
            return ReviewListResponse(
                items=items,
                total=total,
                page=(skip // limit) + 1 if limit > 0 else 1,
                size=limit,
            )

        @self.router.post("/{review_id}/duplicate")
        async def duplicate_review(
            review_id: UUID,
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            review = await self.review_service.duplicate_review(
                db, current_user.id, review_id
            )
            if not review:
                raise HTTPException(status_code=404, detail="Review not found")
            return {"success": True, "data": {"id": review.id}}

        @self.router.delete("/{review_id}")
        async def delete_review(
            review_id: UUID,
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            success = await self.review_service.delete_review(
                db, current_user.id, review_id
            )
            if not success:
                raise HTTPException(status_code=404, detail="Review not found")

            from app.services.report_service import ReportService

            await ReportService().invalidate_report_cache(review_id)

            return {"success": True, "message": "Review deleted"}

        @self.router.get("/{review_id}/report")
        async def download_report(
            review_id: UUID,
            type: str = "pdf",
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            review = await self.review_repo.get(db, review_id)
            if not review or review.user_id != current_user.id:
                raise HTTPException(status_code=404, detail="Review not found")

            from fastapi.responses import Response

            from app.services.report_service import ReportService

            try:
                content = await ReportService().get_or_generate_report(
                    db, review_id, type
                )
                media_type = "application/pdf" if type == "pdf" else "text/html"
                return Response(content=content, media_type=media_type)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/dashboard/metrics")
        async def get_dashboard_metrics(
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            from app.models.review import Review
            from app.models.language import Language
            from datetime import datetime, timedelta

            stmt_all = select(Review).where(Review.user_id == current_user.id)
            res_all = await db.execute(stmt_all)
            reviews = res_all.scalars().all()

            # Avg Score
            valid_scores = [r.quality_score for r in reviews if r.quality_score is not None]
            avg_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

            # Tech Debt Trend
            # Group by actual review dates (days)
            debt_by_date = {}
            for r in reviews:
                if r.status == "completed" and r.created_at and r.review_metadata and "tech_debt" in r.review_metadata:
                    d = r.created_at.date()
                    if d not in debt_by_date:
                        debt_by_date[d] = []
                    debt_by_date[d].append(int(r.review_metadata["tech_debt"]))
            
            tech_debt_trend = None
            if len(debt_by_date) >= 2:
                sorted_dates = sorted(debt_by_date.keys())
                earliest_date = sorted_dates[0]
                latest_date = sorted_dates[-1]
                
                earliest_avg = sum(debt_by_date[earliest_date]) / len(debt_by_date[earliest_date])
                latest_avg = sum(debt_by_date[latest_date]) / len(debt_by_date[latest_date])
                
                if earliest_avg > 0:
                    tech_debt_trend = round(((earliest_avg - latest_avg) / earliest_avg) * 100, 1)
            
            # Review Streak (consecutive days)
            review_dates = set()
            for r in reviews:
                if r.status == "completed" and r.created_at:
                    review_dates.add(r.created_at.date())
            
            streak = 0
            now = datetime.utcnow()
            curr_date = now.date()
            if curr_date not in review_dates and (curr_date - timedelta(days=1)) not in review_dates:
                streak = 0
            else:
                check_date = curr_date if curr_date in review_dates else curr_date - timedelta(days=1)
                while check_date in review_dates:
                    streak += 1
                    check_date -= timedelta(days=1)

            # AI Usage Tokens
            ai_usage_tokens = 0
            has_tokens = False
            for r in reviews:
                if r.status == "completed" and r.review_metadata and "ai_usage" in r.review_metadata:
                    ai_usage = r.review_metadata["ai_usage"]
                    if "total_tokens" in ai_usage:
                        ai_usage_tokens += ai_usage["total_tokens"]
                        has_tokens = True
            
            if not has_tokens:
                ai_usage_tokens = None

            # Most Used Languages
            lang_counts = {}
            for r in reviews:
                if r.language_id:
                    lang_counts[r.language_id] = lang_counts.get(r.language_id, 0) + 1
            
            lang_distribution = []
            if lang_counts:
                lang_stmt = select(Language).where(Language.id.in_(list(lang_counts.keys())))
                lang_res = await db.execute(lang_stmt)
                langs = {l.id: l.name for l in lang_res.scalars().all()}
                
                total_lang_reviews = sum(lang_counts.values())
                colors = ["bg-blue-500", "bg-yellow-500", "bg-cyan-500", "bg-green-500", "bg-purple-500"]
                
                sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
                for idx, (lid, count) in enumerate(sorted_langs):
                    lang_distribution.append({
                        "name": langs.get(lid, "Unknown"),
                        "percent": round((count / total_lang_reviews) * 100),
                        "color": colors[idx % len(colors)]
                    })

            return {
                "success": True,
                "data": {
                    "avgScore": avg_score,
                    "techDebtTrend": tech_debt_trend,
                    "reviewStreak": streak,
                    "aiUsageTokens": ai_usage_tokens,
                    "languages": lang_distribution
                }
            }

        @self.router.get("/dashboard/analytics")
        async def get_dashboard_analytics(
            db: AsyncSession = Depends(get_db),
            current_user: User = Depends(get_current_user),
        ):
            from app.models.language import Language
            from app.models.review import Review

            # 1. Fetch all user reviews
            stmt_all = select(Review).where(Review.user_id == current_user.id)
            res_all = await db.execute(stmt_all)
            reviews = res_all.scalars().all()

            # Avg Score
            valid_scores = [r.quality_score for r in reviews if r.quality_score is not None]
            avg_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0

            # Reviews Run
            reviews_run = len(reviews)

            # Issue Tracking
            critical_alerts = 0
            severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            for r in reviews:
                if r.issues:
                    for issue in r.issues:
                        sev = issue.get("severity", "Low")
                        if sev == "Critical":
                            critical_alerts += 1
                        if sev in severity_counts:
                            severity_counts[sev] += 1
                        else:
                            severity_counts[sev] = 1

            issue_type_data = [
                {"name": "Critical", "count": severity_counts.get("Critical", 0)},
                {"name": "High", "count": severity_counts.get("High", 0)},
                {"name": "Medium", "count": severity_counts.get("Medium", 0)},
                {"name": "Low", "count": severity_counts.get("Low", 0)}
            ]

            # Language Popularity
            lang_counts = {}
            for r in reviews:
                if r.language_id:
                    lang_counts[r.language_id] = lang_counts.get(r.language_id, 0) + 1

            lang_data = []
            if lang_counts:
                lang_stmt = select(Language).where(
                    Language.id.in_(list(lang_counts.keys()))
                )
                lang_res = await db.execute(lang_stmt)
                langs = {l.id: l.name for l in lang_res.scalars().all()}

                for lid, count in lang_counts.items():
                    lang_data.append(
                        {"name": langs.get(lid, "Unknown"), "value": count}
                    )

            # Trend Data (Monthly)
            trends = {}
            for r in reviews:
                if not r.created_at:
                    continue
                month_name = r.created_at.strftime("%b")
                month_sort = r.created_at.strftime("%Y-%m")
                
                if month_sort not in trends:
                    trends[month_sort] = {
                        "name": month_name,
                        "count": 0,
                        "quality": 0,
                        "issues": 0,
                        "techDebt": 0,
                    }

                trends[month_sort]["count"] += 1
                trends[month_sort]["quality"] += r.quality_score or 0
                trends[month_sort]["issues"] += len(r.issues) if r.issues else 0
                
                if r.review_metadata:
                    trends[month_sort]["techDebt"] += int(r.review_metadata.get("tech_debt", 0))

            trend_data = []
            for m in sorted(trends.keys()):
                c = trends[m]["count"]
                trend_data.append(
                    {
                        "name": trends[m]["name"],
                        "quality": round(trends[m]["quality"] / c, 1) if c else 0,
                        "issues": trends[m]["issues"],
                        "techDebt": round(trends[m]["techDebt"] / c, 1) if c else 0,
                    }
                )

            issues_detected = sum(severity_counts.values())

            return {
                "success": True,
                "data": {
                    "metrics": {
                        "avgScore": avg_score,
                        "issuesDetected": issues_detected,
                        "criticalAlerts": critical_alerts,
                        "reviewsRun": reviews_run,
                    },
                    "trendData": trend_data,
                    "langData": lang_data,
                    "issueTypeData": issue_type_data
                }
            }


review_controller = ReviewController()
