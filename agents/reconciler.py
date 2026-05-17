"""
Reconciler Agent
────────────────
Resolves contradictions between data sources using Gemini reasoning.
Produces trust-weighted best-truth recommendations with uncertainty quantification.
"""

from typing import Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse
from core.contradiction_detector import Contradiction
from core.data_federation import DataSource
from core.quality_scorer import QualityReport


class ReconcilerAgent(BaseAgent):
    """
    Resolves cross-source contradictions by reasoning about:
      - Source credibility and quality scores
      - Data recency
      - Context and methodology differences
      - Domain-specific knowledge
    """

    def __init__(self):
        super().__init__(
            agent_name="ReconcilerAgent",
            model_key="reconciler",
            system_instruction=(
                "You are the ReconcilerAgent — an expert at resolving data contradictions "
                "in enterprise environments. When two data sources disagree, you analyze "
                "the credibility, recency, methodology, and context of each source to "
                "determine the most likely truth. You always provide:\n"
                "1. Your recommended 'best truth' value\n"
                "2. An uncertainty range\n"
                "3. Clear reasoning for WHY you trust one source over another\n"
                "4. A confidence percentage (0-100%)\n"
                "5. Actionable recommendations for the data team\n\n"
                "Be specific with numbers. Never say 'it depends' without giving a recommendation."
            ),
        )

    def reconcile(self, contradiction: Contradiction,
                  source_a: Optional[DataSource] = None,
                  source_b: Optional[DataSource] = None,
                  quality_a: Optional[QualityReport] = None,
                  quality_b: Optional[QualityReport] = None) -> AgentResponse:
        """Reconcile a single contradiction."""

        context_parts = [
            f"CONTRADICTION DETAILS:",
            f"  Entity: {contradiction.entity}",
            f"  Attribute: {contradiction.attribute}",
            f"  Source A: '{contradiction.source_a_name}' says: {contradiction.source_a_value}",
            f"  Source B: '{contradiction.source_b_name}' says: {contradiction.source_b_value}",
        ]

        if contradiction.difference_pct:
            context_parts.append(f"  Numerical difference: {contradiction.difference_pct:.1f}%")

        # Add source metadata
        if source_a:
            context_parts.append(f"\nSOURCE A METADATA ({contradiction.source_a_name}):")
            context_parts.append(f"  Type: {source_a.source_type}")
            context_parts.append(f"  Credibility: {source_a.credibility_score:.0%}")
            if source_a.data is not None:
                context_parts.append(f"  Data size: {source_a.row_count} rows × {source_a.column_count} columns")
            if quality_a:
                context_parts.append(f"  Quality Score: {quality_a.overall_score:.1f}/100 (Grade {quality_a.grade})")
                context_parts.append(f"    Completeness: {quality_a.completeness_score:.0f}, "
                                     f"Consistency: {quality_a.consistency_score:.0f}, "
                                     f"Timeliness: {quality_a.timeliness_score:.0f}")

        if source_b:
            context_parts.append(f"\nSOURCE B METADATA ({contradiction.source_b_name}):")
            context_parts.append(f"  Type: {source_b.source_type}")
            context_parts.append(f"  Credibility: {source_b.credibility_score:.0%}")
            if source_b.data is not None:
                context_parts.append(f"  Data size: {source_b.row_count} rows × {source_b.column_count} columns")
            if quality_b:
                context_parts.append(f"  Quality Score: {quality_b.overall_score:.1f}/100 (Grade {quality_b.grade})")

        context = "\n".join(context_parts)

        prompt = (
            "Analyze this data contradiction and provide a reconciliation.\n\n"
            "You must provide:\n"
            "1. **Best Truth**: Your recommended correct value with reasoning\n"
            "2. **Uncertainty Range**: What range of values is plausible\n"
            "3. **Trust Analysis**: Why you trust one source over the other, citing specific metrics\n"
            "4. **Root Cause**: What likely caused this discrepancy\n"
            "5. **Action Items**: What should the data team do to prevent this\n"
            "6. **Confidence**: Your confidence in this reconciliation (0-100%)\n"
        )

        response = self.query(prompt, context=context)
        response.sources_used = [contradiction.source_a_name, contradiction.source_b_name]
        response.metadata["contradiction_id"] = contradiction.contradiction_id
        response.metadata["entity"] = contradiction.entity
        return response

    def reconcile_all(self, contradictions: List[Contradiction],
                      sources: Dict[str, DataSource] = None,
                      quality_reports: Dict[str, QualityReport] = None) -> List[AgentResponse]:
        """Reconcile all contradictions."""
        results = []

        for c in contradictions:
            src_a = None
            src_b = None
            qa = None
            qb = None

            if sources:
                src_a = sources.get(c.source_a_id)
                src_b = sources.get(c.source_b_id)
            if quality_reports:
                qa = quality_reports.get(c.source_a_id)
                qb = quality_reports.get(c.source_b_id)

            result = self.reconcile(c, src_a, src_b, qa, qb)
            results.append(result)

        return results

    def generate_reconciliation_report(self, contradictions: List[Contradiction],
                                        resolutions: List[AgentResponse]) -> AgentResponse:
        """Generate a comprehensive reconciliation report."""
        report_context = []
        for c, r in zip(contradictions, resolutions):
            report_context.append(
                f"CONTRADICTION: {c.entity} → {c.attribute}\n"
                f"  Source A: {c.source_a_value} | Source B: {c.source_b_value}\n"
                f"  Resolution: {r.content[:300]}...\n"
                f"  Confidence: {r.confidence:.0%}\n"
            )

        prompt = (
            f"Generate an executive summary of {len(contradictions)} data contradictions "
            f"and their resolutions. Highlight the most critical conflicts, overall data "
            f"integrity health, and top 3 recommendations for the enterprise data team.\n\n"
            f"Include an overall data integrity score (0-100)."
        )

        return self.query(prompt, context="\n".join(report_context))
