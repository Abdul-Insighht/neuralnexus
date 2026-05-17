"""
Forecaster Agent
────────────────
Predictive intelligence: temporal pattern detection, trend analysis,
risk scoring, and forward-looking insights from enterprise data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from agents.base_agent import BaseAgent, AgentResponse
from core.data_federation import DataSource


class ForecasterAgent(BaseAgent):
    """
    Detects patterns in time-series enterprise data and generates
    forward-looking insights, risk scores, and forecasts.
    """

    def __init__(self):
        super().__init__(
            agent_name="ForecasterAgent",
            model_key="forecaster",
            system_instruction=(
                "You are the ForecasterAgent — an enterprise data forecasting specialist. "
                "You analyze time-series patterns, trends, and seasonality to generate "
                "actionable predictions. You always provide:\n"
                "1. Current trend direction and strength\n"
                "2. Key patterns detected (seasonality, cycles, anomalies)\n"
                "3. Forward-looking forecast with confidence intervals\n"
                "4. Risk factors and their probability scores\n"
                "5. Specific, actionable recommendations\n\n"
                "Use specific numbers, percentages, and time ranges. "
                "Rate your confidence as a percentage (0-100%)."
            ),
        )

    def analyze_trends(self, source: DataSource,
                       date_col: str = None,
                       metric_cols: List[str] = None) -> AgentResponse:
        """Analyze trends in a data source."""
        if source.data is None or len(source.data) == 0:
            return AgentResponse(
                agent_name=self.agent_name,
                content="No structured data available for trend analysis.",
                confidence=0.0,
            )

        df = source.data

        # Auto-detect date column
        if date_col is None:
            date_candidates = [c for c in df.columns
                               if any(kw in c.lower() for kw in ("date", "time"))]
            date_col = date_candidates[0] if date_candidates else None

        # Auto-detect metric columns
        if metric_cols is None:
            metric_cols = list(df.select_dtypes(include=[np.number]).columns[:5])

        # Compute statistics
        stats = self._compute_trend_stats(df, date_col, metric_cols)

        context = (
            f"DATA SOURCE: {source.source_name}\n"
            f"Period: {stats.get('period', 'Unknown')}\n"
            f"Rows: {len(df):,}\n\n"
            f"COMPUTED STATISTICS:\n{self._format_stats(stats)}\n"
        )

        prompt = (
            "Analyze the trends and patterns in this enterprise data. Provide:\n"
            "1. **Trend Summary**: Direction, strength, and key inflection points\n"
            "2. **Patterns**: Seasonality, cycles, or recurring patterns\n"
            "3. **Forecast**: Next quarter/period predictions with confidence intervals\n"
            "4. **Risk Assessment**: Top 3 risks with probability scores (0-100%)\n"
            "5. **Recommendations**: 3 specific actions for the enterprise team\n"
            "6. **Confidence**: Your overall confidence (0-100%)\n"
        )

        response = self.query(prompt, context=context)
        response.sources_used = [source.source_name]
        response.metadata["stats"] = stats
        return response

    def detect_seasonality(self, series: pd.Series,
                            periods_to_check: List[int] = None) -> Dict:
        """Detect seasonality in a numeric series."""
        if len(series) < 10:
            return {"has_seasonality": False, "reason": "Insufficient data"}

        if periods_to_check is None:
            periods_to_check = [4, 7, 12, 30, 90, 365]

        results = {}
        for period in periods_to_check:
            if len(series) < period * 2:
                continue

            try:
                # Autocorrelation at this lag
                autocorr = series.autocorr(lag=period)
                if abs(autocorr) > 0.3:
                    results[period] = {
                        "autocorrelation": float(autocorr),
                        "strength": "strong" if abs(autocorr) > 0.6 else "moderate",
                    }
            except Exception:
                continue

        return {
            "has_seasonality": len(results) > 0,
            "seasonal_periods": results,
        }

    def generate_proactive_insights(self, sources: Dict[str, DataSource]) -> AgentResponse:
        """Generate proactive insights across all data sources without being asked."""
        insights = []

        for sid, source in sources.items():
            if source.data is None:
                continue

            df = source.data
            numeric_cols = df.select_dtypes(include=[np.number]).columns

            for col in numeric_cols[:3]:
                series = df[col].dropna()
                if len(series) < 10:
                    continue

                # Trend direction
                recent = series.tail(int(len(series) * 0.3))
                older = series.head(int(len(series) * 0.3))
                trend_pct = ((recent.mean() - older.mean()) / (older.mean() + 1e-10)) * 100

                if abs(trend_pct) > 5:
                    direction = "📈 increasing" if trend_pct > 0 else "📉 decreasing"
                    insights.append(
                        f"• {source.source_name} → '{col}': {direction} by {abs(trend_pct):.1f}% "
                        f"(recent avg: {recent.mean():,.2f} vs historical avg: {older.mean():,.2f})"
                    )

                # Volatility check
                cv = series.std() / (series.mean() + 1e-10) * 100
                if cv > 50:
                    insights.append(
                        f"• ⚡ High volatility in {source.source_name} → '{col}': "
                        f"CV = {cv:.1f}% (may need attention)"
                    )

        if not insights:
            return AgentResponse(
                agent_name=self.agent_name,
                content="📊 All metrics are within normal ranges. No proactive alerts.",
                confidence=0.85,
            )

        context = "DETECTED PATTERNS AND TRENDS:\n" + "\n".join(insights)

        prompt = (
            "Based on these automatically detected patterns, generate a proactive "
            "intelligence briefing for enterprise leadership. Prioritize the most "
            "impactful trends and provide actionable recommendations. "
            "Format as a concise executive briefing with risk scores."
        )

        response = self.query(prompt, context=context)
        response.metadata["raw_insights"] = insights
        return response

    # ── Internal ────────────────────────────────────────────────────────────

    def _compute_trend_stats(self, df: pd.DataFrame, date_col: str,
                              metric_cols: List[str]) -> Dict:
        """Compute trend statistics for all metric columns."""
        stats = {}

        if date_col:
            try:
                dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
                if len(dates) > 0:
                    stats["period"] = f"{dates.min().date()} to {dates.max().date()}"
                    stats["days_span"] = (dates.max() - dates.min()).days
            except Exception:
                stats["period"] = "Unknown"

        for col in metric_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            col_stats = {
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
                "cv": float(series.std() / (series.mean() + 1e-10) * 100),
                "count": int(len(series)),
            }

            # Trend: compare recent 30% vs older 30%
            n = len(series)
            if n >= 10:
                recent = series.tail(int(n * 0.3))
                older = series.head(int(n * 0.3))
                col_stats["trend_pct"] = float(
                    ((recent.mean() - older.mean()) / (older.mean() + 1e-10)) * 100
                )
                col_stats["trend_direction"] = "up" if col_stats["trend_pct"] > 2 else \
                    "down" if col_stats["trend_pct"] < -2 else "stable"

            # Seasonality check
            seasonal = self.detect_seasonality(series)
            col_stats["seasonality"] = seasonal

            stats[col] = col_stats

        return stats

    def _format_stats(self, stats: Dict) -> str:
        """Format statistics for prompt context."""
        lines = []
        for key, value in stats.items():
            if isinstance(value, dict) and "mean" in value:
                lines.append(
                    f"  {key}: mean={value['mean']:,.2f}, std={value['std']:,.2f}, "
                    f"trend={value.get('trend_direction', '?')} "
                    f"({value.get('trend_pct', 0):+.1f}%)"
                )
            elif isinstance(value, str):
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)
