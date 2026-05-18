"""
Dynamic Knowledge Graph — Layer 3
──────────────────────────────────
Entity-relation graph with temporal edges, contradiction tracking,
and confidence scoring. Built on NetworkX with PyVis visualization.
"""

import networkx as nx
import re
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field


@dataclass
class KGEntity:
    """An entity node in the knowledge graph."""
    entity_id: str
    name: str
    entity_type: str        # company, metric, person, region, product, date, event
    attributes: Dict[str, Any] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    first_seen: str = ""
    last_updated: str = ""
    confidence: float = 1.0


@dataclass
class KGRelation:
    """A directed edge in the knowledge graph."""
    relation_id: str
    source_entity: str      # entity_id
    target_entity: str      # entity_id
    relation_type: str      # reports_to, contradicts, supports, etc.
    weight: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    data_source: str = ""


class DynamicKnowledgeGraph:
    """
    Temporal knowledge graph with contradiction-aware edges.
    
    Features:
      - Auto-extraction of entities from structured and text data
      - Temporal validity on edges
      - Contradiction edges with confidence
      - Subgraph queries for specific entities
      - PyVis export for interactive visualization
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities: Dict[str, KGEntity] = {}
        self.relations: List[KGRelation] = []
        self._entity_counter = 0
        self._relation_counter = 0
        self._name_index: Dict[str, str] = {}

    def add_entity(self, name: str, entity_type: str,
                   attributes: Dict = None, source: str = "",
                   confidence: float = 1.0) -> str:
        """Add or update an entity. Returns entity_id."""
        if not hasattr(self, "_name_index"):
            self._name_index = {e.name.lower().strip(): eid for eid, e in self.entities.items()}

        # Check for existing entity with same name and type
        existing_id = self._find_entity(name, entity_type)
        if existing_id:
            entity = self.entities[existing_id]
            if attributes:
                entity.attributes.update(attributes)
            if source and source not in entity.sources:
                entity.sources.append(source)
            entity.last_updated = datetime.now().isoformat()
            return existing_id

        self._entity_counter += 1
        entity_id = f"E-{self._entity_counter:05d}"

        entity = KGEntity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            attributes=attributes or {},
            sources=[source] if source else [],
            first_seen=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            confidence=confidence,
        )
        self.entities[entity_id] = entity
        self._name_index[name.lower().strip()] = entity_id
        self.graph.add_node(entity_id, label=name, type=entity_type,
                           confidence=confidence)
        return entity_id

    def add_relation(self, source_id: str, target_id: str,
                     relation_type: str, weight: float = 1.0,
                     confidence: float = 1.0, metadata: Dict = None,
                     data_source: str = "",
                     valid_from: str = None, valid_to: str = None) -> str:
        """Add a directed edge between two entities."""
        self._relation_counter += 1
        rel_id = f"R-{self._relation_counter:05d}"

        relation = KGRelation(
            relation_id=rel_id,
            source_entity=source_id,
            target_entity=target_id,
            relation_type=relation_type,
            weight=weight,
            confidence=confidence,
            metadata=metadata or {},
            data_source=data_source,
            valid_from=valid_from,
            valid_to=valid_to,
        )
        self.relations.append(relation)

        # Edge color based on relation type
        color_map = {
            "contradicts": "#FF4444",
            "supports": "#44BB44",
            "caused_by": "#FF8800",
            "correlates_with": "#4488FF",
            "part_of": "#888888",
            "reports_to": "#AA44FF",
            "measured_at": "#44DDDD",
            "produced_by": "#FFAA44",
        }
        color = color_map.get(relation_type, "#CCCCCC")

        self.graph.add_edge(
            source_id, target_id,
            relation=relation_type,
            weight=weight,
            color=color,
            confidence=confidence,
            title=f"{relation_type} (conf: {confidence:.2f})",
        )
        return rel_id

    def build_from_structured(self, df: pd.DataFrame, source_name: str,
                              entity_columns: List[str] = None,
                              metric_columns: List[str] = None):
        """Auto-extract entities and relations from a DataFrame."""
        if entity_columns is None:
            # Auto-detect: string columns are entities
            entity_columns = [c for c in df.columns
                              if df[c].dtype == "object"
                              and df[c].nunique() < 100]
        if metric_columns is None:
            metric_columns = [c for c in df.columns
                              if pd.api.types.is_numeric_dtype(df[c])]

        # Create entity nodes for each unique value in entity columns
        for col in entity_columns:
            for val in df[col].dropna().unique():
                self.add_entity(
                    name=str(val),
                    entity_type=self._infer_entity_type(col),
                    source=source_name,
                    attributes={"column": col},
                )

        # Create metric entities and relations
        for _, row in df.iterrows():
            entity_ids = []
            for col in entity_columns:
                if pd.notna(row.get(col)):
                    eid = self._find_entity(str(row[col]))
                    if eid:
                        entity_ids.append(eid)

            for metric_col in metric_columns:
                if pd.notna(row.get(metric_col)):
                    metric_id = self.add_entity(
                        name=f"{metric_col}={row[metric_col]:.2f}" if isinstance(row[metric_col], float) else f"{metric_col}={row[metric_col]}",
                        entity_type="metric",
                        attributes={"value": row[metric_col], "column": metric_col},
                        source=source_name,
                    )

                    # Link entity to its metrics
                    for eid in entity_ids[:2]:  # Limit to avoid explosion
                        self.add_relation(
                            eid, metric_id, "measured_at",
                            data_source=source_name,
                        )

            # Link co-occurring entities
            for i in range(len(entity_ids)):
                for j in range(i + 1, min(i + 2, len(entity_ids))):
                    self.add_relation(
                        entity_ids[i], entity_ids[j], "correlates_with",
                        data_source=source_name,
                        weight=0.5,
                    )

    def build_from_text(self, text: str, source_name: str):
        """Extract entities and relations from unstructured text."""
        # Extract named entities using regex patterns
        patterns = {
            "company": r'(NexaCorp|Google|Microsoft|NASA)',
            "person": r'(?:CEO|CFO|CTO|VP|Director)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            "product": r'(Enterprise Suite|Cloud Platform|Analytics Pro|Security Shield|AI Toolkit)',
            "region": r'(North America|Europe|Asia Pacific|Latin America|Middle East|APAC|EMEA)',
            "metric": r'(\$[\d,.]+\s*[MBK]?(?:illion)?)',
            "quarter": r'(Q[1-4]\s*\d{4}|FY\d{4})',
        }

        for entity_type, pattern in patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1) if match.lastindex else match.group(0)
                self.add_entity(name=name.strip(), entity_type=entity_type,
                               source=source_name)

        # Extract key relationships from text patterns
        # "revenue of $X.XM" → link region to revenue metric
        rev_pattern = r'(North America|Europe|Asia Pacific|Latin America|Middle East)\s+(\$[\d,.]+[MBK]?)'
        for match in re.finditer(rev_pattern, text, re.IGNORECASE):
            region_id = self._find_entity(match.group(1))
            metric_id = self._find_entity(match.group(2))
            if region_id and metric_id:
                self.add_relation(region_id, metric_id, "produced_by",
                                 data_source=source_name)

    def add_contradiction_edge(self, entity_a_name: str, entity_b_name: str,
                                attribute: str, val_a: str, val_b: str,
                                source_a: str, source_b: str):
        """Add a contradiction edge between conflicting facts."""
        eid_a = self._find_entity(entity_a_name) or \
                self.add_entity(entity_a_name, "fact", source=source_a)
        eid_b = self._find_entity(entity_b_name) or \
                self.add_entity(entity_b_name, "fact", source=source_b)

        self.add_relation(
            eid_a, eid_b, "contradicts",
            confidence=0.9,
            metadata={
                "attribute": attribute,
                "value_a": val_a,
                "value_b": val_b,
                "source_a": source_a,
                "source_b": source_b,
            },
        )

    def query_entity_by_id(self, eid: str) -> Dict:
        """Get all information about an entity by its ID (fast O(1) connections lookup)."""
        if eid not in self.entities:
            return {"found": False}

        entity = self.entities[eid]
        neighbors = list(self.graph.neighbors(eid))
        predecessors = list(self.graph.predecessors(eid))

        connections = []
        for n in neighbors:
            edge_data = self.graph.edges[eid, n]
            connections.append({
                "target": self.entities[n].name if n in self.entities else n,
                "relation": edge_data.get("relation", "related"),
                "confidence": edge_data.get("confidence", 1.0),
            })
        for p in predecessors:
            edge_data = self.graph.edges[p, eid]
            connections.append({
                "source": self.entities[p].name if p in self.entities else p,
                "relation": edge_data.get("relation", "related"),
                "confidence": edge_data.get("confidence", 1.0),
            })

        return {
            "found": True,
            "entity": {
                "id": entity.entity_id,
                "name": entity.name,
                "type": entity.entity_type,
                "attributes": entity.attributes,
                "sources": entity.sources,
                "confidence": entity.confidence,
            },
            "connections": connections,
            "contradiction_count": sum(1 for c in connections
                                       if c.get("relation") == "contradicts"),
        }

    def query_entity(self, name: str) -> Dict:
        """Get all information about an entity and its connections."""
        eid = self._find_entity(name)
        if not eid:
            return {"found": False, "name": name}
        return self.query_entity_by_id(eid)

    def get_contradictions(self) -> List[Dict]:
        """Get all contradiction edges."""
        contradictions = []
        for rel in self.relations:
            if rel.relation_type == "contradicts":
                src_name = self.entities.get(rel.source_entity, KGEntity("", "?", "")).name
                tgt_name = self.entities.get(rel.target_entity, KGEntity("", "?", "")).name
                contradictions.append({
                    "entity_a": src_name,
                    "entity_b": tgt_name,
                    "metadata": rel.metadata,
                    "confidence": rel.confidence,
                })
        return contradictions

    def get_stats(self) -> Dict:
        """Return graph statistics."""
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entity_types": {str(k): int(v) for k, v in pd.Series([e.entity_type for e in self.entities.values()]).value_counts().items()},
            "relation_types": {str(k): int(v) for k, v in pd.Series([r.relation_type for r in self.relations]).value_counts().items()},
            "contradiction_count": sum(1 for r in self.relations if r.relation_type == "contradicts"),
            "connected_components": nx.number_weakly_connected_components(self.graph) if len(self.graph) > 0 else 0,
        }

    def export_pyvis(self, output_path: str = "knowledge_graph.html",
                     height: str = "700px", width: str = "100%"):
        """Export graph to interactive PyVis HTML."""
        try:
            from pyvis.network import Network
        except ImportError:
            return

        net = Network(height=height, width=width, directed=True,
                      bgcolor="#0B1120", font_color="#F1F5F9")
        net.barnes_hut(gravity=-5000, central_gravity=0.3,
                       spring_length=150, spring_strength=0.04)

        # Professional color palette for entity types
        type_colors = {
            "company": "#EF4444", "person": "#06B6D4", "product": "#3B82F6",
            "region": "#10B981", "metric": "#F59E0B", "date": "#8B5CF6",
            "quarter": "#8B5CF6", "event": "#EC4899", "fact": "#F97316",
            "department": "#14B8A6", "entity": "#64748B",
        }

        # Only include entities that have at least one connection to prevent physics engine freeze
        connected_entities = set()
        for rel in self.relations:
            connected_entities.add(rel.source_entity)
            connected_entities.add(rel.target_entity)

        for eid, entity in self.entities.items():
            if eid not in connected_entities:
                continue
                
            color = type_colors.get(entity.entity_type, "#64748B")
            size = 25 if entity.entity_type in ("company", "region") else 15
            net.add_node(
                eid, label=entity.name, color=color, size=size,
                title=f"Type: {entity.entity_type}\nSources: {', '.join(entity.sources)}"
            )

        for rel in self.relations:
            color = "#EF4444" if rel.relation_type == "contradicts" else \
                    "#10B981" if rel.relation_type == "supports" else "#475569"
            width = 3 if rel.relation_type == "contradicts" else 1
            net.add_edge(
                rel.source_entity, rel.target_entity,
                label=rel.relation_type, color=color, width=width,
                title=f"{rel.relation_type} (conf: {rel.confidence:.2f})",
            )

        net.save_graph(output_path)
        return output_path

    # ── Internal ────────────────────────────────────────────────────────────

    def _find_entity(self, name: str, entity_type: str = None, allow_partial: bool = False) -> Optional[str]:
        """Find entity by name (case-insensitive exact match with fast index lookup)."""
        name_lower = name.lower().strip()
        
        # 1. Fast exact lookup using index
        if hasattr(self, "_name_index") and name_lower in self._name_index:
            eid = self._name_index[name_lower]
            if entity_type is None or self.entities[eid].entity_type == entity_type:
                return eid
                
        # 2. Case-insensitive exact loop fallback (only if index is missing)
        if not hasattr(self, "_name_index") or not self._name_index:
            for eid, entity in self.entities.items():
                if entity.name.lower().strip() == name_lower:
                    if entity_type is None or entity.entity_type == entity_type:
                        return eid
                    
        # 3. Partial match (only if explicitly requested and len >= 3)
        if allow_partial and len(name_lower) >= 3:
            for eid, entity in self.entities.items():
                if name_lower in entity.name.lower() or entity.name.lower() in name_lower:
                    if entity_type is None or entity.entity_type == entity_type:
                        return eid
                        
        return None

    def _infer_entity_type(self, column_name: str) -> str:
        """Infer entity type from column name."""
        col_lower = column_name.lower()
        if "region" in col_lower or "country" in col_lower or "location" in col_lower:
            return "region"
        if "product" in col_lower or "item" in col_lower:
            return "product"
        if "date" in col_lower or "time" in col_lower or "quarter" in col_lower:
            return "date"
        if "name" in col_lower or "employee" in col_lower or "person" in col_lower:
            return "person"
        if "company" in col_lower or "org" in col_lower:
            return "company"
        if "dept" in col_lower or "department" in col_lower:
            return "department"
        return "entity"
