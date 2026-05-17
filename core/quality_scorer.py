"""
Data Quality Scorer — Layer 2
──────────────────────────────
Automated quality assessment for each data source across three dimensions:
  1. Completeness — How many fields are non-null?
  2. Consistency — Are there duplicates, outliers, type mismatches?
  3. Timeliness — How fresh is the data?
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from core.data_federation import DataSource


@dataclass
class QualityReport:
    """Quality assessment result for a single data source."""
    source_id: str
    source_name: str
    overall_score: float = 0.0          # 0-100
    completeness_score: float = 0.0     # 0-100
    consistency_score: float = 0.0      # 0-100
    timeliness_score: float = 0.0       # 0-100
    issues: List[Dict] = field(default_factory=list)
    duplicate_count: int = 0
    null_count: int = 0
    outlier_count: int = 0
    total_cells: int = 0
    assessed_at: str = ""

    @property
    def grade(self) -> str:
        if self.overall_score >= 90: return "A"
        if self.overall_score >= 80: return "B"
        if self.overall_score >= 70: return "C"
        if self.overall_score >= 50: return "D"
        return "F"

    @property
    def grade_emoji(self) -> str:
        grades = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⛔"}
        return grades.get(self.grade, "❓")

    def summary(self) -> str:
        return (
            f"{self.grade_emoji} {self.source_name}: {self.overall_score:.1f}/100 "
            f"(Grade {self.grade}) | "
            f"C={self.completeness_score:.0f} I={self.consistency_score:.0f} "
            f"T={self.timeliness_score:.0f} | "
            f"{len(self.issues)} issues found"
        )


class DataQualityScorer:
    """
    Scores data quality across completeness, consistency, and timeliness.
    Returns detailed QualityReport with actionable issue descriptions.
    """

    def __init__(self, completeness_weight=0.35, consistency_weight=0.35,
                 timeliness_weight=0.30, zscore_threshold=2.5):
        self.w_complete = completeness_weight
        self.w_consist = consistency_weight
        self.w_timely = timeliness_weight
        self.zscore_thresh = zscore_threshold

    def score_source(self, source: DataSource) -> QualityReport:
        """Score a single data source."""
        report = QualityReport(
            source_id=source.source_id,
            source_name=source.source_name,
            assessed_at=datetime.now().isoformat(),
        )

        if source.data is not None and len(source.data) > 0:
            report = self._score_structured(source, report)
        elif source.text_content:
            report = self._score_text(source, report)
        else:
            report.overall_score = 0
            report.issues.append({
                "severity": "critical",
                "type": "empty_source",
                "message": "Data source is empty or could not be loaded."
            })

        return report

    def score_all(self, sources: Dict[str, DataSource]) -> Dict[str, QualityReport]:
        """Score all sources in the federation hub."""
        return {sid: self.score_source(src) for sid, src in sources.items()}

    # ── Structured Data Scoring ─────────────────────────────────────────────

    def _score_structured(self, source: DataSource,
                          report: QualityReport) -> QualityReport:
        df = source.data
        report.total_cells = df.shape[0] * df.shape[1]

        # 1. Completeness
        report.completeness_score, null_issues = self._assess_completeness(df)
        report.issues.extend(null_issues)

        # 2. Consistency
        report.consistency_score, consist_issues = self._assess_consistency(df)
        report.issues.extend(consist_issues)

        # 3. Timeliness
        report.timeliness_score, time_issues = self._assess_timeliness(df, source)
        report.issues.extend(time_issues)

        # Overall weighted score
        report.overall_score = (
            self.w_complete * report.completeness_score +
            self.w_consist * report.consistency_score +
            self.w_timely * report.timeliness_score
        )

        return report

    def _assess_completeness(self, df: pd.DataFrame) -> Tuple[float, List[Dict]]:
        """Score completeness based on null/missing values."""
        issues = []
        total_cells = df.shape[0] * df.shape[1]
        null_cells = df.isnull().sum().sum()
        null_pct = (null_cells / total_cells * 100) if total_cells > 0 else 0

        # Per-column analysis
        for col in df.columns:
            col_null_pct = df[col].isnull().mean() * 100
            if col_null_pct > 5:
                issues.append({
                    "severity": "warning" if col_null_pct < 20 else "critical",
                    "type": "missing_values",
                    "column": col,
                    "message": f"Column '{col}' has {col_null_pct:.1f}% missing values "
                               f"({df[col].isnull().sum()}/{len(df)} rows)",
                })

        score = max(0, 100 - (null_pct * 5))  # Heavy penalty for missing data
        return score, issues

    def _assess_consistency(self, df: pd.DataFrame) -> Tuple[float, List[Dict]]:
        """Score consistency: duplicates, outliers, type issues."""
        issues = []
        penalties = 0

        # Duplicate detection
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            dup_pct = dup_count / len(df) * 100
            penalties += min(30, dup_pct * 3)
            issues.append({
                "severity": "warning",
                "type": "duplicates",
                "message": f"Found {dup_count} duplicate rows ({dup_pct:.1f}%)",
                "count": int(dup_count),
            })

        # Outlier detection (Z-score on numeric columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_total = 0
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 10:
                continue
            z_scores = np.abs((series - series.mean()) / (series.std() + 1e-10))
            outliers = (z_scores > self.zscore_thresh).sum()
            if outliers > 0:
                outlier_total += outliers
                issues.append({
                    "severity": "info",
                    "type": "outlier",
                    "column": col,
                    "message": f"Column '{col}' has {outliers} statistical outliers (|z| > {self.zscore_thresh})",
                    "count": int(outliers),
                })

        if outlier_total > 0:
            penalties += min(20, outlier_total * 2)

        score = max(0, 100 - penalties)
        return score, issues

    def _assess_timeliness(self, df: pd.DataFrame,
                           source: DataSource) -> Tuple[float, List[Dict]]:
        """Score timeliness based on recency of data."""
        issues = []

        # Try to find date columns
        date_cols = [c for c, t in source.schema.items()
                     if t in ("datetime", "date_string")]

        if not date_cols:
            # Try to detect date columns by name
            date_cols = [c for c in df.columns
                         if any(kw in c.lower() for kw in ("date", "time", "timestamp"))]

        if not date_cols:
            return 70.0, [{
                "severity": "info",
                "type": "no_date_column",
                "message": "No date/time column detected — timeliness cannot be fully assessed."
            }]

        # Check the most recent date in the data
        max_date = None
        for col in date_cols:
            try:
                dates = pd.to_datetime(df[col], errors="coerce").dropna()
                if len(dates) > 0:
                    col_max = dates.max()
                    if max_date is None or col_max > max_date:
                        max_date = col_max
            except Exception:
                continue

        if max_date is None:
            return 60.0, []

        days_old = (datetime.now() - max_date.to_pydatetime().replace(tzinfo=None)).days

        if days_old <= 7:
            score = 100
        elif days_old <= 30:
            score = 90
        elif days_old <= 90:
            score = 75
        elif days_old <= 365:
            score = 55
        else:
            score = 30

        if days_old > 30:
            issues.append({
                "severity": "warning",
                "type": "stale_data",
                "message": f"Most recent data is {days_old} days old (latest: {max_date.date()})",
            })

        return score, issues

    # ── Text Data Scoring ───────────────────────────────────────────────────

    def _score_text(self, source: DataSource,
                    report: QualityReport) -> QualityReport:
        """Simple quality scoring for text/document sources."""
        text = source.text_content

        # Completeness: is there substantial content?
        if len(text) > 2000:
            report.completeness_score = 95
        elif len(text) > 500:
            report.completeness_score = 75
        else:
            report.completeness_score = 50
            report.issues.append({
                "severity": "warning",
                "type": "short_document",
                "message": f"Document is only {len(text)} characters — may be incomplete."
            })

        # Consistency: basic checks
        report.consistency_score = 85  # Default for text

        # Timeliness: check if there's a date in the text
        import re
        date_patterns = re.findall(
            r'(?:January|February|March|April|May|June|July|August|September|'
            r'October|November|December)\s+\d{1,2},?\s+\d{4}', text
        )
        if date_patterns:
            try:
                latest = max(pd.to_datetime(d) for d in date_patterns)
                days_old = (datetime.now() - latest.to_pydatetime()).days
                report.timeliness_score = max(30, 100 - days_old * 0.3)
            except Exception:
                report.timeliness_score = 70
        else:
            report.timeliness_score = 65

        report.overall_score = (
            self.w_complete * report.completeness_score +
            self.w_consist * report.consistency_score +
            self.w_timely * report.timeliness_score
        )

        return report
