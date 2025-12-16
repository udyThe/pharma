"""
Pharma Agentic AI - Dashboard Page
Analytics dashboard with KPIs, charts, and insights.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
from src.services.data_provider import fetch_market_data, fetch_patent_data, fetch_clinical_data

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

st.set_page_config(
    page_title="Dashboard - Pharma AI",
    page_icon="📊",
    layout="wide"
)


def load_market_data():
    """Load market data from live API if configured, else DB."""
    api_data = fetch_market_data()
    if api_data:
        return api_data
    try:
        from src.database.db import get_db_session
        from src.database.models import MarketData
        with get_db_session() as db:
            records = db.query(MarketData).all()
            return [
                {
                    "molecule": r.molecule,
                    "region": r.region,
                    "therapy_area": r.therapy_area,
                    "indication": r.indication,
                    "market_size_usd_mn": r.market_size_usd_mn,
                    "cagr_percent": r.cagr_percent,
                    "top_competitors": r.top_competitors or [],
                    "generic_penetration": r.generic_penetration,
                    "patient_burden": r.patient_burden,
                    "competition_level": r.competition_level or r.generic_penetration
                }
                for r in records
            ]
    except Exception as e:
        st.error(f"Could not load market data: {e}")
    # Hardcoded realistic fallback
    return [
        {"molecule": "Paracetamol (Dolo 650)", "region": "India", "therapy_area": "Analgesic", "indication": "Fever/Pain",
         "market_size_usd_mn": 420, "cagr_percent": 6.2, "top_competitors": ["Calpol", "Crocin"], "generic_penetration": "High", "patient_burden": "High", "competition_level": "High"},
        {"molecule": "Sitagliptin", "region": "Global", "therapy_area": "Diabetes", "indication": "T2D",
         "market_size_usd_mn": 1800, "cagr_percent": 4.5, "top_competitors": ["Vildagliptin", "Linagliptin"], "generic_penetration": "Medium", "patient_burden": "Very High", "competition_level": "Medium"},
        {"molecule": "Pembrolizumab", "region": "Global", "therapy_area": "Oncology", "indication": "NSCLC",
         "market_size_usd_mn": 25000, "cagr_percent": 12.5, "top_competitors": ["Nivolumab", "Atezolizumab"], "generic_penetration": "Low", "patient_burden": "High", "competition_level": "Low"},
    ]


def load_patent_data():
    """Load patent data from live API if configured, else DB."""
    api_data = fetch_patent_data()
    if api_data:
        # Flatten common nested patent structure
        flattened = []
        for entry in api_data:
            molecule = entry.get("molecule")
            patents = entry.get("patents") if isinstance(entry, dict) else None
            if patents:
                for patent in patents:
                    flattened.append({
                        "molecule": molecule,
                        "patent_number": patent.get("patent_number"),
                        "type": patent.get("type") or patent.get("patent_type"),
                        "expiry_date": patent.get("expiry_date"),
                        "status": patent.get("status", "Active")
                    })
            else:
                flattened.append(entry)
        return flattened
    try:
        from src.database.db import get_db_session
        from src.database.models import Patent
        with get_db_session() as db:
            records = db.query(Patent).all()
            return [
                {
                    "molecule": r.molecule,
                    "patent_number": r.patent_number,
                    "type": r.patent_type,
                    "expiry_date": r.expiry_date.strftime("%Y-%m-%d") if r.expiry_date else None,
                    "status": r.status.value if hasattr(r.status, 'value') else str(r.status)
                }
                for r in records
            ]
    except Exception as e:
        st.error(f"Could not load patent data: {e}")
    # Hardcoded realistic fallback
    return [
        {"molecule": "Paracetamol (Dolo 650)", "patent_number": "IN-Formulation-2010", "type": "Formulation", "expiry_date": "2027-12-31", "status": "Active"},
        {"molecule": "Sitagliptin", "patent_number": "US7326708", "type": "Composition of Matter", "expiry_date": "2022-11-24", "status": "Expired"},
        {"molecule": "Pembrolizumab", "patent_number": "US8354509", "type": "Composition of Matter", "expiry_date": "2028-06-15", "status": "Active"},
    ]


def load_clinical_data():
    """Load clinical trial data from live API if configured, else DB."""
    api_data = fetch_clinical_data()
    if api_data:
        flattened = []
        for entry in api_data:
            if "active_trials" in entry:
                indication = entry.get("indication")
                therapy_area = entry.get("therapy_area", "")
                for trial in entry.get("active_trials", []):
                    flattened.append({
                        "nct_id": trial.get("nct_id"),
                        "indication": indication,
                        "therapy_area": therapy_area,
                        "phase": trial.get("phase"),
                        "drug_name": trial.get("drug_name"),
                        "sponsor": trial.get("sponsor"),
                        "patient_burden_score": entry.get("patient_burden_score"),
                        "competition_density": entry.get("competition_density"),
                        "unmet_need": entry.get("unmet_need")
                    })
            else:
                flattened.append(entry)
        return flattened
    try:
        from src.database.db import get_db_session
        from src.database.models import ClinicalTrial
        with get_db_session() as db:
            records = db.query(ClinicalTrial).all()
            return [
                {
                    "nct_id": r.nct_id,
                    "indication": r.indication,
                    "therapy_area": r.therapy_area,
                    "phase": r.phase,
                    "drug_name": r.drug_name,
                    "sponsor": r.sponsor,
                    "patient_burden_score": r.patient_burden_score,
                    "competition_density": r.competition_density,
                    "unmet_need": r.unmet_need
                }
                for r in records
            ]
    except Exception as e:
        st.error(f"Could not load clinical data: {e}")
    # Hardcoded realistic fallback
    return [
        {"nct_id": "NCT01234567", "indication": "Fever/Pain", "therapy_area": "Analgesic", "phase": "Post-marketing", "drug_name": "Paracetamol", "sponsor": "Generic", "patient_burden_score": 3, "competition_density": "High", "unmet_need": "Low"},
        {"nct_id": "NCT09876543", "indication": "Type 2 Diabetes", "therapy_area": "Diabetes", "phase": "Phase IV", "drug_name": "Sitagliptin", "sponsor": "Merck", "patient_burden_score": 8.5, "competition_density": "Medium", "unmet_need": "Medium"},
        {"nct_id": "NCT04123456", "indication": "Non-Small Cell Lung Cancer", "therapy_area": "Oncology", "phase": "Phase III", "drug_name": "Pembrolizumab", "sponsor": "Merck", "patient_burden_score": 9.1, "competition_density": "Low", "unmet_need": "High"},
    ]


def main():
    st.markdown("# 📊 Analytics Dashboard")
    st.markdown("Real-time insights into pharmaceutical market intelligence")
    
    # Load data
    market_data = load_market_data()
    patent_data = load_patent_data()
    clinical_data = load_clinical_data()
    
    # KPI Row
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_market = sum((d.get("market_size_usd_mn") or 0) for d in market_data)
        st.metric("Total Market Size", f"${total_market:,.0f}M", "+12% YoY")
    
    with col2:
        avg_cagr = sum((d.get("cagr_percent") or 0) for d in market_data) / len(market_data) if market_data else 0
        st.metric("Avg CAGR", f"{avg_cagr:.1f}%", "+2.3%")
    
    with col3:
        active_patents = sum(1 for p in patent_data if p.get("status") == "Active")
        st.metric("Active Patents", active_patents, f"/{len(patent_data)} total")
    
    with col4:
        st.metric("Clinical Trials", len(clinical_data), "across all phases")
    
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Market Size by Molecule")
        try:
            from src.services.analytics import ChartService
            fig = ChartService.market_size_chart(market_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")
    
    with col2:
        st.markdown("### Growth Rate (CAGR)")
        try:
            from src.services.analytics import ChartService
            fig = ChartService.cagr_comparison_chart(market_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Whitespace Analysis")
        try:
            from src.services.analytics import ChartService
            fig = ChartService.competition_matrix(market_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")
    
    with col2:
        st.markdown("### Therapy Area Distribution")
        try:
            from src.services.analytics import ChartService
            fig = ChartService.therapy_area_pie(market_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")
    
    # Charts Row 3
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Patent Expiry Timeline")
        try:
            from src.services.analytics import ChartService
            fig = ChartService.patent_timeline(patent_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")
    
    with col2:
        st.markdown("### Clinical Trial Pipeline")
        try:
            from src.services.analytics import ChartService
            # Restructure for funnel
            trial_data = [{"active_trials": [t]} for t in clinical_data]
            fig = ChartService.clinical_trials_funnel(trial_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")
    
    # Molecule Comparison
    st.markdown("---")
    st.markdown("### 🔬 Molecule Comparison Tool")
    
    molecules = list(set(d.get("molecule", "") for d in market_data))
    selected = st.multiselect("Select molecules to compare", molecules, default=molecules[:3] if len(molecules) >= 3 else molecules)
    
    if selected:
        try:
            from src.services.analytics import ChartService
            fig = ChartService.molecule_comparison(selected, market_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Comparison error: {e}")
    
    # Data Tables
    st.markdown("---")
    st.markdown("### 📋 Data Explorer")
    
    tab1, tab2, tab3 = st.tabs(["Market Data", "Patents", "Clinical Trials"])
    
    with tab1:
        if market_data:
            import pandas as pd
            df = pd.DataFrame(market_data)
            st.dataframe(df, use_container_width=True, height=300)
        else:
            st.info("No market data available")
    
    with tab2:
        if patent_data:
            import pandas as pd
            df = pd.DataFrame(patent_data)
            st.dataframe(df, use_container_width=True, height=300)
        else:
            st.info("No patent data available")
    
    with tab3:
        if clinical_data:
            import pandas as pd
            df = pd.DataFrame(clinical_data)
            st.dataframe(df, use_container_width=True, height=300)
        else:
            st.info("No clinical trial data available")
    
    # Footer
    st.markdown("---")
    st.caption(f"Dashboard generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Pharma Agentic AI")


if __name__ == "__main__":
    main()
