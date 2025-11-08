from typing import Dict, Any, List
from datetime import datetime


class ReportsController:
    def __init__(self, repo):
        self.repo = repo

    @staticmethod
    def _normalize_dates(report_start: str, report_end: str) -> Dict[str, str]:
        def to_start(s: str) -> str:
            s = s.strip()
            return s if len(s) > 10 else f"{s} 00:00:00"

        def to_end(s: str) -> str:
            s = s.strip()
            return s if len(s) > 10 else f"{s} 23:59:59"

        start_norm = to_start(report_start)
        end_norm = to_end(report_end)
        if datetime.fromisoformat(start_norm) > datetime.fromisoformat(end_norm):
            raise ValueError("Invalid date range: start must be <= end")
        return {"start": start_norm, "end": end_norm}

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100.0, 2)

    @staticmethod
    def _with_created_percent(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        total = sum(int(r.get("count", 0)) for r in rows)
        out: List[Dict[str, Any]] = []
        for r in rows:
            cnt = int(r.get("count", 0))
            out.append({
                **r,
                "percentage": ReportsController._rate(cnt, total)
            })
        return out

    @staticmethod
    def _with_ended_rates(row: Dict[str, Any]) -> Dict[str, Any]:
        ended_total     = int(row.get("ended_total", 0))
        completed_count = int(row.get("completed_count", 0))
        expired_count   = int(row.get("expired_count", 0))

        return {
            **row,
            "completed_rate": ReportsController._rate(completed_count, ended_total),
            "expired_rate":   ReportsController._rate(expired_count, ended_total),
        }

    def build_report(self, report_start: str, report_end: str) -> Dict[str, Any]:
        rng = self._normalize_dates(report_start, report_end)

        created_status_raw = self.repo.created_status_distribution(
            start=rng["start"], end=rng["end"]
        )
        created_status = self._with_created_percent(created_status_raw)

        ended_perf_raw = self.repo.ended_performance(
            start=rng["start"], end=rng["end"]
        )
        ended_perf = self._with_ended_rates(ended_perf_raw)

        region_created = self.repo.region_counts_created(rng["start"], rng["end"])
        region_ended   = self.repo.region_counts_ended(rng["start"], rng["end"])

        category_created = self.repo.category_counts_created(rng["start"], rng["end"])
        category_ended   = self.repo.category_counts_ended(rng["start"], rng["end"])

        return {
            "meta": {
                "report_start": rng["start"],
                "report_end":   rng["end"],
                "status_basis": "SQLite view computed_status (now)",
            },
            "created_status": created_status,          
            "ended_performance": ended_perf,           
            "regional": {
                "created": region_created,             
                "ended":   region_ended,               
            },
            "category": {
                "created": category_created,           
                "ended":   category_ended,             
            },
        }