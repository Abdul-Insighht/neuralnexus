"""
Data Lineage Tracker — Layer 2
───────────────────────────────
Tracks the provenance chain of every fact used in an answer.
Every piece of information can be traced back to its exact source,
row, column, and transformation step.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json


@dataclass
class LineageNode:
    """A single node in the data lineage chain."""
    node_id: str
    source_id: str
    source_name: str
    data_type: str              # "raw_cell", "aggregation", "text_extract", "inference"
    value: Any = None
    column: Optional[str] = None
    row_index: Optional[int] = None
    text_span: Optional[str] = None       # For text sources: the exact span
    transformation: Optional[str] = None  # What operation produced this
    confidence: float = 1.0
    timestamp: str = ""
    children: List[str] = field(default_factory=list)  # downstream nodes


@dataclass
class LineageChain:
    """Complete provenance chain for a single fact in a response."""
    fact_id: str
    fact_text: str               # The fact as stated in the answer
    root_sources: List[str]      # Original source IDs
    nodes: List[LineageNode] = field(default_factory=list)
    confidence: float = 1.0

    def summary(self) -> str:
        sources = ", ".join(set(n.source_name for n in self.nodes))
        return (f"📋 Fact: \"{self.fact_text[:80]}...\"\n"
                f"   Sources: {sources}\n"
                f"   Confidence: {self.confidence:.0%}\n"
                f"   Chain depth: {len(self.nodes)} nodes")


class LineageTracker:
    """
    Tracks complete data provenance for every fact in the system.
    
    Supports:
      - Raw cell references (exact row/column in a CSV)
      - Text span references (exact substring in a document)
      - Aggregation lineage (SUM, AVG, etc.)
      - Inference lineage (derived by AI agent)
    """

    def __init__(self):
        self.chains: Dict[str, LineageChain] = {}
        self._node_counter = 0

    def track_raw_cell(self, source_id: str, source_name: str,
                       column: str, row_index: int, value: Any,
                       fact_text: str = "") -> LineageNode:
        """Track a fact from a specific cell in structured data."""
        node = self._create_node(
            source_id=source_id,
            source_name=source_name,
            data_type="raw_cell",
            value=value,
            column=column,
            row_index=row_index,
        )
        if fact_text:
            self._ensure_chain(fact_text, source_id, node)
        return node

    def track_text_extract(self, source_id: str, source_name: str,
                           text_span: str, value: Any = None,
                           fact_text: str = "") -> LineageNode:
        """Track a fact extracted from a text document."""
        node = self._create_node(
            source_id=source_id,
            source_name=source_name,
            data_type="text_extract",
            value=value,
            text_span=text_span,
        )
        if fact_text:
            self._ensure_chain(fact_text, source_id, node)
        return node

    def track_aggregation(self, source_id: str, source_name: str,
                          column: str, operation: str, value: Any,
                          input_nodes: List[LineageNode] = None,
                          fact_text: str = "") -> LineageNode:
        """Track an aggregated value (e.g., SUM of revenue)."""
        node = self._create_node(
            source_id=source_id,
            source_name=source_name,
            data_type="aggregation",
            value=value,
            column=column,
            transformation=f"{operation}({column})",
        )
        if input_nodes:
            node.children = [n.node_id for n in input_nodes]
        if fact_text:
            self._ensure_chain(fact_text, source_id, node)
        return node

    def track_inference(self, source_ids: List[str],
                        source_names: List[str],
                        reasoning: str, value: Any,
                        confidence: float = 0.8,
                        fact_text: str = "") -> LineageNode:
        """Track a fact inferred by an AI agent."""
        node = self._create_node(
            source_id=source_ids[0] if source_ids else "agent",
            source_name=", ".join(source_names),
            data_type="inference",
            value=value,
            transformation=f"AI Inference: {reasoning[:200]}",
            confidence=confidence,
        )
        if fact_text:
            for sid in source_ids:
                self._ensure_chain(fact_text, sid, node)
            if fact_text in self.chains:
                self.chains[fact_text].confidence = confidence
        return node

    def get_lineage_for_fact(self, fact_text: str) -> Optional[LineageChain]:
        """Retrieve the full lineage chain for a given fact."""
        # Exact match
        if fact_text in self.chains:
            return self.chains[fact_text]
        # Partial match
        for key, chain in self.chains.items():
            if fact_text.lower() in key.lower() or key.lower() in fact_text.lower():
                return chain
        return None

    def get_all_chains(self) -> List[LineageChain]:
        """Return all tracked lineage chains."""
        return list(self.chains.values())

    def get_sources_used(self) -> List[str]:
        """Return unique source names used across all chains."""
        sources = set()
        for chain in self.chains.values():
            for node in chain.nodes:
                sources.add(node.source_name)
        return sorted(sources)

    def to_dict(self) -> Dict:
        """Serialize all lineage data for display."""
        result = {}
        for fact_text, chain in self.chains.items():
            result[fact_text] = {
                "fact_id": chain.fact_id,
                "confidence": chain.confidence,
                "sources": chain.root_sources,
                "nodes": [
                    {
                        "source": n.source_name,
                        "type": n.data_type,
                        "value": str(n.value)[:100] if n.value else None,
                        "column": n.column,
                        "row": n.row_index,
                        "span": n.text_span[:80] if n.text_span else None,
                        "transform": n.transformation,
                        "confidence": n.confidence,
                    }
                    for n in chain.nodes
                ],
            }
        return result

    # ── Internal ────────────────────────────────────────────────────────────

    def _create_node(self, **kwargs) -> LineageNode:
        self._node_counter += 1
        return LineageNode(
            node_id=f"LN-{self._node_counter:05d}",
            timestamp=datetime.now().isoformat(),
            **kwargs,
        )

    def _ensure_chain(self, fact_text: str, source_id: str,
                      node: LineageNode):
        if fact_text not in self.chains:
            self.chains[fact_text] = LineageChain(
                fact_id=f"FACT-{len(self.chains)+1:04d}",
                fact_text=fact_text,
                root_sources=[source_id],
            )
        chain = self.chains[fact_text]
        chain.nodes.append(node)
        if source_id not in chain.root_sources:
            chain.root_sources.append(source_id)
