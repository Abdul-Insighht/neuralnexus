"""
NeuralNexus — Intelligence Portal
──────────────────────────────────
Streamlit UI for the Autonomous Financial Intelligence Fabric.
AI Agent Olympics Hackathon 2026 — lablab.ai | Track 4: Data & Intelligence
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NeuralNexus — Autonomous Financial Intelligence Fabric",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ── Session State ────────────────────────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "proactive_insights" not in st.session_state:
    st.session_state.proactive_insights = None
if "reconciliation_results" not in st.session_state:
    st.session_state.reconciliation_results = None


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("# 🧠 NeuralNexus")
    st.caption("Autonomous Financial Intelligence Fabric")
    st.markdown("---")

    st.markdown("### 📦 Data Ingestion")

    if "orchestrator" not in st.session_state:
        from agents.orchestrator import OrchestratorAgent
        st.session_state.orchestrator = OrchestratorAgent()

    orch = st.session_state.orchestrator

    st.markdown("### 📂 Upload Your Data")
    st.caption("Upload CSV, Excel, or PDF files with custom credibility scores.")

    upload_type = st.selectbox(
        "File type",
        ["CSV (.csv)", "Excel (.xlsx)", "PDF (.pdf)"],
        label_visibility="collapsed",
    )

    uploaded = st.file_uploader(
        "Choose file",
        type=["csv", "xlsx", "xls", "pdf", "json", "txt"],
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    source_name = st.text_input(
        "Source Name",
        placeholder="e.g. Q3 Audited Financials",
        key="upload_source_name",
    )

    credibility = st.slider(
        "Credibility Score",
        min_value=0.0,
        max_value=1.0,
        value=0.75,
        step=0.05,
        help="0.95 = Audited report | 0.70 = CRM export | 0.50 = Manual data",
        key="upload_credibility",
    )

    if uploaded:
        if st.button("⚡ Ingest File", use_container_width=True, key="ingest_btn"):
            tmp = os.path.join(PROJECT_ROOT, "demo_data", uploaded.name)
            os.makedirs(os.path.dirname(tmp), exist_ok=True)
            with open(tmp, "wb") as f:
                f.write(uploaded.read())
            try:
                name = source_name if source_name else uploaded.name
                orch.federation.ingest_auto(
                    tmp, source_name=name, credibility=credibility
                )
                st.session_state.initialized = True
                st.success(f"✅ {name} ingested!")
            except Exception as e:
                st.error(f"❌ {uploaded.name}: {e}")

    st.markdown("---")

    if not st.session_state.initialized:
        st.info("Or load demo data to start quickly.")
        if st.button("🚀 Initialize with Demo Data", use_container_width=True, key="init_btn"):
            from demo_data.generate_data import generate_all_demo_data
            with st.spinner("Generating 5 enterprise datasets..."):
                demo_paths = generate_all_demo_data()
            with st.spinner("Building intelligence fabric — scoring, detecting, indexing..."):
                result = orch.ingest_data(
                    list(demo_paths.values()),
                    ["Sales Database", "Financial Report", "Inventory API",
                     "HR Headcount", "Market Feed"],
                    [0.80, 0.95, 0.80, 0.75, 0.65],
                )
            st.session_state.initialized = True
            st.rerun()
    else:
        st.success(f"✅ Fabric Active ({len(orch.federation.sources)} sources)")
        
        if st.button("🔍 Run Full Analysis", use_container_width=True, key="reanalyze_btn"):
            with st.spinner("Running all agents on updated data..."):
                orch.quality_reports = orch.quality_scorer.score_all(orch.federation.sources)
                orch.contradictions = orch.contradiction_detector.detect_all(orch.federation.sources)
                orch.validator.scan_all(orch.federation.sources, orch.quality_reports)
                orch._build_knowledge_graph()
                orch._build_vector_store_local()
                orch.is_initialized = True
            st.success("✅ Full analysis complete")
            st.rerun()

        if st.button("🧹 Clear All Data", use_container_width=True):
            st.session_state.initialized = False
            del st.session_state.orchestrator
            st.rerun()

    st.markdown("---")
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("Gemini 2.0 Flash · 5-Agent System")
    st.markdown(
        "<div style='text-align:center;color:rgba(255,255,255,0.3);font-size:11px;padding:8px 0'>"
        "AI Agent Olympics Hackathon 2026<br>lablab.ai · Track 4: Data & Intelligence</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center; padding:28px 0 12px 0;'>
    <div class='hero-title'>🧠 Neural<span class='hero-green'>Nexus</span></div>
    <p class='hero-sub'>
        Autonomous Financial Intelligence Fabric — 5 AI agents that detect contradictions,
        reconcile conflicts, forecast risks, and audit every answer with full data lineage
    </p>
</div>
""", unsafe_allow_html=True)


# ── Landing ──────────────────────────────────────────────────────────────────
if not st.session_state.initialized:
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("#### 🔍 Contradiction Detection")
        st.caption("Finds when your data sources disagree and reconciles conflicts with AI reasoning.")
    with c2:
        st.markdown("#### 📊 Quality Scoring")
        st.caption("Completeness, consistency, and timeliness scoring for every data source.")
    with c3:
        st.markdown("#### 📈 Proactive Forecasting")
        st.caption("Trend analysis, risk scoring, and proactive alerts — without being asked.")
    with c4:
        st.markdown("#### 🕸️ Knowledge Graph")
        st.caption("Auto-extracted entities and relations with contradiction edges.")

    st.markdown("---")
    st.info("👈 Click **🚀 Initialize with Demo Data** in the sidebar to begin")
    st.stop()


orch = st.session_state.orchestrator


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_query, tab_dash, tab_conflict, tab_alerts, tab_kg, tab_lineage = st.tabs([
    "💬 Intelligence Query",
    "📊 Quality Dashboard",
    "⚡ Contradictions",
    "🔔 Proactive Insights",
    "🕸️ Knowledge Graph",
    "📋 Data Lineage",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — INTELLIGENCE QUERY
# ══════════════════════════════════════════════════════════════════════════════
with tab_query:
    st.markdown("## 💬 Ask Your Enterprise Data")
    st.caption("NeuralNexus retrieves → reasons → validates → reviews with full lineage and contradiction awareness.")

    cols = st.columns(3)
    sel = None
    for i, q in enumerate([
        "What is our Q3 revenue and should I trust it?",
        "Show me all contradictions in our financial data",
        "What anomalies and risks should we watch for next quarter?",
    ]):
        with cols[i]:
            if st.button(q, key=f"s_{i}", use_container_width=True):
                sel = q

    user_input = st.chat_input("Ask anything about your enterprise data...")
    if sel:
        user_input = sel

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("🔄 Orchestrator → Reconciler → Forecaster → Critic → Reviewing..."):
            result = orch.process_query(user_input)

        meta = (
            f"\n\n---\n"
            f"**Sources**: {', '.join(result['sources']) if result['sources'] else 'Knowledge Graph'} · "
            f"**Confidence**: {result['confidence']:.0%} · "
            f"**Contradictions**: {result['contradictions_found']} · "
            f"**Chunks**: {result['retrieved_chunks']}"
        )
        st.session_state.chat_history.append({
            "role": "assistant", "content": result["answer"] + meta, "result": result,
        })

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "result" in msg:
                res = msg["result"]
                if res.get("specialist_insights"):
                    with st.expander("🔬 Specialist Agent Insights"):
                        for a, ins in res["specialist_insights"].items():
                            st.markdown(f"**{a}:**\n{ins[:600]}")
                if res.get("review"):
                    with st.expander("🧐 Critic Review"):
                        st.markdown(res["review"]["review_text"][:600])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — QUALITY DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    st.markdown("## 📊 Data Quality Dashboard")
    st.caption("Each source is scored on completeness, consistency, and timeliness.")

    if orch.quality_reports:
        cols = st.columns(len(orch.quality_reports))
        for i, (sid, rpt) in enumerate(orch.quality_reports.items()):
            with cols[i]:
                st.metric(rpt.source_name[:20], f"{rpt.overall_score:.0f}", f"Grade {rpt.grade}")

        st.markdown("---")

        rows = []
        for sid, rpt in orch.quality_reports.items():
            rows.append({
                "Source": rpt.source_name[:18],
                "Completeness": rpt.completeness_score,
                "Consistency": rpt.consistency_score,
                "Timeliness": rpt.timeliness_score,
            })
        df = pd.DataFrame(rows)

        fig = go.Figure()
        palette = {"Completeness": "#22C55E", "Consistency": "#FFFFFF", "Timeliness": "#16A34A"}
        for col_name, color in palette.items():
            fig.add_trace(go.Bar(
                name=col_name, x=df["Source"], y=df[col_name],
                text=[f"{v:.0f}" for v in df[col_name]],
                textposition="auto", marker_color=color,
                textfont=dict(color="#000000" if color == "#FFFFFF" else "#FFFFFF"),
            ))
        fig.update_layout(
            barmode="group",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="rgba(255,255,255,0.7)", height=380,
            legend=dict(orientation="h", y=1.12, font=dict(color="rgba(255,255,255,0.7)")),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", range=[0, 110]),
            margin=dict(l=40, r=20, t=30, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Issues
        st.markdown("### Issues Detected")
        issues = []
        for sid, rpt in orch.quality_reports.items():
            for iss in rpt.issues:
                sev = iss["severity"].upper()
                icon = {"CRITICAL": "🔴", "WARNING": "🟠", "INFO": "🟡"}.get(sev, "⚪")
                issues.append({
                    "": icon, "Source": rpt.source_name[:18],
                    "Severity": sev, "Type": iss["type"],
                    "Description": iss["message"][:90],
                })
        if issues:
            st.dataframe(pd.DataFrame(issues), use_container_width=True, hide_index=True)
        else:
            st.success("No issues detected.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CONTRADICTIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_conflict:
    st.markdown("## ⚡ Cross-Source Contradictions")
    st.caption("Automatically detected conflicts between your data sources — with AI-powered reconciliation.")

    if orch.contradictions:
        n = len(orch.contradictions)
        hi = sum(1 for c in orch.contradictions if c.severity == "high")
        md = sum(1 for c in orch.contradictions if c.severity == "medium")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Conflicts", n)
        c2.metric("🔴 High Severity", hi)
        c3.metric("🟠 Medium Severity", md)
        st.markdown("---")

        for i, c in enumerate(orch.contradictions[:10]):
            icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(c.severity, "⚪")
            label = f"{icon} {c.entity} → {c.attribute}"
            if c.difference_pct:
                label += f" (Δ {c.difference_pct:.1f}%)"

            with st.expander(label, expanded=(i == 0)):
                a, b = st.columns(2)
                with a:
                    st.markdown(f"**{c.source_a_name}**")
                    st.code(c.source_a_value, language=None)
                with b:
                    st.markdown(f"**{c.source_b_name}**")
                    st.code(c.source_b_value, language=None)

        st.markdown("---")
        if st.button("🔮 Reconcile All Contradictions", use_container_width=True):
            with st.spinner("ReconcilerAgent analyzing all conflicts with Gemini 2.0 Flash..."):
                results = orch.reconcile_contradictions()
                st.session_state.reconciliation_results = results

        if st.session_state.reconciliation_results:
            st.markdown("### ⚖️ ReconcilerAgent Verdicts")
            for r in st.session_state.reconciliation_results:
                with st.expander(f"📋 {r.get('contradiction', 'Resolution')[:80]}", expanded=True):
                    st.markdown(r["resolution"])
                    st.caption(f"Confidence: {r['confidence']:.0%}")
    else:
        st.success("✅ No contradictions detected across data sources.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PROACTIVE INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_alerts:
    st.markdown("## 🔔 Proactive Intelligence")
    st.caption("Insights surfaced autonomously by ValidatorAgent + ForecasterAgent — without anyone asking.")

    if st.button("🔍 Generate Proactive Intelligence Report", use_container_width=True):
        with st.spinner("ValidatorAgent + ForecasterAgent scanning all data sources..."):
            insights = orch.get_proactive_insights()
            st.session_state.proactive_insights = insights

    if st.session_state.proactive_insights:
        ins = st.session_state.proactive_insights

        # Anomaly section
        with st.expander("🔍 Anomaly Detection — ValidatorAgent", expanded=True):
            st.markdown(ins.get("anomalies", "No anomalies."))
            if "anomaly_analysis" in ins:
                st.markdown("---\n**🤖 AI Root-Cause Analysis:**")
                st.markdown(ins["anomaly_analysis"])

        # Forecast section
        with st.expander("📈 Trend Forecast — ForecasterAgent", expanded=True):
            st.markdown(ins.get("forecast", "No forecasts."))

        with st.expander("⚡ Contradictions Summary"):
            st.markdown(ins.get("contradictions", "None."))

        # Quick anomaly stats
        if orch.validator.anomalies:
            st.markdown("### Anomaly Breakdown")
            anom_types = {}
            for a in orch.validator.anomalies:
                anom_types[a.anomaly_type] = anom_types.get(a.anomaly_type, 0) + 1

            fig = go.Figure(go.Bar(
                x=list(anom_types.values()),
                y=list(anom_types.keys()),
                orientation="h",
                marker_color=["#22C55E", "#FBBF24", "#EF4444", "#FFFFFF",
                               "#16A34A", "#3B82F6"][:len(anom_types)],
                text=list(anom_types.values()),
                textposition="auto",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="rgba(255,255,255,0.7)", height=250,
                margin=dict(l=20, r=20, t=10, b=20),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Click the button above to generate proactive anomaly and forecast intelligence reports.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — KNOWLEDGE GRAPH
# ══════════════════════════════════════════════════════════════════════════════
with tab_kg:
    st.markdown("## 🕸️ Knowledge Graph")
    st.caption("Entities, relationships, and contradiction edges — extracted and visualized automatically.")

    kg = orch.knowledge_graph
    stats = kg.get_stats()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entities", stats["total_entities"])
    c2.metric("Relations", stats["total_relations"])
    c3.metric("Contradictions", stats["contradiction_count"])
    c4.metric("Components", stats["connected_components"])

    left, right = st.columns(2)
    with left:
        if stats.get("entity_types"):
            fig = px.pie(
                values=list(stats["entity_types"].values()),
                names=list(stats["entity_types"].keys()),
                title="Entity Types",
                color_discrete_sequence=["#22C55E", "#FFFFFF", "#16A34A", "#FBBF24",
                                         "#3B82F6", "#EF4444", "#A78BFA", "#FB923C"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="rgba(255,255,255,0.7)", height=320,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        if stats.get("relation_types"):
            fig2 = px.bar(
                x=list(stats["relation_types"].values()),
                y=list(stats["relation_types"].keys()),
                orientation="h", title="Relation Types",
                color_discrete_sequence=["#22C55E"],
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="rgba(255,255,255,0.7)", height=320, showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            )
            st.plotly_chart(fig2, use_container_width=True)

    if st.button("🗺️ Generate Interactive Graph Visualization"):
        with st.spinner("Building interactive PyVis graph..."):
            out = os.path.join(PROJECT_ROOT, "app", "knowledge_graph.html")
            kg.export_pyvis(out)
            if os.path.exists(out):
                with open(out, "r", encoding="utf-8") as f:
                    st.components.v1.html(f.read(), height=650, scrolling=True)

    st.markdown("### 🔎 Entity Search")
    st.caption("Search for any entity to see its connections and contradiction involvement.")
    eq = st.text_input("Search:", placeholder="e.g. North America, Cloud Platform, Q3 2024")
    if eq:
        info = kg.query_entity(eq)
        if info.get("found"):
            e = info["entity"]
            st.markdown(f"**{e['name']}** — `{e['type']}` — Sources: {', '.join(e['sources'])}")
            if info.get("contradiction_count", 0) > 0:
                st.warning(f"⚠️ {info['contradiction_count']} contradictions involve this entity")
            if info.get("connections"):
                st.dataframe(pd.DataFrame(info["connections"][:15]),
                             use_container_width=True, hide_index=True)
        else:
            st.info(f"'{eq}' not found in the knowledge graph.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — DATA LINEAGE
# ══════════════════════════════════════════════════════════════════════════════
with tab_lineage:
    st.markdown("## 📋 Data Lineage")
    st.caption("Every fact in every answer is traceable — exact source file, row, column, timestamp, and quality score.")

    ld = orch.lineage_tracker.to_dict()
    if ld:
        for fact, chain in ld.items():
            with st.expander(f"📌 {fact[:70]}..."):
                st.markdown(f"`{chain['fact_id']}` · **{chain['confidence']:.0%}** · "
                            f"Sources: {', '.join(chain['sources'])}")
                if chain.get("nodes"):
                    st.dataframe(pd.DataFrame(chain["nodes"]),
                                 use_container_width=True, hide_index=True)
    else:
        st.info("Ask questions in the Intelligence Query tab to build lineage chains.")

    st.markdown("### 📦 Ingested Sources")
    if orch.federation.sources:
        rows = []
        for src in orch.federation.sources.values():
            rows.append({
                "Name": src.source_name,
                "Type": src.source_type.upper(),
                "Rows": f"{src.row_count:,}" if src.row_count else "—",
                "Credibility": f"{src.credibility_score:.0%}",
                "Ingested": src.ingested_at[:19] if src.ingested_at else "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='footer-text'>"
    "🧠 NeuralNexus · Autonomous Financial Intelligence Fabric · "
    "Gemini 2.0 Flash · 5-Agent System · "
    "AI Agent Olympics Hackathon 2026 — lablab.ai"
    "</div>",
    unsafe_allow_html=True,
)
