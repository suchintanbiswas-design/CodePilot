from uuid import UUID




class ReportService:
    def __init__(self):
        pass

    async def generate_report_content(
        self, db, review_id: UUID, report_type: str
    ) -> bytes:
        from sqlalchemy import select

        from app.models.review import Review

        stmt = select(Review).where(Review.id == review_id)
        res = await db.execute(stmt)
        review = res.scalars().first()

        if not review:
            raise Exception("Review not found")

        if report_type == "pdf":
            import io
            from datetime import datetime

            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )
            Story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                "CodePilotTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#2C3E50"),
                spaceAfter=14,
            )
            Story.append(Paragraph("CodePilot Review Report", title_style))
            Story.append(Spacer(1, 12))

            # Review Summary
            Story.append(
                Paragraph(f"<b>Review Title:</b> {review.title}", styles["Normal"])
            )
            Story.append(Paragraph(f"<b>Status:</b> {review.status}", styles["Normal"]))
            gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            Story.append(
                Paragraph(f"<b>Generated At:</b> {gen_time}", styles["Normal"])
            )
            Story.append(Spacer(1, 12))

            # Scores
            qs = review.quality_score or "N/A"
            metadata = review.review_metadata or {}
            ss = metadata.get("security_score", "N/A")
            ps = metadata.get("performance_score", "N/A")
            td = metadata.get("tech_debt", "N/A")

            Story.append(Paragraph(f"<b>Quality Score:</b> {qs}", styles["Normal"]))
            Story.append(Paragraph(f"<b>Security Score:</b> {ss}", styles["Normal"]))
            Story.append(Paragraph(f"<b>Performance Score:</b> {ps}", styles["Normal"]))
            Story.append(Paragraph(f"<b>Tech Debt:</b> {td}", styles["Normal"]))
            Story.append(Spacer(1, 12))

            # AI Summary
            ai_summary = metadata.get("ai_summary", "No AI summary available.")
            Story.append(Paragraph("<b>AI Summary:</b>", styles["Heading3"]))
            Story.append(Paragraph(ai_summary, styles["Normal"]))
            Story.append(Spacer(1, 12))

            # Issues Table
            Story.append(Paragraph("<b>Issues Found:</b>", styles["Heading3"]))
            if review.issues:
                data = [["Line", "Severity", "Message"]]
                for issue in review.issues[:20]:  # Limit to 20 for PDF
                    data.append(
                        [
                            str(issue.get("line", "N/A")),
                            issue.get("severity", "Unknown"),
                            issue.get("message", "")[:50] + "...",  # truncate
                        ]
                    )
                t = Table(data, colWidths=[50, 70, 340])
                t.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            (
                                "BACKGROUND",
                                (0, 1),
                                (-1, -1),
                                colors.HexColor("#ECF0F1"),
                            ),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                Story.append(t)
            else:
                Story.append(Paragraph("No issues found.", styles["Normal"]))
            Story.append(Spacer(1, 12))

            # Code Snippets
            Story.append(Paragraph("<b>Original Code Snippet:</b>", styles["Heading3"]))
            orig = (
                (review.source_code[:500] + "...")
                if review.source_code and len(review.source_code) > 500
                else (review.source_code or "N/A")
            )
            Story.append(Paragraph(orig.replace("\n", "<br/>"), styles["Code"]))
            Story.append(Spacer(1, 12))

            if review.improved_code:
                Story.append(
                    Paragraph("<b>Improved Code Snippet:</b>", styles["Heading3"])
                )
                impr = (
                    (review.improved_code[:500] + "...")
                    if len(review.improved_code) > 500
                    else review.improved_code
                )
                Story.append(Paragraph(impr.replace("\n", "<br/>"), styles["Code"]))

            doc.build(Story)
            return buffer.getvalue()

        elif report_type == "html":
            return f"<html><body><h1>Report for Review {review_id}</h1><p>{review.title}</p></body></html>".encode(
                "utf-8"
            )

        return b"UNKNOWN_FORMAT"

    async def get_or_generate_report(
        self, db, review_id: UUID, report_type: str
    ) -> bytes:
        cache_key = f"report:{review_id}:{report_type}"
        from app.config.redis import _redis_client
        # try to get from redis
        if _redis_client:
            cached = await _redis_client.get(cache_key)
            if cached:
                return cached

        # generate synchronously
        content = await self.generate_report_content(db, review_id, report_type)

        # cache it
        if _redis_client:
            await _redis_client.setex(cache_key, 3600, content)
        return content

    async def invalidate_report_cache(self, review_id: UUID):
        from app.config.redis import _redis_client
        if _redis_client:
            for report_type in ["pdf", "html"]:
                cache_key = f"report:{review_id}:{report_type}"
                await _redis_client.delete(cache_key)
