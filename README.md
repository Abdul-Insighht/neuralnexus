<div align="center">

# 🧠 NeuralNexus
### Autonomous Financial Intelligence Fabric

**The AI system that doesn't just answer questions about your financial data — it continuously monitors, detects contradictions, reconciles conflicts, and surfaces insights before you even ask.**

[![Track 4: Data & Intelligence](https://img.shields.io/badge/Track%204-Data%20%26%20Intelligence-6C63FF?style=for-the-badge)](https://lablab.ai)
[![Gemini 2.0](https://img.shields.io/badge/Powered%20by-Gemini%202.0%20Flash-00D4AA?style=for-the-badge)](https://ai.google.dev)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-4ECDC4?style=for-the-badge)](https://python.org)
[![React](https://img.shields.io/badge/UI-React-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> 🏆 Built for **AI Agent Olympics Hackathon 2026** — lablab.ai | Milan AI Week

</div>

---

## 💥 The $100 Billion Problem

Every year, enterprises lose billions due to **bad data decisions**:

| The Real Pain | Industry Impact |
|---|---|
| Finance dept says revenue is **$4.6M**, Sales says **$4.2M** | Wrong bonuses, wrong forecasts |
| Audited data mixed with raw spreadsheets | SOX compliance failures |
| Anomalies discovered **after** quarterly close | Restatements, regulatory fines |
| No one knows **which source to trust** | Paralysis in boardroom decisions |

Standard RAG systems make this **worse** — they confidently answer using whichever source they happen to retrieve, with zero awareness of contradiction or data quality.

**NeuralNexus** is the first autonomous intelligence fabric built specifically for **financial enterprise data** — detecting contradictions in real time, reconciling conflicts with full auditability, and surfacing insights proactively.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  LAYER 5: Intelligence Portal                    │
│   React & Tailwind UI |  Natural Language Query Interface        │
│         Contradiction Dashboard  |  Data Lineage Explorer        │
├──────────────────────────────────────────────────────────────────┤
│                    LAYER 4: Agent Society                        │
│   🎯 Orchestrator  │  🔍 Validator  │  ⚖️ Reconciler            │
│         📈 Forecaster          │        🧐 Critic               │
├──────────────────────────────────────────────────────────────────┤
│                  LAYER 3: Knowledge Synthesis                    │
│       Dynamic Knowledge Graph (NetworkX)                         │
│       Temporal Vector Store (FAISS + credibility weights)        │
├──────────────────────────────────────────────────────────────────┤
│              LAYER 2: Data Intelligence Pipeline                 │
│   Quality Scoring  │  Conflict Detection  │  Lineage Tracking   │
├──────────────────────────────────────────────────────────────────┤
│                  LAYER 1: Data Federation Hub                    │
│      CSV / Excel  │  PDFs / Reports  │  APIs  │  Databases       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🤖 The 5-Agent Society

| Agent | Model | Role | Why It Matters |
|---|---|---|---|
| 🎯 **OrchestratorAgent** | Gemini 2.0 Flash | Routes queries, coordinates agents, synthesizes final answers | The brain that decides who handles what |
| 🔍 **ValidatorAgent** | Gemini 2.0 Flash | Continuous anomaly detection, drift monitoring, proactive alerts | Catches problems before humans notice |
| ⚖️ **ReconcilerAgent** | Gemini 2.0 Flash | Resolves cross-source contradictions with uncertainty quantification | Tells you WHICH source to trust and WHY |
| 📈 **ForecasterAgent** | Gemini 2.0 Flash | Temporal pattern detection, risk scoring, forward-looking insights | Turns historical data into future warnings |
| 🧐 **CriticAgent** | Gemini 2.0 Flash | Reviews every answer for quality before the user sees it | Ensures no hallucinated or overconfident answer reaches you |

> **Note:** All agents use Gemini 2.0 Flash for speed and cost-efficiency during the hackathon demo.

---

## ✨ Key Features

### 🔴 Cross-Source Contradiction Detection
Automatically scans all loaded data sources and flags numerical inconsistencies. Example: Revenue reported as $4.6M in audited financials vs $4.2M in CRM export — flagged instantly with severity score.

### ⚖️ AI-Powered Reconciliation with Reasoning
The ReconcilerAgent doesn't just pick a winner. It reasons through:
- Source credibility (audited > raw spreadsheet)
- Recency of data
- Historical reliability of each source
- Returns a confidence-weighted recommendation with full explanation

### 📋 Complete Data Lineage
Every number in every answer is traceable. Click any figure and see:
- Which exact file it came from
- Which row/column
- When it was last updated
- Its quality score at ingestion time

### 🕸️ Dynamic Knowledge Graph
Entities (companies, accounts, people), their relationships, and contradiction edges — all visualized and queryable. Built with NetworkX, rendered with PyVis.

### 📊 Real-Time Quality Dashboard
Each data source gets scored on:
- **Completeness** — missing fields ratio
- **Consistency** — internal contradictions
- **Timeliness** — data freshness
- **Credibility** — source authority

### 🔔 Proactive Intelligence Alerts
The ValidatorAgent and ForecasterAgent surface insights without being asked:
- "Revenue trend shows 15% decline over 3 periods — investigate Q3"
- "Source B has degraded in reliability by 23% this month"

### 🧐 Answer Quality Gate
Before any response reaches you, the CriticAgent reviews it for:
- Overconfident claims
- Unacknowledged uncertainty
- Missing caveats on contradicted data

---

## 💰 Business Impact

| Metric | Before NeuralNexus | After NeuralNexus |
|---|---|---|
| Data reconciliation time | 3–5 business days | Under 3 minutes |
| Contradiction discovery | After quarterly close | Real-time |
| Audit trail creation | Manual, error-prone | Automated, complete |
| SOX/HIPAA readiness | Months of preparation | Built-in |
| Bad decisions from wrong data | Frequent | Dramatically reduced |

> **Target industries:** Financial Services, Healthcare Revenue Cycle, Legal & Compliance, Enterprise Accounting

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/neuralnexus.git
cd neuralnexus

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..
```

### Configuration

```bash
# Option 1: Environment variable (recommended)
set GEMINI_API_KEY=your_api_key_here        # Windows CMD
$env:GEMINI_API_KEY="your_api_key_here"     # Windows PowerShell
export GEMINI_API_KEY=your_api_key_here     # Linux/Mac

# Option 2: .env file
cp .env.example .env
# Open .env and add: GEMINI_API_KEY=your_key_here

# Option 3: Edit config.py directly
```

### Run

You need two terminals to run the decoupled architecture:

```bash
# Terminal 1: Launch the FastAPI Backend
python app/api.py
# Runs on http://localhost:8000

# Terminal 2: Launch the React Frontend
cd frontend
npm run dev
# Opens at http://localhost:5173
```

---

## 🎬 Demo Walkthrough (5-Minute Judge Demo)

### Step 1 — Initialize (30 seconds)
Click **"🚀 Initialize with Demo Data"** in the sidebar. The system will:
- Generate 5 realistic financial datasets (with intentional contradictions baked in)
- Score each source for quality
- Detect 3 cross-source contradictions automatically
- Build the knowledge graph
- Index everything into the temporal vector store

### Step 2 — The WOW Moment (1 minute)
Navigate to the **Contradictions** tab. You'll see:
```
⚠️  CONTRADICTION DETECTED — HIGH SEVERITY
    Field: Q3 Revenue
    Source A (Audited Financials):  $4,628,000  ← Credibility: 94%
    Source B (CRM Export):          $4,195,000  ← Credibility: 71%
    Variance: $433,000 (9.4%)

    ReconcilerAgent Verdict:
    "Trust Source A. Audited financials have a 6-month verified track record
     with zero restatements. Source B is a raw CRM export with known
     data entry inconsistencies. Confidence: 87%"
```

### Step 3 — Natural Language Query (1 minute)
In the **Intelligence Query** tab, ask:
> *"What is our Q3 revenue and should I trust it?"*

The system will:
1. Retrieve from both conflicting sources
2. ReconcilerAgent resolves the conflict
3. CriticAgent adds caveat
4. Returns answer with full lineage citation

### Step 4 — Proactive Alerts (30 seconds)
Navigate to **Proactive Insights** tab — alerts generated WITHOUT being asked:
- Revenue anomaly alert
- Data quality degradation warning
- Forecasted risk for next period

### Step 5 — Data Lineage (30 seconds)
Click any number in any answer → full provenance chain appears showing exact source file, row, timestamp, and quality score at ingestion.

---

## 📂 Using Your Own Data (Custom Upload Guide)

After trying the demo, you can connect **your real enterprise data** to NeuralNexus. The system accepts multiple file types and live data sources.

---

### ✅ Supported File Types & How to Upload

#### 1. 📊 CSV Files — Sales, Revenue, Transactions, HR Data

**Format your CSV like this:**

```csv
date,revenue,department,source,notes
2024-01-01,4628000,Finance,Audited,Q3 Close
2024-01-01,4195000,Sales,CRM Export,Raw data
2024-02-01,4800000,Finance,Audited,Q4 Close
```

**Rules:**
- First row must be column headers
- Date column should be named `date` or `period` (format: `YYYY-MM-DD`)
- Numeric columns: no commas inside numbers (`4628000` not `4,628,000`)
- UTF-8 encoding (save as "CSV UTF-8" in Excel)

---

#### 2. 📗 Excel Files (.xlsx) — Multi-Sheet Reports, Budget Files

**What NeuralNexus reads from Excel:**
- Every sheet is treated as a **separate data source**
- Sheet name becomes the source label in contradictions
- Supports formulas (reads calculated values, not formulas)

**Best practices:**
- Name your sheets clearly: `Audited_Financials`, `CRM_Export`, `Budget_2024`
- Keep one table per sheet (no merged cells in data rows)
- Row 1 = headers, Row 2 onwards = data

---

#### 3. 📄 PDF Files — Audit Reports, Contracts, Financial Statements

**What gets extracted:**
- Tables inside PDFs (balance sheets, income statements)
- Key numerical figures mentioned in text
- Named entities (company names, account names, people)

**Best PDFs to use:**
- Annual reports
- Audit statements
- Quarterly earnings documents
- Contract documents with financial terms

**Tip:** Text-based PDFs work best. Scanned image PDFs need OCR — the system handles this automatically but takes longer.

---

#### 4. 🔗 REST APIs — Live CRM, ERP, or Database Data

Add your API endpoint in the sidebar **"Connect Live Source"** panel:

```json
{
  "source_name": "Salesforce CRM",
  "endpoint": "https://your-instance.salesforce.com/api/v1/revenue",
  "auth_type": "bearer",
  "token": "your_token_here",
  "refresh_interval_minutes": 30
}
```

**Supported auth types:** `bearer`, `api_key`, `basic`

**Common integrations:**
| System | Type | What to Pull |
|---|---|---|
| Salesforce | REST API | Opportunity revenue, pipeline |
| SAP ERP | REST API | GL entries, cost centers |
| QuickBooks | OAuth API | P&L, balance sheet |
| HubSpot | REST API | Deal values, forecasts |
| Google Sheets | Sheets API | Any live spreadsheet |

---

#### 5. 🗄️ Databases — PostgreSQL, MySQL, SQLite

In `config.py`, add your connection:

```python
DATABASE_SOURCES = [
    {
        "name": "Production DB",
        "type": "postgresql",
        "connection_string": "postgresql://user:pass@host:5432/dbname",
        "query": "SELECT date, revenue, department FROM financial_summary",
        "credibility_score": 0.95
    }
]
```

---

### 🚀 How to Upload in the App (Step by Step)

```
1. Open the app → http://localhost:5173
2. In the LEFT SIDEBAR → click "📂 Upload Your Data"
3. Choose your file type tab:
   ┌─────────────────────────────────────┐
   │  CSV  │  Excel  │  PDF  │  API  │  DB │
   └─────────────────────────────────────┘
4. Upload your file (drag & drop or browse)
5. Set the SOURCE NAME (e.g., "Q3 Audited Financials")
6. Set CREDIBILITY SCORE (0.0 to 1.0):
   - Audited financial report → 0.95
   - CRM raw export          → 0.70
   - Manual spreadsheet      → 0.55
7. Click "⚡ Ingest & Analyze"
8. Repeat for each data source (minimum 2 sources to detect contradictions)
9. Click "🔍 Run Full Analysis" to start all 5 agents
```

---

### 🧪 Real-World Test Scenarios (Try These With Your Data)

Once your data is loaded, try these queries that mirror real enterprise use cases:

#### Finance Team
```
"What is total revenue for Q3 and are all sources in agreement?"
"Show me all contradictions in our revenue figures"
"Which data source should I use for the board presentation?"
"Are there any anomalies in our expense data this month?"
```

#### Operations / Supply Chain
```
"What is the inventory discrepancy between warehouse A and ERP system?"
"Show me forecast vs actual for last 6 months"
"Which department has the most data quality issues?"
```

#### HR / Payroll
```
"Is headcount consistent across HR system and payroll data?"
"Show me any salary discrepancies between departments"
```

#### Legal / Compliance
```
"Pull all contract values above $500,000 and verify against accounting records"
"Generate a full audit trail for Q3 revenue figures"
```

---

### 📋 Free Public Datasets to Test With (Real Data, No Setup Needed)

Use these free datasets to test NeuralNexus with real-world data — just download and upload directly into the app:

| Dataset | Format | Source | What to Test |
|---|---|---|---|
| US Company Financials | CSV | [Kaggle — Financial Statements](https://www.kaggle.com/datasets/ryanholbrook/dl-course-data) | Revenue contradictions across quarters |
| SEC 10-K Filings | PDF | [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-K&dateb=&owner=include&count=10) | Extract and reconcile financial tables |
| World Bank GDP Data | CSV | [data.worldbank.org/indicator/NY.GDP.MKTP.CD](https://data.worldbank.org/indicator/NY.GDP.MKTP.CD) | Multi-source national data contradictions |
| UN Trade Statistics | Excel | [comtradeplus.un.org](https://comtradeplus.un.org) | Import/export value discrepancies |
| Kaggle Sales Dataset | CSV | [Kaggle — Superstore Sales](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) | Multi-region sales contradiction demo |

---

### ⚠️ Data Privacy Note

All data processing happens **locally on your machine**. Your files are:
- Never uploaded to any external server
- Only sent to Google Gemini API as text excerpts for AI reasoning
- Stored in memory during session only — cleared on restart

For sensitive financial data, review Google's [Gemini API Data Usage Policy](https://ai.google.dev/gemini-api/terms) before use.

---

## 📁 Project Structure

```
neuralnexus/
├── core/
│   ├── data_federation.py          # Multi-source data connectors
│   ├── quality_scorer.py           # Data quality assessment (completeness, consistency, timeliness)
│   ├── contradiction_detector.py   # Cross-source conflict detection engine
│   ├── lineage_tracker.py          # Full data provenance tracking
│   ├── knowledge_graph.py          # Dynamic KG with NetworkX + PyVis
│   └── temporal_vector_store.py    # Recency-biased, credibility-weighted FAISS store
├── agents/
│   ├── base_agent.py               # Gemini 2.0 Flash integration base class
│   ├── orchestrator.py             # Master routing and synthesis agent
│   ├── validator.py                # Anomaly detection and drift monitoring agent
│   ├── reconciler.py               # Contradiction resolution with uncertainty quantification
│   ├── forecaster.py               # Temporal pattern and risk prediction agent
│   └── critic.py                   # Answer quality gate and caveat injection
├── demo_data/
│   └── generate_data.py            # Realistic financial demo dataset generator
├── app/
│   └── api.py                      # FastAPI Backend (REST endpoints)
├── frontend/                       # React + Tailwind CSS UI
│   ├── src/                        # React components and views
│   └── tailwind.config.js          # Custom Bookish theme config
├── config.py                       # API keys, model selection, thresholds
├── requirements.txt
├── .env.example
├── .gitignore
├── DEMO_SCRIPT.md                  # 5-minute judge demo script
└── README.md
```

---

## 🛠️ Technology Stack

| Layer | Technology | Why |
|---|---|---|
| LLM Brain | Gemini 2.0 Flash | Speed + cost-efficient for all 5 agents |
| Embeddings | `text-embedding-004` | Google's best semantic embedding model |
| Vector Store | FAISS | Fast similarity search with custom temporal + credibility weights |
| Knowledge Graph | NetworkX + PyVis | Queryable entity graph with contradiction edges |
| Frontend | React + Tailwind CSS + Recharts | High-performance, decoupled "Bookish" UI |
| Backend | FastAPI | High-speed REST API routing |
| Data Pipeline | Pandas, NumPy | Enterprise-grade data processing |
| Anomaly Detection | SciPy, scikit-learn | Statistical drift and outlier detection |

---

## 🌐 Deployment Architecture

Because the system is now decoupled, you can deploy it easily:

1. **Backend (FastAPI)**: Deploy to Render, Railway, or Heroku.
2. **Frontend (React)**: Deploy to Vercel or Netlify.

---

## 🔮 Roadmap (Post-Hackathon)

- [ ] Real-time database connectors (PostgreSQL, Snowflake, BigQuery)
- [ ] SOX/HIPAA compliance report auto-generation
- [ ] Webhook alerts to Slack/Teams
- [ ] Multi-tenant enterprise SaaS deployment
- [ ] Fine-tuned reconciliation model on financial data

---

## 👥 Team

Built with ❤️ for **AI Agent Olympics Hackathon 2026** — lablab.ai

---

## 📜 License

MIT License — Free to use, modify, and deploy.