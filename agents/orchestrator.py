"""
Orchestrator Agent — The Brain
───────────────────────────────
Master routing agent that decomposes queries, coordinates specialist agents,
synthesizes responses, and manages the full intelligence pipeline.
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentResponse, get_embeddings_batch, get_query_embedding, _fallback_embedding
from agents.validator import ValidatorAgent
from agents.reconciler import ReconcilerAgent
from agents.forecaster import ForecasterAgent
from agents.critic import CriticAgent

from core.data_federation import DataFederationHub, DataSource
from core.quality_scorer import DataQualityScorer, QualityReport
from core.contradiction_detector import ContradictionDetector, Contradiction
from core.lineage_tracker import LineageTracker
from core.knowledge_graph import DynamicKnowledgeGraph
from core.temporal_vector_store import TemporalVectorStore


class OrchestratorAgent(BaseAgent):
    """
    The brain of NeuralNexus. Coordinates all agents and infrastructure.
    
    Responsibilities:
      1. Data ingestion and indexing
      2. Query decomposition and routing
      3. Agent coordination
      4. Response synthesis with lineage
      5. Proactive intelligence generation
    """

    def __init__(self):
        super().__init__(
            agent_name="OrchestratorAgent",
            model_key="orchestrator",
            system_instruction=(
                "You are the OrchestratorAgent — the central intelligence coordinator of NeuralNexus, "
                "an enterprise intelligence fabric. You synthesize information from multiple data "
                "sources, specialist agents, and a knowledge graph to provide comprehensive, "
                "data-driven answers.\n\n"
                "When answering:\n"
                "1. Always cite which data sources your facts come from\n"
                "2. If there are contradictions in the data, explain them\n"
                "3. Provide confidence levels\n"
                "4. Include uncertainty ranges where applicable\n"
                "5. Give actionable recommendations\n"
                "6. Never make up data — if uncertain, say so\n\n"
                "Format your responses with clear headers, bullet points, and "
                "distinguish between FACTS (from data) and ANALYSIS (your reasoning)."
            ),
        )

        # Initialize all components
        self.federation = DataFederationHub()
        self.quality_scorer = DataQualityScorer()
        self.contradiction_detector = ContradictionDetector()
        self.lineage_tracker = LineageTracker()
        self.knowledge_graph = DynamicKnowledgeGraph()
        self.vector_store = TemporalVectorStore()

        # Initialize specialist agents
        self.validator = ValidatorAgent()
        self.reconciler = ReconcilerAgent()
        self.forecaster = ForecasterAgent()
        self.critic = CriticAgent()

        # State
        self.quality_reports: Dict[str, QualityReport] = {}
        self.contradictions: List[Contradiction] = []
        self.is_initialized = False

    # ── Data Ingestion ──────────────────────────────────────────────────────

    def ingest_data(self, file_paths: List[str],
                    source_names: List[str] = None,
                    credibilities: List[float] = None) -> Dict:
        """Ingest multiple data sources and build the intelligence fabric."""
        print("[*] Ingesting data sources...")

        for i, path in enumerate(file_paths):
            name = source_names[i] if source_names and i < len(source_names) else None
            cred = credibilities[i] if credibilities and i < len(credibilities) else None

            try:
                source = self.federation.ingest_auto(
                    path, source_name=name, credibility=cred
                )
                print(f"  [+] {source.summary()}")
            except Exception as e:
                print(f"  [-] Failed to ingest {path}: {e}")

        # Score quality (local — no API calls)
        print("\n[*] Scoring data quality...")
        self.quality_reports = self.quality_scorer.score_all(self.federation.sources)
        for sid, report in self.quality_reports.items():
            try:
                print(f"  {report.summary()}")
            except UnicodeEncodeError:
                safe_emoji = {"A": "[A]", "B": "[B]", "C": "[C]", "D": "[D]", "F": "[F]"}.get(report.grade, "[?]")
                safe_summary = (
                    f"{safe_emoji} {report.source_name}: {report.overall_score:.1f}/100 "
                    f"(Grade {report.grade}) | "
                    f"C={report.completeness_score:.0f} I={report.consistency_score:.0f} "
                    f"T={report.timeliness_score:.0f} | "
                    f"{len(report.issues)} issues found"
                )
                print(f"  {safe_summary}")

        # Detect contradictions (local — no API calls)
        print("\n[*] Scanning for contradictions...")
        self.contradictions = self.contradiction_detector.detect_all(self.federation.sources)
        print(f"  Found {len(self.contradictions)} contradictions")

        # Build knowledge graph (local — no API calls)
        print("\n[*] Building knowledge graph...")
        self._build_knowledge_graph()
        kg_stats = self.knowledge_graph.get_stats()
        print(f"  Entities: {kg_stats['total_entities']}, Relations: {kg_stats['total_relations']}")

        # Build vector store using LOCAL embeddings (no API calls!)
        # Real Gemini embeddings are used only for user queries (saves quota)
        print("\n[*] Building vector store (local embeddings for speed)...")
        self._build_vector_store_local()
        vs_stats = self.vector_store.get_stats()
        print(f"  Chunks indexed: {vs_stats['total_chunks']}")

        # Run anomaly scan (local — no API calls)
        print("\n[*] Running anomaly scan...")
        anomalies = self.validator.scan_all(self.federation.sources, self.quality_reports)
        print(f"  Detected {len(anomalies)} anomalies")

        self.is_initialized = True
        print("\n[+] NeuralNexus Intelligence Fabric initialized!")

        return {
            "sources": len(self.federation.sources),
            "quality_reports": {sid: r.overall_score for sid, r in self.quality_reports.items()},
            "contradictions": len(self.contradictions),
            "kg_entities": kg_stats["total_entities"],
            "kg_relations": kg_stats["total_relations"],
            "vector_chunks": vs_stats["total_chunks"],
            "anomalies": len(anomalies),
        }

    # ── Query Processing ────────────────────────────────────────────────────

    def process_query(self, user_query: str,
                      use_critic: bool = True) -> Dict[str, Any]:
        """
        Process a user query through the full intelligence pipeline.
        
        Flow:
          1. Retrieve relevant context from vector store
          2. Check knowledge graph for entity information
          3. Route to specialist agents if needed
          4. Synthesize response
          5. Review with CriticAgent
          6. Track lineage
        """
        if not self.is_initialized:
            return {
                "answer": "Please ingest data first using the sidebar.",
                "confidence": 0.0,
                "sources": [],
                "specialist_insights": {},
                "review": None,
                "contradictions_found": 0,
                "retrieved_chunks": 0,
            }

        # Step 1: Retrieve context from vector store
        retrieved_context = self._retrieve_context(user_query)

        # Step 2: Check knowledge graph (local — no API call)
        kg_context = self._query_knowledge_graph(user_query)

        # Step 3: Check for relevant contradictions (local)
        contradiction_context = self._get_relevant_contradictions(user_query)

        # Step 4: Get data summaries (local)
        data_summary = self._get_data_summary()

        # Build full context
        full_context = self._build_query_context(
            user_query, retrieved_context, kg_context,
            contradiction_context, data_summary
        )

        # Step 5: Generate response (1 API call)
        prompt = (
            f"USER QUERY: {user_query}\n\n"
            "Answer this query using the provided context. Follow these rules:\n"
            "1. Cite specific data sources for every factual claim\n"
            "2. If there are contradictions in the data, explain them\n"
            "3. Provide confidence levels\n"
            "4. Give actionable insights\n"
            "5. Rate your overall confidence (0-100%)\n"
        )

        main_response = self.query(prompt, context=full_context)
        main_response.sources_used = list(set(
            r.chunk.source_name for r in retrieved_context
        )) if retrieved_context else []

        # Step 6: Route to specialists only if relevant (0-1 API calls)
        specialist_insights = self._route_to_specialists(user_query)

        # Step 7: Critic review (1 API call)
        review_result = None
        if use_critic:
            review_result = self.critic.review(
                main_response,
                original_query=user_query,
                available_data_summary=data_summary[:500],
            )

        # Step 8: Track lineage (local)
        for r in retrieved_context[:5]:
            self.lineage_tracker.track_text_extract(
                source_id=r.chunk.source_id,
                source_name=r.chunk.source_name,
                text_span=r.chunk.content[:200],
                fact_text=user_query,
            )

        # Build final result
        final_answer = review_result["enhanced_answer"] if review_result else main_response.content

        return {
            "answer": final_answer,
            "confidence": main_response.confidence,
            "sources": main_response.sources_used,
            "specialist_insights": specialist_insights,
            "review": review_result,
            "contradictions_found": len(self.contradictions),
            "retrieved_chunks": len(retrieved_context),
            "lineage": self.lineage_tracker.to_dict(),
        }

    def process_query_stream(self, user_query: str):
        """
        Process a user query through the intelligence pipeline and yield streaming NDJSON chunks.
        Bypasses the CriticAgent review to enable real-time streaming speed.
        """
        import json
        
        if not self.is_initialized:
            yield json.dumps({
                "type": "error",
                "content": "Please ingest data first using the sidebar."
            }) + "\n"
            return

        # Retrieve Context
        retrieved_context = self._retrieve_context(user_query)
        kg_context = self._query_knowledge_graph(user_query)
        contradiction_context = self._get_relevant_contradictions(user_query)
        data_summary = self._get_data_summary()

        full_context = self._build_query_context(
            user_query, retrieved_context, kg_context,
            contradiction_context, data_summary
        )

        prompt = (
            f"USER QUERY: {user_query}\n\n"
            "Answer this query using the provided context. Follow these rules:\n"
            "1. Cite specific data sources for every factual claim\n"
            "2. If there are contradictions in the data, explain them\n"
            "3. Provide confidence levels\n"
            "4. Give actionable insights\n"
            "5. Rate your overall confidence (0-100%)\n"
        )

        # Track lineage
        for r in retrieved_context[:5]:
            self.lineage_tracker.track_text_extract(
                source_id=r.chunk.source_id,
                source_name=r.chunk.source_name,
                text_span=r.chunk.content[:200],
                fact_text=user_query,
            )

        sources_used = list(set(
            r.chunk.source_name for r in retrieved_context
        )) if retrieved_context else []

        full_answer = ""
        # Stream the LLM response
        for chunk in self.query_stream(prompt, context=full_context):
            full_answer += chunk
            yield json.dumps({
                "type": "chunk",
                "content": chunk
            }) + "\n"

        # Try to extract confidence from the full string
        confidence = self._extract_confidence(full_answer)

        # Optional: Async specialist insights (we do this synchronously here, but fast)
        specialist_insights = self._route_to_specialists(user_query)

        # Yield the final metadata chunk
        yield json.dumps({
            "type": "meta",
            "data": {
                "confidence": confidence,
                "sources": sources_used,
                "specialist_insights": specialist_insights,
                "review": None, # Skipped for streaming
                "contradictions_found": len(self.contradictions),
                "retrieved_chunks": len(retrieved_context),
                "lineage": self.lineage_tracker.to_dict(),
            }
        }) + "\n"

    def get_proactive_insights(self) -> Dict[str, Any]:
        """Generate proactive insights without user asking."""
        results = {}

        # Validator insights (local summary — no API call)
        results["anomalies"] = self.validator.get_summary()

        # AI-powered analysis (1 API call)
        ai_analysis = self.validator.get_ai_analysis()
        results["anomaly_analysis"] = ai_analysis.content

        # Forecaster insights (1 API call)
        forecast = self.forecaster.generate_proactive_insights(self.federation.sources)
        results["forecast"] = forecast.content

        # Contradiction status (local — no API call)
        if self.contradictions:
            results["contradictions"] = self.contradiction_detector.get_summary()
        else:
            results["contradictions"] = "No contradictions detected."

        return results

    def reconcile_contradictions(self) -> List[Dict]:
        """Run reconciliation on all detected contradictions."""
        if not self.contradictions:
            return []

        results = []
        for c in self.contradictions[:5]:  # Limit to top 5
            resolution = self.reconciler.reconcile(
                c,
                source_a=self.federation.sources.get(c.source_a_id),
                source_b=self.federation.sources.get(c.source_b_id),
                quality_a=self.quality_reports.get(c.source_a_id),
                quality_b=self.quality_reports.get(c.source_b_id),
            )
            results.append({
                "contradiction": c.summary(),
                "resolution": resolution.content,
                "confidence": resolution.confidence,
            })

        return results

    # ── Internal Pipeline ───────────────────────────────────────────────────

    def _build_knowledge_graph(self):
        """Build KG from all ingested sources."""
        for sid, source in self.federation.sources.items():
            if source.data is not None:
                self.knowledge_graph.build_from_structured(
                    source.data, source.source_name
                )
            if source.text_content:
                self.knowledge_graph.build_from_text(
                    source.text_content, source.source_name
                )

        # Add contradiction edges
        for c in self.contradictions:
            self.knowledge_graph.add_contradiction_edge(
                entity_a_name=f"{c.entity} ({c.source_a_name})",
                entity_b_name=f"{c.entity} ({c.source_b_name})",
                attribute=c.attribute,
                val_a=c.source_a_value,
                val_b=c.source_b_value,
                source_a=c.source_a_name,
                source_b=c.source_b_name,
            )

        # Export for visualization
        try:
            self.knowledge_graph.export_pyvis(os.path.join("app", "knowledge_graph.html"))
        except Exception as e:
            print(f"  [-] Failed to export Knowledge Graph PyVis HTML: {e}")

    def _build_vector_store_local(self):
        """
        Chunk all data and index with LOCAL random embeddings.
        This is fast (zero API calls) and works great for demo.
        Actual Gemini embeddings are used at QUERY time only.
        """
        for sid, source in self.federation.sources.items():
            chunks = []
            if source.data is not None:
                df = source.data
                for i in range(0, len(df), 5):  # Group 5 rows per chunk
                    batch = df.iloc[i:i+5]
                    text = f"[Source: {source.source_name}]\n"
                    text += batch.to_string(index=False)
                    chunks.append(text)

            if source.text_content:
                text = source.text_content
                chunk_size = 500
                overlap = 50
                for i in range(0, len(text), chunk_size - overlap):
                    chunk = text[i:i + chunk_size]
                    if len(chunk.strip()) > 20:
                        chunks.append(f"[Source: {source.source_name}]\n{chunk}")

            if not chunks:
                continue

            try:
                # Use LOCAL fallback embeddings — zero API calls
                embeddings = [_fallback_embedding() for _ in chunks]
                emb_array = np.array(embeddings, dtype="float32")

                quality = self.quality_reports.get(sid)
                q_score = quality.overall_score / 100.0 if quality else 0.7

                self.vector_store.add_chunks(
                    texts=chunks,
                    embeddings=emb_array,
                    source_id=sid,
                    source_name=source.source_name,
                    quality_score=q_score,
                    credibility_score=source.credibility_score,
                )
            except Exception as e:
                print(f"  [!] Error indexing {source.source_name}: {e}")

    def _retrieve_context(self, query: str, top_k: int = 8) -> list:
        """Retrieve relevant chunks from vector store."""
        try:
            query_emb = get_query_embedding(query)
            if query_emb:
                return self.vector_store.search(
                    np.array(query_emb, dtype="float32"),
                    top_k=top_k,
                )
        except Exception as e:
            print(f"  [!] Retrieval error: {e}")
        return []

    def _query_knowledge_graph(self, query: str) -> str:
        """Extract entities from query and look them up in KG."""
        import re
        entities_found = []
        for eid, entity in self.knowledge_graph.entities.items():
            if entity.name.lower() in query.lower():
                info = self.knowledge_graph.query_entity(entity.name)
                if info.get("found"):
                    entities_found.append(info)

        if not entities_found:
            return ""

        lines = ["KNOWLEDGE GRAPH CONTEXT:"]
        for info in entities_found[:5]:
            e = info["entity"]
            lines.append(f"  Entity: {e['name']} (type: {e['type']})")
            for conn in info.get("connections", [])[:5]:
                if "target" in conn:
                    lines.append(f"    -> {conn['relation']} -> {conn['target']}")
                if "source" in conn:
                    lines.append(f"    <- {conn['relation']} <- {conn['source']}")
            if info.get("contradiction_count", 0) > 0:
                lines.append(f"    WARNING: {info['contradiction_count']} contradictions detected!")

        return "\n".join(lines)

    def _get_relevant_contradictions(self, query: str) -> str:
        """Find contradictions relevant to the query."""
        relevant = []
        query_lower = query.lower()
        for c in self.contradictions:
            if (c.entity.lower() in query_lower or
                c.attribute.lower() in query_lower or
                any(word in query_lower for word in c.entity.lower().split())):
                relevant.append(c)

        if not relevant:
            return ""

        lines = ["RELEVANT DATA CONTRADICTIONS:"]
        for c in relevant[:3]:
            lines.append(c.summary())
        return "\n".join(lines)

    def _get_data_summary(self) -> str:
        """Get a summary of all available data."""
        lines = ["AVAILABLE DATA SOURCES:"]
        for src in self.federation.sources.values():
            lines.append(f"  {src.summary()}")
            quality = self.quality_reports.get(src.source_id)
            if quality:
                lines.append(f"    Quality: {quality.overall_score:.0f}/100 ({quality.grade})")
        return "\n".join(lines)

    def _build_query_context(self, query: str, retrieved: list,
                              kg_context: str, contradiction_context: str,
                              data_summary: str) -> str:
        """Build the full context string for the LLM."""
        parts = [data_summary]

        if retrieved:
            parts.append("\nRETRIEVED RELEVANT DATA:")
            for r in retrieved[:6]:
                parts.append(f"  [Score: {r.final_score:.3f} | "
                             f"Source: {r.chunk.source_name}]\n  {r.chunk.content[:300]}")

        if kg_context:
            parts.append(f"\n{kg_context}")

        if contradiction_context:
            parts.append(f"\n{contradiction_context}")

        return "\n".join(parts)

    def _route_to_specialists(self, query: str) -> Dict[str, str]:
        """Route query to specialist agents if relevant keywords detected."""
        insights = {}
        query_lower = query.lower()

        # Forecaster: trigger on trend/forecast/predict/future/risk keywords
        forecast_keywords = ["trend", "forecast", "predict", "future", "risk",
                              "next quarter", "outlook", "projection", "growth"]
        if any(kw in query_lower for kw in forecast_keywords):
            for source in self.federation.sources.values():
                if source.data is not None:
                    result = self.forecaster.analyze_trends(source)
                    insights[f"forecast_{source.source_name}"] = result.content
                    break

        # Validator: trigger on quality/anomaly/issue keywords
        validator_keywords = ["quality", "anomal", "issue", "problem",
                               "error", "wrong", "incorrect", "suspicious"]
        if any(kw in query_lower for kw in validator_keywords):
            result = self.validator.get_ai_analysis()
            insights["validation"] = result.content

        return insights
