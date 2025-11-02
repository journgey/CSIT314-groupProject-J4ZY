from typing import Dict, Any, List, Optional
from datetime import datetime


class ReportsService:
    """
    Service layer for reports.
    - Validates input (date range).
    - Sets default anchor time to end-of-day of report_end.
    - Delegates to repository and assembles the response payload.
    """

    def __init__(self, repo):
        self.repo = repo

    @staticmethod
    def _normalize_dates(report_start: str, report_end: str) -> Dict[str, str]:
        """
        Normalize to inclusive boundaries:
        - start: YYYY-MM-DD 00:00:00
        - end  : YYYY-MM-DD 23:59:59
        """
        # Accept 'YYYY-MM-DD' or full 'YYYY-MM-DD HH:MM:SS'
        def to_start(s: str) -> str:
            return s if len(s) > 10 else f"{s} 00:00:00"

        def to_end(s: str) -> str:
            return s if len(s) > 10 else f"{s} 23:59:59"

        start_norm = to_start(report_start.strip())
        end_norm = to_end(report_end.strip())
        # Basic validation: start <= end
        if datetime.fromisoformat(start_norm) > datetime.fromisoformat(end_norm):
            raise ValueError("Invalid date range: start must be <= end")
        return {"start": start_norm, "end": end_norm}

    @staticmethod
    def _default_anchor(end_inclusive: str) -> str:
        """
        Anchor time is fixed at the end of the reporting window.
        """
        return end_inclusive  # already '... 23:59:59'

    def build_report(self, report_start: str, report_end: str) -> Dict[str, Any]:
        # Normalize date range and derive anchor
        rng = self._normalize_dates(report_start, report_end)
        anchor = self._default_anchor(rng["end"])

        # 1) Created cohort (status distribution)
        created_status = self.repo.created_status_distribution(
            start=rng["start"], end=rng["end"], anchor=anchor
        )

        # 2) Ended cohort performance
        ended_perf = self.repo.ended_performance(
            start=rng["start"], end=rng["end"], anchor=anchor
        )

        # 3) Regional analysis
        region_created = self.repo.region_counts_created(rng["start"], rng["end"])
        region_ended = self.repo.region_counts_ended(rng["start"], rng["end"])

        # 4) Category analysis
        category_created = self.repo.category_counts_created(rng["start"], rng["end"])
        category_ended = self.repo.category_counts_ended(rng["start"], rng["end"])

        # Assemble payload
        return {
            "meta": {
                "report_start": rng["start"],
                "report_end": rng["end"],
                "anchor_time": anchor,
            },
            "created_status": created_status,
            "ended_performance": ended_perf,
            "regional": {
                "created": region_created,
                "ended": region_ended,
            },
            "category": {
                "created": category_created,
                "ended": category_ended,
            },
        }
