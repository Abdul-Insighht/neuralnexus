"""
NeuralNexus Configuration
─────────────────────────
Central config for API keys, model selection, and system parameters.
Built for AI Agent Olympics Hackathon 2026 — lablab.ai
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List


# ─── API Keys ────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "AIzaSyBn5TFV-MC0pumGH2PjkxoPqoqD6qwqQ5U",  # Set via env variable or .env file
)

# ─── Security & Governance ───────────────────────────────────────────────────
# Route traffic through Lobster Trap for deep prompt inspection & audit (Track 1)
LOBSTER_TRAP_ENDPOINT = os.environ.get("LOBSTER_TRAP_ENDPOINT", None)


# ─── Gemini Model Selection ─────────────────────────────────────────────────
# All agents use Gemini 2.0 Flash for speed and cost-efficiency
MODELS = {
    "orchestrator": "models/gemini-2.5-flash",
    "validator":    "models/gemini-2.5-flash",
    "reconciler":   "models/gemini-2.5-flash",
    "forecaster":   "models/gemini-2.5-flash",
    "critic":       "models/gemini-2.5-flash",
    "embedding":    "models/gemini-embedding-2",
}


@dataclass
class SystemConfig:
    """Global system configuration."""

    # ── Data Quality ──
    quality_completeness_weight: float = 0.35
    quality_consistency_weight: float = 0.35
    quality_timeliness_weight: float = 0.30
    min_quality_threshold: float = 30.0      # Flag sources below this

    # ── Contradiction Detection ──
    numeric_tolerance_pct: float = 5.0       # % difference to flag conflict
    semantic_similarity_threshold: float = 0.80  # cosine sim for matching facts

    # ── Vector Store ──
    embedding_dim: int = 768
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieval: int = 8
    recency_decay: float = 0.95              # Exponential decay for older data

    # ── Knowledge Graph ──
    kg_max_entities: int = 5000
    kg_relation_types: List[str] = field(default_factory=lambda: [
        "reports_to", "part_of", "caused_by", "contradicts",
        "supports", "correlates_with", "produced_by", "located_in",
        "measured_at", "forecasts",
    ])

    # ── Agent Behaviour ──
    agent_temperature: float = 0.3           # Conservative for enterprise
    agent_max_tokens: int = 4096
    critic_min_score: float = 0.6            # Re-query if answer below this
    max_agent_retries: int = 2

    # ── Anomaly Detection ──
    zscore_threshold: float = 2.5
    iqr_multiplier: float = 1.5

    # ── UI ──
    streamlit_port: int = 8501
    page_title: str = "NeuralNexus — Autonomous Financial Intelligence Fabric"
    page_icon: str = "🧠"


# Singleton
CONFIG = SystemConfig()


# ─── Gemini Generation Config ───────────────────────────────────────────────
GENERATION_CONFIG = {
    "temperature": CONFIG.agent_temperature,
    "max_output_tokens": CONFIG.agent_max_tokens,
    "top_p": 0.95,
    "top_k": 40,
}


# ─── Source Credibility Defaults ─────────────────────────────────────────────
DEFAULT_SOURCE_CREDIBILITY: Dict[str, float] = {
    "financial_reports":  0.95,   # Audited financials = high trust
    "sales_database":     0.85,
    "api_endpoint":       0.80,
    "spreadsheet":        0.70,
    "web_scrape":         0.50,
    "user_upload":        0.60,
}
