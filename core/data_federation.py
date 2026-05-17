"""
Data Federation Hub — Layer 1
─────────────────────────────
Unified multi-source data ingestion with automatic schema inference,
data fingerprinting, and standardized output format.

Supports: CSV, Excel, JSON, TXT/PDF-text, SQL (SQLite).
"""

import os
import json
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from agents.base_agent import extract_vision_content


@dataclass
class DataSource:
    """Represents an ingested data source with metadata."""
    source_id: str
    source_name: str
    source_type: str                      # csv, excel, json, text, sql
    file_path: str
    ingested_at: str = ""
    fingerprint: str = ""                 # SHA-256 hash
    row_count: int = 0
    column_count: int = 0
    schema: Dict[str, str] = field(default_factory=dict)       # col -> dtype
    data: Optional[pd.DataFrame] = None
    text_content: Optional[str] = None    # For unstructured sources
    raw_json: Optional[dict] = None       # For JSON sources
    credibility_score: float = 0.7        # Default credibility
    tags: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.data is not None:
            return (f"[{self.source_type.upper()}] {self.source_name}: "
                    f"{self.row_count} rows × {self.column_count} cols | "
                    f"Credibility: {self.credibility_score:.0%}")
        elif self.text_content:
            return (f"[{self.source_type.upper()}] {self.source_name}: "
                    f"{len(self.text_content):,} chars | "
                    f"Credibility: {self.credibility_score:.0%}")
        return f"[{self.source_type.upper()}] {self.source_name}: Empty"


class DataFederationHub:
    """
    Centralized data ingestion and normalization layer.
    
    Handles multi-format data loading, schema inference,
    fingerprinting, and unified access for downstream agents.
    """

    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self._ingestion_log: List[Dict] = []

    def ingest_csv(self, file_path: str, source_name: str = None,
                   credibility: float = 0.75, tags: List[str] = None) -> DataSource:
        """Ingest a CSV file."""
        source_name = source_name or os.path.basename(file_path)
        df = pd.read_csv(file_path)

        source = DataSource(
            source_id=self._generate_id(file_path),
            source_name=source_name,
            source_type="csv",
            file_path=file_path,
            ingested_at=datetime.now().isoformat(),
            fingerprint=self._compute_fingerprint(file_path),
            row_count=len(df),
            column_count=len(df.columns),
            schema=self._infer_schema(df),
            data=df,
            credibility_score=credibility,
            tags=tags or [],
        )

        self.sources[source.source_id] = source
        self._log_ingestion(source)
        return source

    def ingest_excel(self, file_path: str, source_name: str = None,
                     sheet_name: int = 0, credibility: float = 0.70,
                     tags: List[str] = None) -> DataSource:
        """Ingest an Excel file."""
        source_name = source_name or os.path.basename(file_path)
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        source = DataSource(
            source_id=self._generate_id(file_path),
            source_name=source_name,
            source_type="excel",
            file_path=file_path,
            ingested_at=datetime.now().isoformat(),
            fingerprint=self._compute_fingerprint(file_path),
            row_count=len(df),
            column_count=len(df.columns),
            schema=self._infer_schema(df),
            data=df,
            credibility_score=credibility,
            tags=tags or [],
        )

        self.sources[source.source_id] = source
        self._log_ingestion(source)
        return source

    def ingest_json(self, file_path: str, source_name: str = None,
                    data_key: str = "data", credibility: float = 0.80,
                    tags: List[str] = None) -> DataSource:
        """Ingest a JSON file. Extracts data array from `data_key` if present."""
        source_name = source_name or os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        df = None
        if isinstance(raw, list):
            df = pd.json_normalize(raw)
        elif isinstance(raw, dict) and data_key in raw:
            df = pd.json_normalize(raw[data_key])

        source = DataSource(
            source_id=self._generate_id(file_path),
            source_name=source_name,
            source_type="json",
            file_path=file_path,
            ingested_at=datetime.now().isoformat(),
            fingerprint=self._compute_fingerprint(file_path),
            row_count=len(df) if df is not None else 0,
            column_count=len(df.columns) if df is not None else 0,
            schema=self._infer_schema(df) if df is not None else {},
            data=df,
            raw_json=raw,
            credibility_score=credibility,
            tags=tags or [],
        )

        self.sources[source.source_id] = source
        self._log_ingestion(source)
        return source

    def ingest_text(self, file_path: str, source_name: str = None,
                    credibility: float = 0.90, tags: List[str] = None) -> DataSource:
        """Ingest a text/PDF-extracted file."""
        source_name = source_name or os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        source = DataSource(
            source_id=self._generate_id(file_path),
            source_name=source_name,
            source_type="text",
            file_path=file_path,
            ingested_at=datetime.now().isoformat(),
            fingerprint=self._compute_fingerprint(file_path),
            text_content=content,
            credibility_score=credibility,
            tags=tags or [],
        )

        self.sources[source.source_id] = source
        self._log_ingestion(source)
        return source

    def ingest_pdf(self, file_path: str, source_name: str = None,
                   credibility: float = 0.90, tags: List[str] = None) -> DataSource:
        """Ingest a PDF file using Gemini Multimodal Vision, with PyMuPDF fallback."""
        source_name = source_name or os.path.basename(file_path)

        content = None
        # Try Gemini Vision First
        content = extract_vision_content(file_path, mime_type="application/pdf")
        
        if not content:
            # Fallback to PyMuPDF
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                pages = []
                for page in doc:
                    pages.append(page.get_text())
                content = "\n\n".join(pages)
                doc.close()
            except ImportError:
                # Fallback: try reading as text
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                content = f"[PDF extraction failed for {file_path}]"

        source = DataSource(
            source_id=self._generate_id(file_path),
            source_name=source_name,
            source_type="pdf",
            file_path=file_path,
            ingested_at=datetime.now().isoformat(),
            fingerprint=self._compute_fingerprint(file_path),
            text_content=content,
            credibility_score=credibility,
            tags=tags or [],
        )

        self.sources[source.source_id] = source
        self._log_ingestion(source)
        return source

    def ingest_image(self, file_path: str, source_name: str = None,
                     credibility: float = 0.85, tags: List[str] = None) -> DataSource:
        """Ingest an image (screenshot, chart, receipt) using Gemini Multimodal Vision."""
        source_name = source_name or os.path.basename(file_path)

        content = extract_vision_content(file_path)
        if not content:
            content = f"[Image extraction failed for {file_path}]"

        source = DataSource(
            source_id=self._generate_id(file_path),
            source_name=source_name,
            source_type="image",
            file_path=file_path,
            ingested_at=datetime.now().isoformat(),
            fingerprint=self._compute_fingerprint(file_path),
            text_content=content,
            credibility_score=credibility,
            tags=tags or [],
        )

        self.sources[source.source_id] = source
        self._log_ingestion(source)
        return source

    def ingest_auto(self, file_path: str, source_name: str = None,
                    credibility: float = None, tags: List[str] = None) -> DataSource:
        """Auto-detect file type and ingest."""
        ext = os.path.splitext(file_path)[1].lower()
        cred_defaults = {
            ".csv": 0.75, ".xlsx": 0.70, ".xls": 0.70,
            ".json": 0.80, ".txt": 0.90, ".pdf": 0.90,
            ".png": 0.85, ".jpg": 0.85, ".jpeg": 0.85,
        }
        cred = credibility or cred_defaults.get(ext, 0.60)

        if ext == ".csv":
            return self.ingest_csv(file_path, source_name, cred, tags)
        elif ext in (".xlsx", ".xls"):
            return self.ingest_excel(file_path, source_name, credibility=cred, tags=tags)
        elif ext == ".json":
            return self.ingest_json(file_path, source_name, credibility=cred, tags=tags)
        elif ext == ".pdf":
            return self.ingest_pdf(file_path, source_name, cred, tags)
        elif ext in (".png", ".jpg", ".jpeg"):
            return self.ingest_image(file_path, source_name, cred, tags)
        elif ext in (".txt", ".md"):
            return self.ingest_text(file_path, source_name, cred, tags)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def get_all_structured_data(self) -> Dict[str, pd.DataFrame]:
        """Return all structured (tabular) data sources."""
        return {
            sid: src.data for sid, src in self.sources.items()
            if src.data is not None
        }

    def get_all_text_content(self) -> Dict[str, str]:
        """Return all unstructured text sources."""
        return {
            sid: src.text_content for sid, src in self.sources.items()
            if src.text_content is not None
        }

    def get_source_by_name(self, name: str) -> Optional[DataSource]:
        """Find a source by its display name."""
        for src in self.sources.values():
            if src.source_name.lower() == name.lower():
                return src
        return None

    # ── Internal Helpers ────────────────────────────────────────────────────

    def _infer_schema(self, df: pd.DataFrame) -> Dict[str, str]:
        """Infer column types with semantic labels."""
        schema = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if "int" in dtype:
                schema[col] = "integer"
            elif "float" in dtype:
                schema[col] = "float"
            elif "datetime" in dtype:
                schema[col] = "datetime"
            elif "bool" in dtype:
                schema[col] = "boolean"
            else:
                # Check if it's a date string
                try:
                    sample = df[col].dropna().head(5)
                    pd.to_datetime(sample)
                    schema[col] = "date_string"
                except (ValueError, TypeError):
                    # Check if it looks numeric
                    try:
                        pd.to_numeric(df[col].dropna().head(10))
                        schema[col] = "numeric_string"
                    except (ValueError, TypeError):
                        schema[col] = "string"
        return schema

    def _compute_fingerprint(self, file_path: str) -> str:
        """SHA-256 hash of file contents."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]

    def _generate_id(self, file_path: str) -> str:
        """Generate a stable source ID."""
        base = os.path.basename(file_path)
        return f"src_{hashlib.md5(base.encode()).hexdigest()[:8]}"

    def _log_ingestion(self, source: DataSource):
        """Log ingestion event."""
        self._ingestion_log.append({
            "source_id": source.source_id,
            "source_name": source.source_name,
            "type": source.source_type,
            "rows": source.row_count,
            "fingerprint": source.fingerprint,
            "time": source.ingested_at,
        })

    def get_ingestion_summary(self) -> str:
        """Return a human-readable summary of all ingested sources."""
        lines = ["╔══════════════════════════════════════════════════╗",
                 "║         Data Federation Hub — Summary            ║",
                 "╚══════════════════════════════════════════════════╝"]
        for src in self.sources.values():
            lines.append(f"  {src.summary()}")
        lines.append(f"\n  Total sources: {len(self.sources)}")
        return "\n".join(lines)
