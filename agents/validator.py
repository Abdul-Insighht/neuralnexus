"""
Validator Agent
───────────────
Continuous anomaly detection: Z-score outliers, temporal drift,
data quality flags, and proactive alerting.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from agents.base_agent import BaseAgent, AgentResponse
from core.data_federation import DataSource
from core.quality_scorer import QualityReport


@dataclass
class Anomaly:
    """A detected anomaly."""
    anomaly_id: str
    severity: str           # critical, warning, info
    anomaly_type: str       # outlier, drift, quality_drop, spike, pattern_break
    source_name: str
    column: Optional[str] = None
    description: str = ""
    value: Optional[float] = None
    expected_range: Optional[str] = None
    detected_at: str = ""

    @property
    def icon(self) -> str:
        return {"critical": "🔴", "warning": "🟠", "info": "🟡"}.get(self.severity, "❓")


class ValidatorAgent(BaseAgent):
    """
    Autonomously scans data for anomalies and quality issues.
    
    Detection methods:
      - Z-score outlier detection
      - IQR-based outlier detection
      - Temporal drift (CUSUM-like)
      - Sudden spikes/drops
      - Data quality degradation alerts
    """

    def __init__(self, zscore_threshold: float = 2.5,
                 iqr_multiplier: float = 1.5):
        super().__init__(
            agent_name="ValidatorAgent",
            model_key="validator",
            system_instruction=(
                "You are the ValidatorAgent — a data quality watchdog for enterprise systems. "
                "Your role is to detect anomalies, data drift, and quality issues proactively. "
                "When you find issues, explain them clearly with specific numbers and suggest "
                "what action should be taken. Always rate severity as CRITICAL, WARNING, or INFO."
            ),
        )
        self.zscore_thresh = zscore_threshold
        self.iqr_mult = iqr_multiplier
        self.anomalies: List[Anomaly] = []
        self._counter = 0

    def scan_all(self, sources: Dict[str, DataSource],
                 quality_reports: Dict[str, QualityReport] = None) -> List[Anomaly]:
        """Run full anomaly scan across all data sources."""
        self.anomalies = []

        for sid, source in sources.items():
            if source.data is not None and len(source.data) > 0:
                self._scan_structured(source)

            # Check quality reports for low scores
            if quality_reports and sid in quality_reports:
                report = quality_reports[sid]
                if report.overall_score < 50:
                    self._add_anomaly(
                        severity="critical",
                        anomaly_type="quality_drop",
                        source_name=source.source_name,
                        description=(f"Data quality score critically low: "
                                     f"{report.overall_score:.1f}/100 (Grade {report.grade}). "
                                     f"Issues: {len(report.issues)}"),
                    )
                elif report.overall_score < 70:
                    self._add_anomaly(
                        severity="warning",
                        anomaly_type="quality_drop",
                        source_name=source.source_name,
                        description=(f"Data quality score below threshold: "
                                     f"{report.overall_score:.1f}/100 (Grade {report.grade})"),
                    )

        return self.anomalies

    def get_ai_analysis(self, anomalies: List[Anomaly] = None) -> AgentResponse:
        """Use Gemini to analyze detected anomalies and provide insights."""
        anomalies = anomalies or self.anomalies

        if not anomalies:
            return AgentResponse(
                agent_name=self.agent_name,
                content="✅ No anomalies detected. All data sources appear healthy.",
                confidence=0.95,
            )

        anomaly_text = "\n".join([
            f"- [{a.severity.upper()}] {a.anomaly_type} in '{a.source_name}'"
            f"{f' (column: {a.column})' if a.column else ''}: {a.description}"
            for a in anomalies
        ])

        prompt = f"""Analyze these {len(anomalies)} detected data anomalies and provide:
1. A priority-ranked summary of the most critical issues
2. Likely root causes for each anomaly
3. Recommended actions for the enterprise data team
4. Overall data health assessment (score 0-100)

DETECTED ANOMALIES:
{anomaly_text}

Provide your analysis in a clear, structured format. Include confidence percentage."""

        return self.query(prompt)

    # ── Detection Methods ───────────────────────────────────────────────────

    def _scan_structured(self, source: DataSource):
        """Run all detection methods on a structured source."""
        df = source.data
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 5:
                continue

            # Z-score outliers
            self._detect_zscore_outliers(series, col, source.source_name)

            # IQR outliers
            self._detect_iqr_outliers(series, col, source.source_name)

            # Sudden spikes
            self._detect_spikes(series, col, source.source_name)

        # Check for date-ordered drift
        date_cols = [c for c in df.columns
                     if any(kw in c.lower() for kw in ("date", "time"))]
        if date_cols and numeric_cols.size > 0:
            self._detect_temporal_drift(df, date_cols[0], numeric_cols[0],
                                        source.source_name)

    def _detect_zscore_outliers(self, series: pd.Series, col: str,
                                 source_name: str):
        """Detect outliers using Z-score method."""
        mean = series.mean()
        std = series.std()
        if std == 0:
            return

        z_scores = np.abs((series - mean) / std)
        outliers = series[z_scores > self.zscore_thresh]

        for idx, val in outliers.items():
            z = float(z_scores[idx])
            self._add_anomaly(
                severity="critical" if z > 4 else "warning",
                anomaly_type="outlier",
                source_name=source_name,
                column=col,
                value=float(val),
                description=(f"Statistical outlier: value={val:,.2f}, z-score={z:.2f}. "
                             f"Expected range: [{mean - 2*std:,.2f}, {mean + 2*std:,.2f}]"),
                expected_range=f"[{mean - 2*std:,.2f}, {mean + 2*std:,.2f}]",
            )

    def _detect_iqr_outliers(self, series: pd.Series, col: str,
                               source_name: str):
        """Detect outliers using IQR method."""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return

        lower = q1 - self.iqr_mult * iqr
        upper = q3 + self.iqr_mult * iqr

        outliers = series[(series < lower) | (series > upper)]
        if len(outliers) > 0 and len(outliers) <= 5:
            for idx, val in outliers.items():
                self._add_anomaly(
                    severity="warning",
                    anomaly_type="outlier",
                    source_name=source_name,
                    column=col,
                    value=float(val),
                    description=(f"IQR outlier: value={val:,.2f} outside "
                                 f"[{lower:,.2f}, {upper:,.2f}]"),
                )

    def _detect_spikes(self, series: pd.Series, col: str, source_name: str):
        """Detect sudden spikes or drops (>300% change)."""
        if len(series) < 3:
            return

        pct_change = series.pct_change().abs()
        spikes = pct_change[pct_change > 3.0]  # >300% change

        for idx, change in spikes.items():
            if pd.notna(change):
                val = series.get(idx, 0)
                self._add_anomaly(
                    severity="critical",
                    anomaly_type="spike",
                    source_name=source_name,
                    column=col,
                    value=float(val) if pd.notna(val) else None,
                    description=(f"Sudden spike/drop: {change*100:.0f}% change detected "
                                 f"at index {idx}. Value: {val:,.2f}"),
                )

    def _detect_temporal_drift(self, df: pd.DataFrame, date_col: str,
                                metric_col: str, source_name: str):
        """Detect temporal drift using rolling statistics."""
        try:
            df_sorted = df.sort_values(date_col).copy()
            series = df_sorted[metric_col].dropna()

            if len(series) < 20:
                return

            # Compare first half vs second half statistics
            mid = len(series) // 2
            first_half = series.iloc[:mid]
            second_half = series.iloc[mid:]

            mean_shift = abs(second_half.mean() - first_half.mean()) / (first_half.std() + 1e-10)
            var_ratio = second_half.std() / (first_half.std() + 1e-10)

            if mean_shift > 2.0:
                self._add_anomaly(
                    severity="warning",
                    anomaly_type="drift",
                    source_name=source_name,
                    column=metric_col,
                    description=(f"Temporal drift detected in '{metric_col}': "
                                 f"mean shifted by {mean_shift:.1f} std devs "
                                 f"between first and second half of data period."),
                )

            if var_ratio > 2.0 or var_ratio < 0.5:
                self._add_anomaly(
                    severity="info",
                    anomaly_type="drift",
                    source_name=source_name,
                    column=metric_col,
                    description=(f"Variance change in '{metric_col}': "
                                 f"variability ratio = {var_ratio:.2f}x between periods."),
                )
        except Exception:
            pass

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _add_anomaly(self, severity: str, anomaly_type: str,
                     source_name: str, column: str = None,
                     description: str = "", value: float = None,
                     expected_range: str = None):
        self._counter += 1
        self.anomalies.append(Anomaly(
            anomaly_id=f"ANM-{self._counter:04d}",
            severity=severity,
            anomaly_type=anomaly_type,
            source_name=source_name,
            column=column,
            description=description,
            value=value,
            expected_range=expected_range,
            detected_at=datetime.now().isoformat(),
        ))

    def get_summary(self) -> str:
        """Get anomaly summary."""
        if not self.anomalies:
            return "✅ No anomalies detected."

        critical = sum(1 for a in self.anomalies if a.severity == "critical")
        warning = sum(1 for a in self.anomalies if a.severity == "warning")
        info = sum(1 for a in self.anomalies if a.severity == "info")

        lines = [
            f"🔍 Anomaly Scan Results: {len(self.anomalies)} issues found",
            f"   🔴 Critical: {critical} | 🟠 Warning: {warning} | 🟡 Info: {info}",
            "─" * 50,
        ]
        for a in self.anomalies:
            lines.append(f"  {a.icon} [{a.anomaly_type}] {a.source_name}"
                         f"{f' → {a.column}' if a.column else ''}")
            lines.append(f"    {a.description}")
        return "\n".join(lines)
