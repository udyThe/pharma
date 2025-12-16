# Data Assumptions & Mock API Schemas

## 1. IQVIA Mock API
- **Assumption**: Returns aggregated market data.
- **Schema**:
```json
{
  "molecule": "String",
  "region": "String",
  "market_size_usd_mn": "Float",
  "cagr_percent": "Float",
  "top_competitors": ["String"],
  "generic_penetration": "String (Low/Med/High)"
}
```

## 2. EXIM Mock Server
- **Assumption**: Tracks API (Active Pharmaceutical Ingredient) movement.
- **Schema**:
```json
{
  "molecule": "String",
  "total_import_volume_kg": "Integer",
  "major_source_countries": ["String"],
  "average_price_per_kg": "Float"
}
```

## 3. USPTO API Clone
- **Assumption**: Simplified patent data focusing on expiry.
- **Schema**:
```json
{
  "molecule": "String",
  "patents": [
    {
      "patent_number": "String",
      "type": "String (Composition/Formulation)",
      "expiry_date": "YYYY-MM-DD",
      "status": "String (Active/Expired)"
    }
  ]
}
```

## 4. Clinical Trials Stub
- **Assumption**: Snapshot of current pipeline.
- **Schema**:
```json
{
  "indication": "String",
  "active_trials": [
    {
      "nct_id": "String",
      "phase": "String",
      "drug_name": "String",
      "sponsor": "String"
    }
  ]
}
```

## 5. Internal Docs Repository
- **Assumption**: A folder of PDFs. We will simulate the RAG output.
- **Mock Data**: A JSON file mapping queries to pre-written summaries.

## 6. Web Search Proxy
- **Assumption**: Returns a list of "search results" with titles and snippets.
- **Schema**:
## 7. Social Media Mock
- **Assumption**: Scraped forum posts.
- **Schema**:
```json
[
  {
    "molecule": "String",
    "source": "String (Reddit/PatientsLikeMe)",
    "post_text": "String",
    "sentiment": "Float (-1.0 to 1.0)",
    "date": "YYYY-MM-DD"
  }
]
```

## 8. Competitor Intel Mock
- **Assumption**: Intelligence reports on competitor strategy.
- **Schema**:
```json
[
  {
    "molecule": "String",
    "competitor": "String",
    "predicted_strategy": "String",
    "likelihood": "High/Med/Low",
    "impact": "String"
  }
]
```
