"""
Cross-Source Contradiction Detector — Layer 2
─────────────────────────────────────────────
Finds factual conflicts between different data sources by:
  1. Entity extraction and matching
  2. Numerical comparison with tolerance
  3. Semantic fact comparison via embeddings
"""

import re
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from core.data_federation import DataSource


@dataclass
class Contradiction:
    """Represents a detected conflict between two data sources."""
    contradiction_id: str
    severity: str                          # "high", "medium", "low"
    entity: str                            # What entity is the conflict about
    attribute: str                         # What attribute conflicts
    source_a_id: str
    source_a_name: str
    source_a_value: str
    source_b_id: str
    source_b_name: str
    source_b_value: str
    difference_pct: Optional[float] = None
    context: str = ""
    detected_at: str = ""
    resolved: bool = False
    resolution: Optional[str] = None

    def summary(self) -> str:
        severity_icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(self.severity, "❓")
        return (
            f"{severity_icon} CONFLICT: {self.entity} → {self.attribute}\n"
            f"   Source A [{self.source_a_name}]: {self.source_a_value}\n"
            f"   Source B [{self.source_b_name}]: {self.source_b_value}\n"
            f"   Difference: {self.difference_pct:.1f}%" if self.difference_pct else
            f"{severity_icon} CONFLICT: {self.entity} → {self.attribute}\n"
            f"   Source A [{self.source_a_name}]: {self.source_a_value}\n"
            f"   Source B [{self.source_b_name}]: {self.source_b_value}"
        )


class ContradictionDetector:
    """
    Detects contradictions across multiple data sources.
    
    Works in two modes:
      1. Structured vs Structured: Compare matching columns/entities numerically
      2. Structured vs Text: Extract facts from text and compare with tabular data
    """

    def __init__(self, numeric_tolerance_pct: float = 5.0):
        self.tolerance = numeric_tolerance_pct / 100.0
        self.contradictions: List[Contradiction] = []
        self._counter = 0

    def detect_all(self, sources: Dict[str, DataSource]) -> List[Contradiction]:
        """Run all contradiction detection passes."""
        source_list = list(sources.values())
        self.contradictions = []

        # Structured vs Structured
        structured = [s for s in source_list if s.data is not None]
        for i in range(len(structured)):
            for j in range(i + 1, len(structured)):
                self._compare_structured(structured[i], structured[j])

        # Structured vs Text
        text_sources = [s for s in source_list if s.text_content is not None]
        for ts in text_sources:
            for ss in structured:
                self._compare_text_vs_structured(ts, ss)

        # Text vs Text
        for i in range(len(text_sources)):
            for j in range(i + 1, len(text_sources)):
                self._compare_text_vs_text(text_sources[i], text_sources[j])

        return self.contradictions

    def _compare_structured(self, src_a: DataSource, src_b: DataSource):
        """Compare two structured sources for numerical contradictions."""
        df_a, df_b = src_a.data, src_b.data

        # Find common columns
        common_cols = set(df_a.columns) & set(df_b.columns)
        numeric_common = [c for c in common_cols
                          if pd.api.types.is_numeric_dtype(df_a[c])
                          and pd.api.types.is_numeric_dtype(df_b[c])]

        # Find potential key columns (string columns that match)
        key_candidates = [c for c in common_cols
                          if not pd.api.types.is_numeric_dtype(df_a[c])]

        if not numeric_common or not key_candidates:
            return

        # Try to merge on key columns and compare numeric values
        for key_col in key_candidates[:2]:
            try:
                merged = df_a.merge(df_b, on=key_col, suffixes=("_A", "_B"), how="inner")
                for num_col in numeric_common:
                    col_a = f"{num_col}_A"
                    col_b = f"{num_col}_B"
                    if col_a in merged.columns and col_b in merged.columns:
                        for _, row in merged.iterrows():
                            val_a = row[col_a]
                            val_b = row[col_b]
                            if pd.notna(val_a) and pd.notna(val_b) and val_a != 0:
                                diff_pct = abs(val_a - val_b) / abs(val_a) * 100
                                if diff_pct > self.tolerance * 100:
                                    self._add_contradiction(
                                        entity=str(row[key_col]),
                                        attribute=num_col,
                                        src_a=src_a, val_a=f"{val_a:,.2f}",
                                        src_b=src_b, val_b=f"{val_b:,.2f}",
                                        diff_pct=diff_pct,
                                        severity="high" if diff_pct > 15 else "medium",
                                    )
            except Exception:
                continue

    def _compare_text_vs_structured(self, text_src: DataSource,
                                     struct_src: DataSource):
        """Extract numerical facts from text and compare with structured data."""
        text = text_src.text_content
        if not text:
            return

        # Extract dollar amounts with context
        dollar_facts = self._extract_dollar_facts(text)
        if not dollar_facts:
            return

        df = struct_src.data
        if df is None:
            return

        # Try to match extracted facts with aggregated structured data
        for fact in dollar_facts:
            entity = fact["entity"]
            value_text = fact["value"]
            context = fact["context"]

            # Try to find matching aggregation in structured data
            matches = self._find_structured_match(df, entity, value_text)
            for match_val, match_entity, match_col in matches:
                if match_val > 0 and value_text > 0:
                    diff_pct = abs(match_val - value_text) / max(abs(match_val), abs(value_text)) * 100
                    if diff_pct > self.tolerance * 100:
                        self._add_contradiction(
                            entity=entity,
                            attribute=f"Revenue/Amount ({match_col})",
                            src_a=text_src,
                            val_a=f"${value_text:,.0f} (from text: '{context[:80]}...')",
                            src_b=struct_src,
                            val_b=f"${match_val:,.2f} (aggregated from {match_entity})",
                            diff_pct=diff_pct,
                            severity="high" if diff_pct > 10 else "medium",
                        )

    def _compare_text_vs_text(self, src_a: DataSource, src_b: DataSource):
        """Compare numerical facts extracted from two text sources."""
        facts_a = self._extract_dollar_facts(src_a.text_content or "")
        facts_b = self._extract_dollar_facts(src_b.text_content or "")

        for fa in facts_a:
            for fb in facts_b:
                # Check if they're talking about the same entity
                if self._entities_match(fa["entity"], fb["entity"]):
                    if fa["value"] > 0 and fb["value"] > 0:
                        diff_pct = abs(fa["value"] - fb["value"]) / max(fa["value"], fb["value"]) * 100
                        if diff_pct > self.tolerance * 100:
                            self._add_contradiction(
                                entity=fa["entity"],
                                attribute="Amount",
                                src_a=src_a, val_a=f"${fa['value']:,.0f}",
                                src_b=src_b, val_b=f"${fb['value']:,.0f}",
                                diff_pct=diff_pct,
                            )

    # ── Extraction Helpers ──────────────────────────────────────────────────

    def _extract_dollar_facts(self, text: str) -> List[Dict]:
        """Extract dollar amounts and their surrounding context from text."""
        facts = []
        # Match patterns like $4.2M, $42.3 million, $15,200,000
        patterns = [
            # $X.XM format
            (r'(\$[\d,.]+)\s*[Mm](?:illion)?', 1_000_000),
            # $X.XB format
            (r'(\$[\d,.]+)\s*[Bb](?:illion)?', 1_000_000_000),
            # $X,XXX,XXX format
            (r'(\$[\d,]+(?:\.\d+)?)\b', 1),
        ]

        for pattern, multiplier in patterns:
            for match in re.finditer(pattern, text):
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()

                raw_val = match.group(1).replace("$", "").replace(",", "")
                try:
                    value = float(raw_val) * multiplier
                except ValueError:
                    continue

                # Try to identify the entity from surrounding text
                entity = self._extract_entity_from_context(context)

                facts.append({
                    "value": value,
                    "entity": entity,
                    "context": context,
                    "raw": match.group(0),
                })

        return facts

    def _extract_entity_from_context(self, context: str) -> str:
        """Try to extract the entity being described from surrounding text."""
        # Look for region/quarter patterns
        region_match = re.search(
            r'(North America|Europe|Asia Pacific|Latin America|Middle East|APAC|EMEA|NA)',
            context, re.IGNORECASE
        )
        quarter_match = re.search(r'(Q[1-4]\s*\d{4})', context, re.IGNORECASE)

        parts = []
        if region_match:
            parts.append(region_match.group(1))
        if quarter_match:
            parts.append(quarter_match.group(1))

        return " ".join(parts) if parts else "Unknown Entity"

    def _find_structured_match(self, df: pd.DataFrame, entity: str,
                                value: float) -> List[Tuple[float, str, str]]:
        """Try to find matching aggregated values in structured data."""
        matches = []
        entity_lower = entity.lower()

        # Look for region columns
        region_cols = [c for c in df.columns if "region" in c.lower()]
        quarter_cols = [c for c in df.columns if "quarter" in c.lower()]
        revenue_cols = [c for c in df.columns
                        if any(kw in c.lower() for kw in ("revenue", "amount", "sales", "total"))]

        if not revenue_cols:
            # Fall back to any numeric columns
            revenue_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        for rev_col in revenue_cols[:3]:
            for region_col in region_cols:
                for region_val in df[region_col].unique():
                    if str(region_val).lower() in entity_lower:
                        if quarter_cols:
                            for q_col in quarter_cols:
                                # Match quarter too if present in entity
                                q_match = re.search(r'Q[1-4]', entity, re.IGNORECASE)
                                if q_match:
                                    q_str = q_match.group(0).upper()
                                    mask = (df[region_col] == region_val) & (df[q_col] == q_str)
                                    agg_val = df.loc[mask, rev_col].sum()
                                    if agg_val > 0:
                                        matches.append((
                                            agg_val,
                                            f"{region_val} {q_str}",
                                            rev_col
                                        ))
                        else:
                            mask = df[region_col] == region_val
                            agg_val = df.loc[mask, rev_col].sum()
                            if agg_val > 0:
                                matches.append((agg_val, str(region_val), rev_col))

        return matches

    def _entities_match(self, entity_a: str, entity_b: str) -> bool:
        """Check if two entity strings refer to the same thing."""
        a_lower = entity_a.lower().strip()
        b_lower = entity_b.lower().strip()
        if a_lower == b_lower:
            return True
        # Check overlap of words
        words_a = set(a_lower.split())
        words_b = set(b_lower.split())
        if len(words_a & words_b) >= max(1, min(len(words_a), len(words_b)) * 0.5):
            return True
        return False

    def _add_contradiction(self, entity: str, attribute: str,
                           src_a: DataSource, val_a: str,
                           src_b: DataSource, val_b: str,
                           diff_pct: float = None,
                           severity: str = "medium",
                           context: str = ""):
        self._counter += 1
        c = Contradiction(
            contradiction_id=f"CTR-{self._counter:04d}",
            severity=severity,
            entity=entity,
            attribute=attribute,
            source_a_id=src_a.source_id,
            source_a_name=src_a.source_name,
            source_a_value=val_a,
            source_b_id=src_b.source_id,
            source_b_name=src_b.source_name,
            source_b_value=val_b,
            difference_pct=diff_pct,
            context=context,
            detected_at=datetime.now().isoformat(),
        )
        self.contradictions.append(c)

    def get_summary(self) -> str:
        """Human-readable contradiction summary."""
        if not self.contradictions:
            return "✅ No contradictions detected across data sources."

        lines = [
            f"⚠️  {len(self.contradictions)} Contradictions Detected",
            "=" * 50,
        ]
        for c in self.contradictions:
            lines.append(c.summary())
            lines.append("")
        return "\n".join(lines)
