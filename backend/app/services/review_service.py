from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.engine.ai_reviewer import AIReviewer
from app.engine.confidence_engine import ConfidenceEngine
from app.engine.hybrid_engine import HybridEngine
from app.engine.language_detector import LanguageDetector
from app.engine.scoring_engine import ScoringEngine
from app.engine.static_analyzer import StaticAnalyzer
from app.engine.syntax_validator import SyntaxValidator
from app.models.review import Review
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreateRequest

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self, review_repo: ReviewRepository):
        self.review_repo = review_repo
        self.static_analyzer = StaticAnalyzer()
        self.ai_reviewer = AIReviewer()
        self.hybrid_engine = HybridEngine()
        self.confidence_engine = ConfidenceEngine()
        self.scoring_engine = ScoringEngine()
        self.language_detector = LanguageDetector()
        self.syntax_validator = SyntaxValidator()

    async def submit_review(
        self,
        db: AsyncSession,
        user_id: UUID,
        req: ReviewCreateRequest,
        file: Optional[UploadFile] = None,
    ) -> Review:
        source_code = req.source_code or ""
        file_name = req.file_name
        file_size = req.file_size

        if file:
            content = await file.read()
            # 2MB limit check
            if len(content) > 2097152:
                raise HTTPException(
                    status_code=400, detail="File size exceeds 2MB limit."
                )
            source_code = content.decode("utf-8", errors="replace")
            file_name = file.filename
            file_size = len(content)

        lang_id = None
        if isinstance(req.language_id, UUID):
            lang_id = req.language_id
        elif isinstance(req.language_id, str):
            from app.models.language import Language
            stmt = select(Language).where(Language.name.ilike(req.language_id))
            res = await db.execute(stmt)
            lang_obj = res.scalars().first()
            if lang_obj:
                lang_id = lang_obj.id

        review = Review(
            user_id=user_id,
            language_id=lang_id,
            title=req.title,
            source_code=source_code,
            repo_url=req.repo_url,
            file_name=file_name,
            file_size=file_size,
            status="processing",
            review_metadata={"requested_language": req.language_id} if isinstance(req.language_id, str) else {}
        )
        db.add(review)
        await db.commit()
        
        stmt = (
            select(Review)
            .options(selectinload(Review.language))
            .where(Review.id == review.id)
        )
        res = await db.execute(stmt)
        loaded_review = res.scalars().first()

        # We can trigger the background task here or from the controller.
        # It's cleaner to return the review and let the controller dispatch it to FastAPI BackgroundTasks.
        return loaded_review

    async def process_review(self, db_factory, review_id: UUID) -> None:
        """Background task to process the review."""
        # Using a db session factory or passing a new session
        async with db_factory() as db:
            review = await self.review_repo.get(db, review_id)
            if not review:
                logger.error(f"Review {review_id} not found for processing.")
                return

            notification_created = False
            try:
                if review.repo_url:
                    await self._process_repo(db, review)
                else:
                    await self._process_single_file(db, review)

                review.status = "completed"
            except Exception as e:
                logger.exception("Error processing review.")
                review.status = "failed"
                err_metadata = dict(review.review_metadata or {})
                err_metadata["error"] = str(e)
                review.review_metadata = err_metadata
            finally:
                db.add(review)
                
                # Create a single notification for the review process
                from app.models.notification import Notification
                from sqlalchemy import select
                
                # Deduplication check
                stmt = select(Notification).where(Notification.reference_id == f"review_{review.id}")
                res = await db.execute(stmt)
                existing_notif = res.scalars().first()
                
                if not existing_notif:
                    title = "Review Completed" if review.status == "completed" else "Review Failed"
                    msg = f"Your review for '{review.title}' has {review.status}."
                    notif = Notification(
                        user_id=review.user_id,
                        title=title,
                        message=msg,
                        type=f"review_{review.status}",
                        reference_id=f"review_{review.id}"
                    )
                    db.add(notif)
                
                await db.commit()

    async def _process_single_file(self, db: AsyncSession, review: Review) -> None:
        code = review.source_code
        language = review.review_metadata.get("requested_language", "Unknown")

        if review.language_id:
            from sqlalchemy import select

            from app.models.language import Language

            stmt = select(Language).where(Language.id == review.language_id)
            res = await db.execute(stmt)
            lang_obj = res.scalars().first()
            if lang_obj:
                language = lang_obj.name

        # --- Language Detection (BEFORE pipeline) ---
        lang_detection = self.language_detector.validate_language(
            language, code, review.file_name
        )

        # --- Final Language Resolution ---
        detected = lang_detection.get("detected_language", "Unknown")
        confidence = lang_detection.get("confidence", 0)
        selected = language

        # Use detection as authoritative if confident enough
        if detected != "Unknown" and confidence >= 25 and detected.lower() != selected.lower():
            final_language = detected
            lang_detection["final_language"] = final_language
            lang_detection["language_switched"] = (selected != "Unknown")
            # Update the review's language_id to the detected language
            from sqlalchemy import select as sa_select
            from app.models.language import Language as Lang
            det_stmt = sa_select(Lang).where(Lang.name == final_language)
            det_res = await db.execute(det_stmt)
            det_lang_obj = det_res.scalars().first()
            if det_lang_obj:
                review.language_id = det_lang_obj.id
        else:
            if selected == "Unknown" and (confidence < 25 or detected == "Unknown"):
                raise Exception("Could not confidently determine programming language. Please specify a language manually.")
                
            # Fallback to selected (which might be identical to detected, or detected is low confidence)
            final_language = selected if selected != "Unknown" else detected
            lang_detection["final_language"] = final_language
            lang_detection["language_switched"] = False

        # --- Syntax Validation (uses final_language) ---
        syntax_issues = self.syntax_validator.validate(code, final_language)

        # Use the resolved final language for the entire pipeline
        static_issues = self.static_analyzer.analyze(code, final_language)

        # Prepend syntax issues to static issues for Hybrid Engine processing
        static_issues = syntax_issues + static_issues

        ai_status = "available"
        ai_unavailable_reason = None
        
        try:
            ai_summary, improved_code, ai_enhanced_issues, ai_usage = await self.ai_reviewer.review(
                code, static_issues
            )
        except Exception as e:
            from app.engine.providers.base import AIAvailabilityError
            ai_status = "unavailable"
            if isinstance(e, AIAvailabilityError):
                ai_unavailable_reason = e.reason
            else:
                ai_unavailable_reason = "provider_error"
            
            ai_summary = "AI analysis temporarily unavailable."
            improved_code = None
            ai_enhanced_issues = []
            ai_usage = None

        # --- Hybrid Engine: normalize + fuse ---
        hybrid = HybridEngine()
        normalized_static = hybrid.normalize(static_issues, "Static")
        normalized_ai = hybrid.normalize(ai_enhanced_issues, "AI")
        unified_issues = hybrid.fuse(normalized_static, normalized_ai)

        # --- Confidence Engine ---
        unified_issues = self.confidence_engine.calculate_all(unified_issues)

        review.issues = unified_issues
        review.improved_code = improved_code

        complexity = self.static_analyzer.calculate_cyclomatic_complexity(code)
        lines_of_code = len(code.splitlines())
        metrics = self._calculate_metrics(unified_issues, complexity)
        if ai_usage:
            metrics["ai_usage"] = ai_usage
        
        # --- Scoring Engine ---
        scoring_results = self.scoring_engine.calculate_scores(
            unified_issues,
            cyclomatic_complexity=complexity,
            lines_of_code=lines_of_code
        )
        metrics["scoring_engine"] = scoring_results

        metrics["ai_summary"] = ai_summary
        metrics["lines_of_code"] = lines_of_code
        metrics["language_detection"] = lang_detection
        metrics["ai_status"] = ai_status
        if ai_unavailable_reason:
            metrics["ai_unavailable_reason"] = ai_unavailable_reason

        existing_metadata = dict(review.review_metadata or {})
        existing_metadata.update(metrics)
        review.review_metadata = existing_metadata
        # Override the top-level quality_score with the independent Scoring Engine result
        review.quality_score = scoring_results.get("overall_quality", metrics.get("quality_score", 0))

    async def _process_repo(self, db: AsyncSession, review: Review) -> None:
        url = review.repo_url
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", url, tmpdir],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to clone repository: {e.stderr.decode()}")

            all_issues = []
            file_count = 0
            largest_files = []
            ext_counts = {}
            total_complexity = 0

            total_lines_of_code = 0

            # Map extensions to languages for static analyzer
            ext_to_lang = {
                ".py": "Python",
                ".js": "JavaScript",
                ".ts": "TypeScript",
                ".java": "Java",
                ".c": "C",
                ".cpp": "C++",
            }

            for root, dirs, files in os.walk(tmpdir):
                if ".git" in dirs:
                    dirs.remove(".git")
                for file in files:
                    if not file.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp")):
                        continue

                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, tmpdir)
                    file_size = os.path.getsize(file_path)

                    largest_files.append({"name": rel_path, "size": file_size})

                    ext = os.path.splitext(file)[1].lower()
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
                    file_lang = ext_to_lang.get(ext, "Unknown")

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            code = f.read()
                    except UnicodeDecodeError:
                        continue

                    file_count += 1
                    total_lines_of_code += len(code.splitlines())
                    file_issues = self.static_analyzer.analyze(code, file_lang)
                    for issue in file_issues:
                        issue["file"] = rel_path
                    all_issues.extend(file_issues)
                    total_complexity += (
                        self.static_analyzer.calculate_cyclomatic_complexity(code)
                    )

            largest_files = sorted(
                largest_files, key=lambda x: x["size"], reverse=True
            )[:5]

            total_supported = sum(ext_counts.values())
            language_distribution = {}
            if total_supported > 0:
                for ext, count in ext_counts.items():
                    language_distribution[ext] = (
                        f"{(count / total_supported) * 100:.1f}%"
                    )
            else:
                language_distribution = {"unknown": "100%"}

            # --- Hybrid Engine: normalize repo static issues ---
            hybrid = HybridEngine()
            normalized_static = hybrid.normalize(all_issues, "Static")
            # Repo reviews currently run static analysis only (no AI per-file).
            # Fuse with an empty AI list so every issue gets an issue_id + source tag.
            unified_issues = hybrid.fuse(normalized_static, [])

            # --- Confidence Engine ---
            unified_issues = self.confidence_engine.calculate_all(unified_issues)

            metrics = self._calculate_metrics(unified_issues, total_complexity)
            
            # --- Scoring Engine ---
            scoring_results = self.scoring_engine.calculate_scores(
                unified_issues,
                cyclomatic_complexity=total_complexity,
                lines_of_code=total_lines_of_code
            )
            metrics["scoring_engine"] = scoring_results

            metrics["repo_insights"] = {
                "file_count": file_count,
                "largest_files": largest_files,
                "language_distribution": language_distribution,
                "repo_health_score": scoring_results.get("overall_quality", metrics.get("quality_score", 0)),
            }
            metrics["lines_of_code"] = total_lines_of_code

            review.issues = unified_issues
            existing_metadata = dict(review.review_metadata or {})
            existing_metadata.update(metrics)
            review.review_metadata = existing_metadata
            review.quality_score = scoring_results.get("overall_quality", metrics.get("quality_score", 0))

    def _calculate_metrics(
        self, issues: List[Dict[str, Any]], complexity: int = 10
    ) -> Dict[str, Any]:
        critical = sum(1 for i in issues if i.get("severity") == "Critical")
        high = sum(1 for i in issues if i.get("severity") == "High")
        medium = sum(1 for i in issues if i.get("severity") == "Medium")
        low = sum(1 for i in issues if i.get("severity") == "Low")

        total_issues = len(issues)

        quality_score = max(0, 100 - (critical * 10 + high * 5 + medium * 2 + low * 1))

        if quality_score > 90:
            maintainability_grade = "A"
        elif quality_score > 80:
            maintainability_grade = "B"
        elif quality_score > 70:
            maintainability_grade = "C"
        elif quality_score > 60:
            maintainability_grade = "D"
        else:
            maintainability_grade = "F"

        if critical > 2 or high > 5:
            tech_debt = "High"
        elif critical > 0 or high > 2 or medium > 5:
            tech_debt = "Medium"
        else:
            tech_debt = "Low"

        return {
            "quality_score": quality_score,
            "maintainability_grade": maintainability_grade,
            "tech_debt": critical * 10
            + high * 5
            + medium * 2
            + low,  # Changed to numerical for max filter
            "cyclomatic_complexity": complexity,
            "est_refactoring_time": f"{total_issues * 10} minutes",
            "security_score": max(0, 100 - (critical * 15)),
            "performance_score": max(0, 100 - (medium * 5)),
            "ai_confidence": 0.85,  # mock AI confidence
            "issue_counts": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
            },
        }

    async def duplicate_review(
        self, db: AsyncSession, user_id: UUID, review_id: UUID
    ) -> Optional[Review]:
        original = await self.review_repo.get(db, review_id)
        if not original or original.user_id != user_id:
            return None

        duplicate = Review(
            user_id=user_id,
            language_id=original.language_id,
            title=f"Copy of {original.title}",
            source_code=original.source_code,
            improved_code=original.improved_code,
            issues=original.issues,
            quality_score=original.quality_score,
            review_metadata=original.review_metadata,
            status=original.status,
            file_name=original.file_name,
            file_size=original.file_size,
            repo_url=original.repo_url,
        )
        db.add(duplicate)
        await db.commit()
        await db.refresh(duplicate)
        return duplicate

    async def delete_review(
        self, db: AsyncSession, user_id: UUID, review_id: UUID
    ) -> bool:
        original = await self.review_repo.get(db, review_id)
        if not original or original.user_id != user_id:
            return False

        await self.review_repo.delete(db, review_id)
        return True
