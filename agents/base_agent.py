"""
Base Agent — Agent Foundation
─────────────────────────────
Base class for all NeuralNexus agents with Gemini integration,
structured output, and common utilities.
"""

import numpy as np
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
import time
import threading

from config import GEMINI_API_KEY, MODELS, GENERATION_CONFIG, LOBSTER_TRAP_ENDPOINT


# ── Gemini setup with graceful fallback ─────────────────────────────────────
_GEMINI_READY = False
if GEMINI_API_KEY:
    try:
        # If LOBSTER_TRAP_ENDPOINT is set, route through the proxy for enterprise governance
        client_options = {}
        if LOBSTER_TRAP_ENDPOINT:
            client_options["api_endpoint"] = LOBSTER_TRAP_ENDPOINT
            
        genai.configure(
            api_key=GEMINI_API_KEY,
            client_options=client_options if client_options else None
        )
        _GEMINI_READY = True
    except Exception as e:
        print(f"[NeuralNexus] Gemini config failed: {e}")


# ── Global Rate Limiter ─────────────────────────────────────────────────────
# Gemini free tier: 15 RPM for gemini-2.0-flash, 1500 RPD
# We space out calls to ~4 seconds apart (safe under 15 RPM)
class _RateLimiter:
    """Thread-safe rate limiter for all Gemini API calls."""
    def __init__(self, min_interval: float = 4.0):
        self._min_interval = min_interval
        self._last_call = 0.0
        self._lock = threading.Lock()

    def wait(self):
        with self._lock:
            now = time.time()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.time()

_rate_limiter = _RateLimiter(min_interval=0.0)


@dataclass
class AgentResponse:
    """Standardized agent response."""
    agent_name: str
    content: str
    confidence: float = 0.8
    sources_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    tokens_used: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class BaseAgent:
    """
    Base class for all NeuralNexus agents.

    Provides:
      - Gemini model initialization
      - Structured prompting with system instructions
      - Response parsing and confidence extraction
      - Token tracking
    """

    def __init__(self, agent_name: str, model_key: str = None,
                 system_instruction: str = ""):
        self.agent_name = agent_name
        self.model_key = model_key or "orchestrator"
        self.model_name = MODELS.get(self.model_key, MODELS["orchestrator"])

        self.system_instruction = system_instruction or self._default_system()

        self.model = None
        if _GEMINI_READY:
            try:
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=self.system_instruction,
                    generation_config=genai.GenerationConfig(**GENERATION_CONFIG),
                )
            except Exception:
                pass

        self.chat = None
        self.total_tokens = 0

    def _default_system(self) -> str:
        return (
            f"You are {self.agent_name}, a specialized AI agent in the NeuralNexus "
            f"Enterprise Intelligence Fabric. You provide precise, data-driven analysis "
            f"for enterprise decision-makers. Always cite your sources and quantify "
            f"your confidence level (0-100%). Be concise but thorough."
        )

    def query(self, prompt: str, context: str = "",
              temperature: float = None) -> AgentResponse:
        """Send a query to the Gemini model."""
        if not self.model:
            return AgentResponse(
                agent_name=self.agent_name,
                content=(
                    f"**{self.agent_name}** is offline — no valid Gemini API key configured.\n\n"
                    "Set your key via the sidebar or environment variable `GEMINI_API_KEY`."
                ),
                confidence=0.0,
                metadata={"error": "no_api_key"},
            )

        full_prompt = prompt
        if context:
            full_prompt = f"CONTEXT:\n{context}\n\nQUERY:\n{prompt}"

        config = None
        if temperature is not None:
            config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=GENERATION_CONFIG["max_output_tokens"],
            )

        max_retries = 5
        last_error = None

        for attempt in range(max_retries):
            try:
                _rate_limiter.wait()  # Global throttle
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=config,
                )

                content = response.text
                tokens = 0
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    tokens = getattr(response.usage_metadata, 'total_token_count', 0)
                self.total_tokens += tokens

                confidence = self._extract_confidence(content)

                return AgentResponse(
                    agent_name=self.agent_name,
                    content=content,
                    confidence=confidence,
                    tokens_used=tokens,
                )

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "429" in str(e) or "quota" in err_str or "exhausted" in err_str or "resource" in err_str:
                    wait_time = 15 * (attempt + 1)  # 15s, 30s, 45s, 60s, 75s
                    time.sleep(wait_time)
                    continue
                else:
                    break

        return AgentResponse(
            agent_name=self.agent_name,
            content=f"**{self.agent_name}** encountered an error: `{str(last_error)[:200]}`",
            confidence=0.0,
            metadata={"error": str(last_error)},
        )

    def query_with_chat(self, message: str) -> AgentResponse:
        """Send a message in an ongoing chat session."""
        if not self.model:
            return AgentResponse(
                agent_name=self.agent_name,
                content="Agent offline — no API key.",
                confidence=0.0,
            )

        if self.chat is None:
            self.chat = self.model.start_chat()

        max_retries = 5
        last_error = None

        for attempt in range(max_retries):
            try:
                _rate_limiter.wait()  # Global throttle
                response = self.chat.send_message(message)
                content = response.text
                confidence = self._extract_confidence(content)

                return AgentResponse(
                    agent_name=self.agent_name,
                    content=content,
                    confidence=confidence,
                )
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "429" in str(e) or "quota" in err_str or "exhausted" in err_str or "resource" in err_str:
                    wait_time = 15 * (attempt + 1)
                    time.sleep(wait_time)
                    continue
                else:
                    break

        return AgentResponse(
            agent_name=self.agent_name,
            content=f"Error: {str(last_error)[:200]}",
            confidence=0.0,
        )

    def reset_chat(self):
        """Reset the chat session."""
        self.chat = None

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from response text."""
        patterns = [
            r'[Cc]onfidence[:\s]+(\d{1,3})%',
            r'(\d{1,3})%\s+[Cc]onfiden',
            r'[Cc]onfidence[:\s]+0\.(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                val = float(match.group(1))
                if val > 1:
                    return min(val / 100.0, 1.0)
                return val
        return 0.75  # Default confidence


# ── Embedding helpers (with rate limiting + fallback to random) ──────────────

def _fallback_embedding(dim: int = 768) -> list:
    """Generate a random embedding as fallback when API is unavailable."""
    vec = np.random.randn(dim).astype(float)
    vec = vec / (np.linalg.norm(vec) + 1e-10)
    return vec.tolist()


def get_embedding(text: str) -> Optional[list]:
    """Get embedding vector from Gemini, fallback to random."""
    if not _GEMINI_READY:
        return _fallback_embedding()
    try:
        _rate_limiter.wait()  # Global throttle
        result = genai.embed_content(
            model=MODELS["embedding"],
            content=text,
            task_type="retrieval_document",
        )
        return result['embedding']
    except Exception:
        return _fallback_embedding()


def get_embeddings_batch(texts: List[str]) -> Optional[list]:
    """Get embeddings for a batch of texts."""
    if not _GEMINI_READY:
        return [_fallback_embedding() for _ in texts]
    embeddings = []
    for text in texts:
        try:
            _rate_limiter.wait()  # Global throttle
            result = genai.embed_content(
                model=MODELS["embedding"],
                content=text,
                task_type="retrieval_document",
            )
            embeddings.append(result['embedding'])
        except Exception:
            embeddings.append(_fallback_embedding())
    return embeddings


def get_query_embedding(text: str) -> Optional[list]:
    """Get embedding optimized for query/retrieval."""
    if not _GEMINI_READY:
        return _fallback_embedding()
    try:
        _rate_limiter.wait()  # Global throttle
        result = genai.embed_content(
            model=MODELS["embedding"],
            content=text,
            task_type="retrieval_query",
        )
        return result['embedding']
    except Exception:
        return _fallback_embedding()

def extract_vision_content(file_path: str, mime_type: str = None) -> Optional[str]:
    """Use Gemini Multimodal Vision to extract text, tables, and charts from an image or PDF."""
    if not _GEMINI_READY:
        return None
    try:
        _rate_limiter.wait()
        uploaded_file = genai.upload_file(path=file_path, mime_type=mime_type)
        
        # Wait for processing if it's a large PDF
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
            return None

        model = genai.GenerativeModel(model_name=MODELS.get("orchestrator", "models/gemini-2.5-flash"))
        prompt = "Extract all text, financial tables, and key figures from this document accurately. Describe any charts or graphs in detail. Preserve table structures using markdown."
        response = model.generate_content([uploaded_file, prompt])
        
        # Clean up
        genai.delete_file(uploaded_file.name)
        
        return response.text
    except Exception as e:
        print(f"[NeuralNexus] Vision extraction failed: {e}")
        return None
