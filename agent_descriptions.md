# Agent Descriptions & Workflows

## 1. Master Agent (Orchestrator)
- **Role**: The central brain that interfaces with the user.
- **Input**: Natural language query (e.g., "Identify whitespace opportunities for Molecule X in India").
- **Logic**:
  1.  **Decomposition**: Breaks query into:
      - "Get market size for Molecule X in India" -> IQVIA Agent
      - "Check patent expiry for Molecule X" -> Patent Agent
      - "List active trials for Molecule X" -> Clinical Trials Agent
  2.  **Delegation**: Calls Worker Agents in parallel or sequence.
  3.  **Synthesis**: Combines outputs. If Patent Agent says "Expires 2026" and IQVIA says "Market growing 15%", Master Agent concludes "High potential for biosimilar launch in 2026".
- **Output**: Structured JSON response containing synthesized insights, references to data sources, and a flag to trigger the Report Generator.

## 2. IQVIA Insights Agent
- **Role**: Market Data Specialist.
- **Input**: Molecule Name, Therapy Area, Region.
- **Tools**: `query_iqvia_mock_api(molecule, region)`
- **Output**:
  - Market Size (USD Mn)
  - CAGR (%)
  - Top Competitors
  - Volume Growth trends

## 3. EXIM Trends Agent
- **Role**: Supply Chain & Trade Analyst.
- **Input**: Molecule Name, Country.
- **Tools**: `query_exim_mock_api(molecule)`
- **Output**:
  - Import/Export Volumes (kg/tons)
  - Major Importers/Exporters
  - Price trends per kg

## 4. Patent Landscape Agent
- **Role**: IP Legal Analyst.
- **Input**: Molecule Name.
- **Tools**: `query_uspto_mock_api(molecule)`
- **Output**:
  - Key Patents (Composition of Matter, Process, Formulation)
  - Expiry Dates
  - FTO (Freedom to Operate) Risk Level (High/Medium/Low)

## 5. Clinical Trials Agent
- **Role**: R&D Pipeline Analyst.
- **Input**: Indication / Disease, Molecule.
- **Tools**: `query_clinical_trials_stub(indication)`
- **Output**:
  - Number of Active Trials (Phase I/II/III)
  - Key Sponsors
  - Emerging Indications (repurposing opportunities)

## 6. Internal Knowledge Agent
- **Role**: Corporate Strategist.
- **Input**: Keywords, Topics.
- **Tools**: `search_internal_docs(query)` (RAG over PDF repository)
- **Output**:
  - Summaries of internal strategy decks.
  - Past field insights.
  - SWOT analysis from internal reports.

## 7. Web Intelligence Agent
- **Role**: External Researcher.
- **Input**: Search Query.
- **Tools**: `web_search_proxy(query)`
- **Output**:
  - Recent news (approvals, recalls).
  - Clinical guidelines updates.
  - Competitor announcements.

## 8. Report Generator Agent
- **Role**: Publisher.
- **Input**: Synthesized JSON from Master Agent.
## 9. Social Listening Agent (Patient Voice)
- **Role**: Qualitative Researcher.
- **Input**: Molecule Name, Disease Area.
- **Tools**: `scrape_social_media_mock(query)`
- **Output**:
  - Sentiment Score (-1 to +1)
  - Key Complaint Themes (e.g., "Side effects", "Cost", "Ease of use")
  - Direct Patient Quotes

## 10. Competitor Agent (War Gamer)
- **Role**: Strategic Red Teamer.
- **Input**: Proposed Strategy, Molecule.
- **Tools**: `query_competitor_intel_mock(molecule)`
- **Output**:
  - Predicted Competitor Moves (e.g., "Price cut", "Litigation")
  - Threat Level (High/Medium/Low)
  - Counter-Strategy Recommendations
