# Agent.md - Project Context & Guidelines

> [!NOTE]
> This file serves as the primary context source for AI agents (and human developers) working on the Pharma Agentic AI Solution. It defines the architecture, constraints, and "Golden Paths" for implementation.

## 1. Project Overview
**Goal**: Build an Agentic AI system that accelerates pharmaceutical innovation by repurposing existing molecules.
**Core Value**: Reduces research time from months to minutes by orchestrating data retrieval across market, patent, clinical, and internal sources.
**Key Deliverable**: A functional demo showcasing a "Master Agent" orchestrating "Worker Agents" to answer complex strategic queries.

## 2. Reference Architecture
The system follows a **Multi-Agent Hub-and-Spoke** architecture with explicit layers:

### Layers
1.  **Orchestration Layer**:
    - **Master Agent**: Uses LangGraph/CrewAI to manage state and delegate tasks.
    - **Router/Classifier**: Decides which Worker Agents are needed based on user intent.
2.  **Agent Layer (Worker Nodes)**:
    - Specialized agents acting as **MCP Clients** (Model Context Protocol) to interface with specific data sources.
    - **Agents**: IQVIA (Market), EXIM (Trade), Patent (IP), Clinical (Trials), Internal (RAG), Web (Search).
3.  **Knowledge & Storage Layer**:
    - **Vector DB**: Stores embeddings for Internal Docs (RAG).
    - **State Store**: Persists conversation history and agent intermediate steps (checkpoints).
4.  **Integration Layer**:
    - Standardized interfaces (Mock APIs) for all external data sources.

## 3. Agent Definitions (The "Crew")

| Agent Name | Role | Inputs | Key Tools | Output Schema |
| :--- | :--- | :--- | :--- | :--- |
| **Master Agent** | Orchestrator | User Query | `delegate_task`, `synthesize_report` | Final Answer / PDF Link |
| **IQVIA Agent** | Market Analyst | Molecule, Region | `get_market_size`, `get_competitors` | `{ market_size, cagr, competitors }` |
| **EXIM Agent** | Trade Analyst | Molecule, Country | `get_import_volume`, `get_pricing` | `{ volume_kg, source_countries }` |
| **Patent Agent** | IP Analyst | Molecule | `check_expiry`, `check_fto` | `{ patents: [{expiry, status}] }` |
| **Clinical Agent** | R&D Analyst | Indication | `list_active_trials` | `{ trials: [{phase, sponsor}] }` |
| **Internal Agent** | Strategist | Query String | `search_internal_docs` | `{ summaries: [text], sources: [] }` |
| **Web Agent** | Researcher | Query String | `google_search` | `{ results: [{title, snippet}] }` |
| **Social Agent** | Patient Voice | Molecule, Disease | `scrape_forums` | `{ sentiment: str, complaints: [str] }` |
| **Competitor Agent** | War Gamer | Strategy, Molecule | `analyze_strategy` | `{ risks: [str], counter_moves: [str] }` |

## 4. Data Flow & Orchestration
1.  **User Query**: "Find whitespace for Molecule X in India."
2.  **Master Agent**:
    - Analyzes intent -> Needs Market Data (IQVIA) + Patent Data (Patent Agent).
    - **Parallel Execution**: Dispatches tasks to IQVIA and Patent agents.
3.  **Worker Agents**:
    - Call respective Mock APIs.
    - Return structured JSON.
4.  **Master Agent**:
    - Synthesizes: "Market is growing (IQVIA) AND Patent expires in 2025 (Patent) -> Opportunity."
    - Calls **Report Generator** to create PDF.
5.  **Response**: Returns text summary + PDF link.

## 5. Mock Data Standards
- **Format**: JSON or CSV.
- **Location**: `a:/Projects/Pharma/mock_data/`
- **Constraint**: Agents MUST NOT fail if data is missing; they should return "Data not available" gracefully.

## 6. Development Guidelines
- **Tech Stack**: Python 3.10+, LangGraph (Orchestration), FastAPI (Backend), Streamlit (Frontend).
- **LLM**: Groq (Llama 3 70B) for low-latency inference.
- **Code Style**: Type-hinted Python (`def func(x: int) -> str:`).
- **Error Handling**: All agent tools must have try/catch blocks to prevent crashing the orchestration loop.

## 7. Evaluation & Golden Tasks
To verify the system, run these "Golden Tasks":

### Task 1: The "Whitespace" Query
- **Input**: "Which respiratory diseases show low competition but high patient burden in India?"
- **Success Criteria**:
    - IQVIA Agent identifies "Respiratory" market data.
    - Clinical Agent checks trial density (Low competition).
    - Master Agent combines these to suggest a disease area.

### Task 2: The "Repurposing" Query
- **Input**: "Identify potential repurposing opportunities for Pembrolizumab."
- **Success Criteria**:
    - Clinical Agent finds trials in new indications (Phase II/III).
    - Patent Agent checks if these new indications are covered.
    - Output lists specific diseases with "High Potential".

### Task 3: The "FTO" Check
- **Input**: "Check patent expiry for Sitagliptin in the US."
- **Success Criteria**:
    - Patent Agent returns exact date (e.g., "2022-11-24").
    - Master Agent confirms "Generic entry possible".

### Task 4: The "Patient Voice" Insight
- **Input**: "What are patients complaining about regarding current Diabetes injectables?"
- **Success Criteria**:
    - Social Agent scrapes mock forum data.
    - Identifies "needle pain" or "storage issues" as key complaints.
    - Master Agent highlights this as an innovation opportunity (e.g., "Develop oral formulation").

### Task 5: The "War Game" Simulation
- **Input**: "Simulate a launch of generic Rivaroxaban in 2025. What will competitors do?"
- **Success Criteria**:
    - Competitor Agent predicts "Price war" or "Authorized generic launch".
    - Output includes a "Risk Assessment" table.

## 8. Metrics (Observability)
- **Latency**: End-to-end response time < 10s (using Groq).
- **Tool Usage**: % of queries where correct tools were called.
- **Hallucination Rate**: % of responses citing non-existent data (Target: 0%).
