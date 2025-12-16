"""
Pharma Agentic AI - Compare Page
Side-by-side molecule and company comparison.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from src.services.data_provider import (
    fetch_market_data,
    fetch_patent_data,
    fetch_clinical_data,
    fetch_competitor_data,
    fetch_social_data,
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

st.set_page_config(
    page_title="Compare - Pharma AI",
    page_icon="⚖️",
    layout="wide"
)


def load_all_data():
    """Load all data from database."""
    data = {
        "market": [],
        "patents": [],
        "trials": [],
        "competitors": [],
        "social": []
    }
    
    try:
        from src.database.db import get_db_session
        from src.database.models import MarketData, Patent, ClinicalTrial, Competitor, SocialPost
        
        with get_db_session() as db:
            # Market data
            for r in db.query(MarketData).all():
                data["market"].append({
                    "molecule": r.molecule,
                    "region": r.region,
                    "therapy_area": r.therapy_area,
                    "market_size_usd_mn": r.market_size_usd_mn,
                    "cagr_percent": r.cagr_percent,
                    "generic_penetration": r.generic_penetration,
                    "patient_burden": r.patient_burden,
                    "competition_level": r.competition_level or r.generic_penetration
                })
            
            # Patents
            for r in db.query(Patent).all():
                data["patents"].append({
                    "molecule": r.molecule,
                    "patent_number": r.patent_number,
                    "type": r.patent_type,
                    "expiry_date": r.expiry_date.strftime("%Y-%m-%d") if r.expiry_date else "N/A",
                    "status": r.status.value if hasattr(r.status, 'value') else str(r.status)
                })
            
            # Clinical trials
            for r in db.query(ClinicalTrial).all():
                data["trials"].append({
                    "molecule": r.drug_name,
                    "indication": r.indication,
                    "phase": r.phase,
                    "sponsor": r.sponsor,
                    "nct_id": r.nct_id
                })
            
            # Competitors
            for r in db.query(Competitor).all():
                data["competitors"].append({
                    "molecule": r.molecule,
                    "competitor": r.competitor_name,
                    "strategy": r.predicted_strategy,
                    "likelihood": r.likelihood,
                    "impact": r.impact
                })
            
            # Social/Patient sentiment
            for r in db.query(SocialPost).all():
                data["social"].append({
                    "molecule": r.molecule,
                    "sentiment": r.sentiment,
                    "source": r.source,
                    "complaint": r.complaint_theme,
                    "post": r.post_text[:100]
                })
    except Exception as e:
        st.warning(f"DB unavailable, trying external sources. ({e})")
    
    # External data (preferred; Tavily fallback inside data_provider)
    try:
        market_api = fetch_market_data()
        if market_api:
            data["market"] = market_api
        patent_api = fetch_patent_data()
        if patent_api:
            flattened = []
            for entry in patent_api:
                mol = entry.get("molecule", "")
                patents = entry.get("patents", entry if isinstance(entry, list) else [])
                for p in patents:
                    flattened.append({
                        "molecule": mol or p.get("molecule", ""),
                        "patent_number": p.get("patent_number", "N/A"),
                        "type": p.get("type") or p.get("patent_type") or "Unknown",
                        "expiry_date": p.get("expiry_date", "Unknown"),
                        "status": p.get("status", "Unknown")
                    })
            if flattened:
                data["patents"] = flattened
        clinical_api = fetch_clinical_data()
        if clinical_api:
            trials = []
            for entry in clinical_api:
                indication = entry.get("indication")
                active = entry.get("active_trials") if isinstance(entry, dict) else []
                if active is None:
                    active = []
                if active:
                    for trial in active:
                        if isinstance(trial, dict):
                            trials.append({
                                "molecule": trial.get("drug_name"),
                                "indication": indication,
                                "phase": trial.get("phase"),
                                "sponsor": trial.get("sponsor"),
                                "nct_id": trial.get("nct_id", "N/A")
                            })
                else:
                    trials.append({
                        "molecule": entry.get("drug_name"),
                        "indication": indication,
                        "phase": entry.get("phase"),
                        "sponsor": entry.get("sponsor"),
                        "nct_id": entry.get("nct_id", "N/A")
                    })
            if trials:
                data["trials"] = trials
        comp_api = fetch_competitor_data()
        if comp_api:
            data["competitors"] = [
                {
                    "molecule": c.get("molecule"),
                    "competitor": c.get("competitor") or c.get("company") or c.get("title"),
                    "strategy": c.get("predicted_strategy") or c.get("strategy") or c.get("content", "")[:200],
                    "likelihood": c.get("likelihood", "Medium"),
                    "impact": c.get("impact", "")
                }
                for c in comp_api
            ]
        social_api = fetch_social_data()
        if social_api:
            data["social"] = [
                {
                    "molecule": s.get("molecule"),
                    "sentiment": s.get("sentiment", 0),
                    "source": s.get("source"),
                    "complaint": s.get("complaint_theme") or s.get("complaint"),
                    "post": (s.get("post_text") or s.get("post") or "")[:100]
                }
                for s in social_api
            ]
    except Exception as e:
        st.warning(f"External data unavailable: {e}")

    # Final safety fallback to realistic samples if everything is empty
    if not data["market"]:
        data["market"] = [
            {"molecule": "Paracetamol (Dolo 650)", "region": "India", "therapy_area": "Analgesic", "indication": "Fever/Pain",
             "market_size_usd_mn": 420, "cagr_percent": 6.2, "generic_penetration": "High", "patient_burden": "High", "competition_level": "High"},
            {"molecule": "Sitagliptin", "region": "Global", "therapy_area": "Diabetes", "indication": "T2D",
             "market_size_usd_mn": 1800, "cagr_percent": 4.5, "generic_penetration": "Medium", "patient_burden": "Very High", "competition_level": "Medium"},
            {"molecule": "Pembrolizumab", "region": "Global", "therapy_area": "Oncology", "indication": "NSCLC",
             "market_size_usd_mn": 25000, "cagr_percent": 12.5, "generic_penetration": "Low", "patient_burden": "High", "competition_level": "Low"},
        ]
    if not data["patents"]:
        data["patents"] = [
            {"molecule": "Paracetamol (Dolo 650)", "patent_number": "IN-Formulation-2010", "type": "Formulation", "expiry_date": "2027-12-31", "status": "Active"},
            {"molecule": "Sitagliptin", "patent_number": "US7326708", "type": "Composition of Matter", "expiry_date": "2022-11-24", "status": "Expired"},
            {"molecule": "Pembrolizumab", "patent_number": "US8354509", "type": "Composition of Matter", "expiry_date": "2028-06-15", "status": "Active"},
        ]
    if not data["trials"]:
        data["trials"] = [
            {"molecule": "Paracetamol", "indication": "Fever/Pain", "phase": "Post-marketing", "sponsor": "Generic", "nct_id": "N/A"},
            {"molecule": "Sitagliptin", "indication": "Type 2 Diabetes", "phase": "Phase IV", "sponsor": "Merck", "nct_id": "NCT09876543"},
            {"molecule": "Pembrolizumab", "indication": "Non-Small Cell Lung Cancer", "phase": "Phase III", "sponsor": "Merck", "nct_id": "NCT04123456"},
        ]
    if not data["competitors"]:
        data["competitors"] = [
            {"molecule": "Paracetamol (Dolo 650)", "competitor": "GSK", "strategy": "Maintain OTC dominance; limited differentiation", "likelihood": "Medium", "impact": "Moderate"},
            {"molecule": "Sitagliptin", "competitor": "Sun Pharma", "strategy": "Launch generic at discount post-expiry", "likelihood": "High", "impact": "High"},
            {"molecule": "Pembrolizumab", "competitor": "Roche", "strategy": "Accelerate SC IO competitor", "likelihood": "Medium", "impact": "High"},
        ]
    if not data["social"]:
        data["social"] = [
            {"molecule": "Paracetamol", "sentiment": 0.1, "source": "Forum", "complaint": "Dosing clarity", "post": "Confused about dose frequency for fever."},
            {"molecule": "Sitagliptin", "sentiment": -0.2, "source": "Reddit", "complaint": "Cost", "post": "Co-pays are high; considering switching."},
            {"molecule": "Pembrolizumab", "sentiment": 0.3, "source": "Patient group", "complaint": "Fatigue", "post": "Fatigue manageable but worth the benefit."},
        ]
    
    return data


def get_molecule_profile(molecule: str, data: dict) -> dict:
    """Get comprehensive profile for a molecule."""
    profile = {
        "molecule": molecule,
        "market": None,
        "patents": [],
        "trials": [],
        "competitors": [],
        "sentiment": {"avg": 0, "count": 0, "complaints": []}
    }
    
    # Market data
    for m in data["market"]:
        if m["molecule"].lower() == molecule.lower():
            profile["market"] = m
            break
    
    # Patents
    profile["patents"] = [p for p in data["patents"] if p["molecule"].lower() == molecule.lower()]
    
    # Trials
    profile["trials"] = [t for t in data["trials"] if t["molecule"].lower() == molecule.lower()]
    
    # Competitors
    profile["competitors"] = [c for c in data["competitors"] if c["molecule"].lower() == molecule.lower()]
    
    # Sentiment
    sentiments = [s for s in data["social"] if s["molecule"].lower() == molecule.lower()]
    if sentiments:
        profile["sentiment"]["avg"] = sum(s["sentiment"] for s in sentiments) / len(sentiments)
        profile["sentiment"]["count"] = len(sentiments)
        profile["sentiment"]["complaints"] = list(set(s["complaint"] for s in sentiments if s["complaint"]))
    
    return profile


def render_molecule_card(profile: dict, col):
    """Render a molecule profile card."""
    with col:
        st.markdown(f"### 💊 {profile['molecule']}")
        
        if profile["market"]:
            m = profile["market"]
            st.markdown("#### Market Overview")
            
            metric_cols = st.columns(2)
            with metric_cols[0]:
                st.metric("Market Size", f"${m['market_size_usd_mn']}M")
                st.metric("Competition", m.get("competition_level", m.get("generic_penetration", "N/A")))
            with metric_cols[1]:
                st.metric("CAGR", f"{m['cagr_percent']}%")
                st.metric("Patient Burden", m.get("patient_burden", "N/A"))
            
            st.caption(f"**Region:** {m['region']} | **Therapy:** {m['therapy_area']}")
        else:
            st.warning("No market data available")
        
        st.markdown("---")
        
        # Patents
        st.markdown("#### 📜 Patents")
        if profile["patents"]:
            for p in profile["patents"]:
                status_color = "🟢" if p["status"] == "Active" else "🔴"
                st.caption(f"{status_color} **{p['patent_number']}** - {p['type']} (Expires: {p['expiry_date']})")
        else:
            st.caption("No patent data")
        
        st.markdown("---")
        
        # Clinical Trials
        st.markdown("#### 🔬 Clinical Trials")
        if profile["trials"]:
            for t in profile["trials"]:
                st.caption(f"**{t['phase']}** - {t['indication']} ({t['nct_id']})")
        else:
            st.caption("No active trials")
        
        st.markdown("---")
        
        # Competitor Intel
        st.markdown("#### ⚔️ Competitive Threats")
        if profile["competitors"]:
            for c in profile["competitors"]:
                likelihood_emoji = "🔴" if c["likelihood"] == "High" else "🟡" if c["likelihood"] == "Medium" else "🟢"
                st.caption(f"{likelihood_emoji} **{c['competitor']}**: {c['strategy'][:80]}...")
        else:
            st.caption("No competitive intelligence")
        
        st.markdown("---")
        
        # Sentiment
        st.markdown("#### 💬 Patient Sentiment")
        sentiment = profile["sentiment"]
        if sentiment["count"] > 0:
            avg = sentiment["avg"]
            emoji = "😊" if avg > 0.3 else "😐" if avg > -0.3 else "😟"
            st.metric(f"{emoji} Sentiment Score", f"{avg:.2f}", f"({sentiment['count']} mentions)")
            if sentiment["complaints"]:
                st.caption(f"**Top complaints:** {', '.join(sentiment['complaints'][:3])}")
        else:
            st.caption("No patient feedback data")


def main():
    st.markdown("# ⚖️ Molecule Comparison")
    st.markdown("Compare molecules side-by-side across all dimensions")
    
    # Load data
    data = load_all_data()
    
    # Get unique molecules
    all_molecules = set()
    for m in data["market"]:
        all_molecules.add(m["molecule"])
    for p in data["patents"]:
        all_molecules.add(p["molecule"])
    
    molecules = sorted(list(all_molecules))
    
    if not molecules:
        st.warning("No molecules found in database. Please seed the database first.")
        return
    
    # Selection
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        mol1 = st.selectbox("Select First Molecule", molecules, index=0)
    with col2:
        default_idx = 1 if len(molecules) > 1 else 0
        mol2 = st.selectbox("Select Second Molecule", molecules, index=default_idx)
    
    st.markdown("---")
    
    # Get profiles
    profile1 = get_molecule_profile(mol1, data)
    profile2 = get_molecule_profile(mol2, data)
    
    # Render comparison
    col1, col2 = st.columns(2)
    render_molecule_card(profile1, col1)
    render_molecule_card(profile2, col2)
    
    # Comparison Chart
    st.markdown("---")
    st.markdown("### 📊 Visual Comparison")
    
    try:
        from src.services.analytics import ChartService
        fig = ChartService.molecule_comparison([mol1, mol2], data["market"])
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not generate comparison chart: {e}")
    
    # Summary Table
    st.markdown("---")
    st.markdown("### 📋 Comparison Summary")
    
    summary_data = []
    for profile in [profile1, profile2]:
        m = profile["market"] or {}
        row = {
            "Molecule": profile["molecule"],
            "Market Size": f"${m.get('market_size_usd_mn', 'N/A')}M" if m.get('market_size_usd_mn') else "N/A",
            "CAGR": f"{m.get('cagr_percent', 'N/A')}%" if m.get('cagr_percent') else "N/A",
            "Competition": m.get("competition_level", m.get("generic_penetration", "N/A")),
            "Patient Burden": m.get("patient_burden", "N/A"),
            "Active Patents": sum(1 for p in profile["patents"] if p["status"] == "Active"),
            "Clinical Trials": len(profile["trials"]),
            "Competitors": len(profile["competitors"]),
            "Sentiment": f"{profile['sentiment']['avg']:.2f}" if profile['sentiment']['count'] > 0 else "N/A"
        }
        summary_data.append(row)
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df.set_index("Molecule").T, use_container_width=True)
    
    # Recommendation
    st.markdown("---")
    st.markdown("### 💡 AI Recommendation")
    
    # Simple heuristic recommendation
    if profile1["market"] and profile2["market"]:
        m1, m2 = profile1["market"], profile2["market"]
        
        score1 = m1.get("cagr_percent", 0) * 2
        score2 = m2.get("cagr_percent", 0) * 2
        
        # Prefer low competition
        comp_bonus = {"Low": 20, "Medium": 10, "High": 0}
        score1 += comp_bonus.get(m1.get("competition_level", m1.get("generic_penetration", "Medium")), 10)
        score2 += comp_bonus.get(m2.get("competition_level", m2.get("generic_penetration", "Medium")), 10)
        
        # Prefer high patient burden (more need)
        burden_bonus = {"Very High": 20, "High": 15, "Medium": 10, "Low": 5}
        score1 += burden_bonus.get(m1.get("patient_burden", "Medium"), 10)
        score2 += burden_bonus.get(m2.get("patient_burden", "Medium"), 10)
        
        winner = mol1 if score1 > score2 else mol2
        loser = mol2 if score1 > score2 else mol1
        
        st.success(f"""
        **Recommended Focus: {winner}**
        
        Based on the analysis, **{winner}** presents a more attractive opportunity due to:
        - {"Higher growth rate (CAGR)" if (m1 if winner == mol1 else m2)["cagr_percent"] > (m2 if winner == mol1 else m1)["cagr_percent"] else "More favorable market conditions"}
        - {"Lower competition" if comp_bonus.get((m1 if winner == mol1 else m2).get("competition_level", ""), 0) > comp_bonus.get((m2 if winner == mol1 else m1).get("competition_level", ""), 0) else "Significant market presence"}
        - {"Higher unmet patient need" if burden_bonus.get((m1 if winner == mol1 else m2).get("patient_burden", ""), 0) > burden_bonus.get((m2 if winner == mol1 else m1).get("patient_burden", ""), 0) else "Established patient base"}
        
        *Note: This is a simplified analysis. Consult with strategy teams for detailed recommendations.*
        """)
    else:
        st.info("Select molecules with market data to see AI recommendations.")
    
    # Footer
    st.markdown("---")
    st.caption(f"Comparison generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Pharma Agentic AI")


if __name__ == "__main__":
    main()
