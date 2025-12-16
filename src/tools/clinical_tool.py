"""
Clinical Trials Tool
Queries database for clinical trials and pipeline analysis.
"""
import json
from typing import Optional
from crewai.tools import tool
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def _extract_entity_from_query(query: str, entity_type: str = "indication") -> str:
    """Extract entities from natural language query."""
    if not query:
        return None
    
    query_lower = query.lower()
    
    if entity_type == "indication":
        indications = {
            "copd": ["copd", "chronic obstructive"],
            "asthma": ["asthma", "asthmatic"],
            "ipf": ["ipf", "idiopathic pulmonary fibrosis", "pulmonary fibrosis"],
            "nsclc": ["nsclc", "non-small cell lung cancer", "lung cancer"],
            "melanoma": ["melanoma", "skin cancer"],
            "diabetes": ["diabetes", "diabetic", "t2dm", "type 2 diabetes"],
            "rheumatoid arthritis": ["rheumatoid", "ra", "arthritis"]
        }
        for indication, keywords in indications.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return indication.upper() if indication in ["copd", "ipf", "nsclc"] else indication.title()
    
    elif entity_type == "therapy_area":
        areas = {
            "respiratory": ["respiratory", "lung", "copd", "asthma", "pulmonary"],
            "oncology": ["oncology", "cancer", "tumor", "nsclc", "melanoma"],
            "diabetes": ["diabetes", "diabetic", "glucose"],
            "immunology": ["immune", "autoimmune", "rheumatoid"]
        }
        for area, keywords in areas.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return area.capitalize()
    
    elif entity_type == "molecule":
        # Brand name mappings
        brand_to_molecule = {
            "dolo": "Paracetamol", "dolo650": "Paracetamol",
            "ozempic": "Semaglutide", "wegovy": "Semaglutide",
            "humira": "Adalimumab", "keytruda": "Pembrolizumab",
            "herceptin": "Trastuzumab", "revlimid": "Lenalidomide"
        }
        for brand, mol in brand_to_molecule.items():
            if brand in query_lower:
                return mol
        
        known_molecules = [
            "pembrolizumab", "sitagliptin", "rivaroxaban", "pirfenidone",
            "roflumilast", "tiotropium", "omalizumab", "fluticasone",
            "semaglutide", "adalimumab", "trastuzumab", "lenalidomide",
            "paracetamol", "azithromycin", "pantoprazole", "escitalopram",
            "metformin", "atorvastatin", "amlodipine", "montelukast"
        ]
        for mol in known_molecules:
            if mol in query_lower:
                return mol.capitalize()
    
    return None


def _query_database(indication: str = None, therapy_area: str = None, molecule: str = None):
    """Query clinical trials from database."""
    try:
        from src.database.db import get_db_session
        from src.database.models import ClinicalTrial
        
        with get_db_session() as session:
            query = session.query(ClinicalTrial)
            
            if indication:
                query = query.filter(ClinicalTrial.indication.ilike(f"%{indication}%"))
            if therapy_area:
                query = query.filter(ClinicalTrial.therapy_area.ilike(f"%{therapy_area}%"))
            if molecule:
                query = query.filter(ClinicalTrial.drug_name.ilike(f"%{molecule}%"))
            
            results = query.all()
            
            if not results:
                return None
            
            # Group by indication
            grouped = {}
            for r in results:
                ind = r.indication
                if ind not in grouped:
                    grouped[ind] = {
                        "indication": ind,
                        "therapy_area": r.therapy_area,
                        "competition_density": r.competition_density or "Medium",
                        "unmet_need": r.unmet_need or "Medium",
                        "patient_burden_score": r.patient_burden_score or "N/A",
                        "active_trials": []
                    }
                grouped[ind]["active_trials"].append({
                    "phase": r.phase,
                    "drug_name": r.drug_name,
                    "sponsor": r.sponsor,
                    "nct_id": r.nct_id
                })
            
            return list(grouped.values())
    except Exception as e:
        print(f"Database query error: {e}")
        return None


def _load_clinical_data() -> list:
    """Load clinical trials from database, fallback to JSON."""
    db_data = _query_database()
    if db_data:
        return db_data
    
    # Fallback to JSON file
    data_path = Path(__file__).resolve().parent.parent.parent / "mock_data" / "clinical_trials.json"
    if data_path.exists():
        with open(data_path, "r") as f:
            return json.load(f)
    return []


def _fetch_from_clinicaltrials_api(drug_name: str = None, indication: str = None) -> list:
    """
    Fetch clinical trials from ClinicalTrials.gov API.
    Falls back to this when database has no results.
    """
    try:
        from src.services.external_apis import fetch_clinical_trials
        
        trials = fetch_clinical_trials(drug_name=drug_name, indication=indication, limit=15)
        
        if not trials:
            return None
        
        # Group by indication
        grouped = {}
        for trial in trials:
            ind = trial.indication
            if ind not in grouped:
                grouped[ind] = {
                    "indication": ind,
                    "therapy_area": "External Data",
                    "competition_density": "Unknown",
                    "unmet_need": "Unknown",
                    "patient_burden_score": "N/A",
                    "active_trials": [],
                    "source": "clinicaltrials.gov"
                }
            grouped[ind]["active_trials"].append({
                "phase": trial.phase,
                "drug_name": trial.drug_name,
                "sponsor": trial.sponsor or "Unknown",
                "nct_id": trial.nct_id,
                "status": trial.status,
                "title": trial.title
            })
        
        return list(grouped.values())
        
    except Exception as e:
        print(f"ClinicalTrials.gov API error: {e}")
        return None


@tool("Query Clinical Trials")
def query_clinical_trials(indication: Optional[str] = None, molecule: Optional[str] = None, therapy_area: Optional[str] = None, query: Optional[str] = None) -> str:
    """
    Query active clinical trials by indication, molecule, or therapy area.
    
    Args:
        indication: Disease/condition to search (e.g., 'COPD', 'NSCLC', 'Diabetes')
        molecule: Drug name to search for in trials
        therapy_area: Therapeutic area (e.g., 'Respiratory', 'Oncology')
        query: Natural language query to extract parameters from
    
    Returns:
        List of active clinical trials with phase, sponsor, and competition density.
    """
    try:
        # Extract from query if parameters not provided
        if query:
            if not indication:
                indication = _extract_entity_from_query(query, "indication")
            if not therapy_area:
                therapy_area = _extract_entity_from_query(query, "therapy_area")
            if not molecule:
                molecule = _extract_entity_from_query(query, "molecule")
        
        # Avoid duplicate filtering - if both extracted to same value, clear one
        if indication and therapy_area and indication.lower() == therapy_area.lower():
            therapy_area = None  # Prefer indication over therapy_area
        
        # Try database first
        db_results = _query_database(indication, therapy_area, molecule)
        data = db_results if db_results else _load_clinical_data()
        
        results = []
        
        for entry in data:
            # Filter by indication (with null safety)
            entry_indication = entry.get("indication") or ""
            if indication and indication.lower() not in entry_indication.lower():
                continue
            # Filter by therapy area (with null safety)
            entry_therapy = entry.get("therapy_area") or ""
            if therapy_area and therapy_area.lower() not in entry_therapy.lower():
                continue
            # Filter by molecule (check in trials)
            if molecule:
                molecule_found = False
                for trial in entry.get("active_trials", []):
                    drug_name = trial.get("drug_name") or ""
                    if molecule.lower() in drug_name.lower():
                        molecule_found = True
                        break
                if not molecule_found:
                    continue
            
            results.append(entry)
        
        if not results:
            # Try external API as last resort
            search_term = molecule or indication
            if search_term:
                external_data = _fetch_from_clinicaltrials_api(drug_name=molecule, indication=indication)
                if external_data:
                    output = [f"**Clinical Trials from ClinicalTrials.gov** *(Real-time data)*\n"]
                    for r in external_data:
                        trials = r.get("active_trials", [])
                        trial_info = f"**{r['indication']}**\n"
                        trial_info += f"  Active Trials: {len(trials)}\n"
                        
                        for trial in trials[:5]:  # Limit to 5 per indication
                            status = trial.get("status", "Unknown")
                            trial_info += f"    - [{trial['phase']}] {trial['drug_name']} ({status})\n"
                            trial_info += f"      Sponsor: {trial['sponsor']} | NCT: {trial['nct_id']}\n"
                        
                        output.append(trial_info)
                    
                    output.append("\n---\n*Data fetched in real-time from ClinicalTrials.gov*")
                    return "\n".join(output)
            
            filters = []
            if indication:
                filters.append(f"indication='{indication}'")
            if molecule:
                filters.append(f"molecule='{molecule}'")
            if therapy_area:
                filters.append(f"therapy_area='{therapy_area}'")
            filter_str = ", ".join(filters) if filters else "the specified criteria"
            return f"No clinical trials found for {filter_str}. Try: COPD, Asthma, IPF, NSCLC, Melanoma, Diabetes."
        
        output = []
        for r in results:
            trials = r.get("active_trials", [])
            competition = r.get("competition_density", "Unknown")
            unmet_need = r.get("unmet_need", "Unknown")
            burden = r.get("patient_burden_score", "N/A")
            
            trial_info = f"**{r['indication']}** ({r.get('therapy_area', 'N/A')})\n"
            trial_info += f"  Competition Density: {competition} | Unmet Need: {unmet_need} | Patient Burden: {burden}\n"
            trial_info += f"  Active Trials: {len(trials)}\n"
            
            for trial in trials:
                trial_info += f"    - [{trial['phase']}] {trial['drug_name']} (Sponsor: {trial['sponsor']}) - {trial['nct_id']}\n"
            
            output.append(trial_info)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error querying clinical trials: {str(e)}"


@tool("Find Repurposing Opportunities")
def find_repurposing_opportunities(molecule: str = None, query: Optional[str] = None) -> str:
    """
    Find potential repurposing opportunities for a molecule by identifying new indications in trials.
    
    Args:
        molecule: Name of the molecule to find repurposing opportunities for.
        query: Natural language query to extract molecule from.
    
    Returns:
        List of new indications where the molecule is being tested.
    """
    try:
        if not molecule and query:
            molecule = _extract_entity_from_query(query, "molecule")
        
        if not molecule:
            molecule = query or "unspecified molecule"
        
        data = _load_clinical_data()
        opportunities = []
        
        for entry in data:
            for trial in entry.get("active_trials", []):
                if molecule.lower() in trial.get("drug_name", "").lower():
                    opportunities.append({
                        "indication": entry["indication"],
                        "therapy_area": entry.get("therapy_area", "N/A"),
                        "phase": trial["phase"],
                        "sponsor": trial["sponsor"],
                        "nct_id": trial["nct_id"],
                        "competition": entry.get("competition_density", "Unknown"),
                        "unmet_need": entry.get("unmet_need", "Unknown")
                    })
        
        if not opportunities:
            return f"No repurposing opportunities found for {molecule} in clinical trials."
        
        output = [f"**Repurposing Opportunities for {molecule}:**\n"]
        
        # Sort by phase (later phases = more advanced)
        phase_order = {"Phase IV": 0, "Phase III": 1, "Phase II": 2, "Phase I": 3}
        opportunities.sort(key=lambda x: phase_order.get(x["phase"], 4))
        
        for opp in opportunities:
            potential = "HIGH" if opp["phase"] in ["Phase III", "Phase IV"] and opp["competition"] == "Low" else "MEDIUM"
            
            output.append(
                f"- **{opp['indication']}** ({opp['therapy_area']})\n"
                f"  Phase: {opp['phase']} | Sponsor: {opp['sponsor']}\n"
                f"  Competition: {opp['competition']} | Unmet Need: {opp['unmet_need']}\n"
                f"  **Repurposing Potential: {potential}**\n"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error finding repurposing opportunities: {str(e)}"


@tool("Analyze Competition Density")
def analyze_competition_density(indication: str) -> str:
    """
    Analyze the competition density for a specific indication.
    
    Args:
        indication: Disease indication to analyze (e.g., 'COPD', 'Asthma', 'NSCLC')
    
    Returns:
        Competition analysis with trial counts and recommendations.
    """
    try:
        data = _load_clinical_data()
        
        result = None
        for entry in data:
            if indication.lower() in entry.get("indication", "").lower():
                result = entry
                break
        
        if not result:
            return f"No data found for indication: {indication}"
        
        trials = result.get("active_trials", [])
        competition = result.get("competition_density", "Unknown")
        unmet_need = result.get("unmet_need", "Unknown")
        burden = result.get("patient_burden_score", "N/A")
        
        # Count trials by phase
        phase_counts = {}
        sponsors = set()
        for trial in trials:
            phase = trial["phase"]
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
            sponsors.add(trial["sponsor"])
        
        output = (
            f"**Competition Analysis for {result['indication']}:**\n\n"
            f"**Overall Competition:** {competition}\n"
            f"**Unmet Need:** {unmet_need}\n"
            f"**Patient Burden Score:** {burden}/10\n\n"
            f"**Trial Landscape:**\n"
            f"  - Total Active Trials: {len(trials)}\n"
            f"  - Unique Sponsors: {len(sponsors)}\n"
        )
        
        for phase, count in sorted(phase_counts.items()):
            output += f"  - {phase}: {count} trial(s)\n"
        
        # Recommendation
        output += "\n**Strategic Recommendation:**\n"
        if competition == "Low" and unmet_need in ["High", "Very High"]:
            output += "  ✅ **HIGH OPPORTUNITY** - Low competition with significant unmet need\n"
        elif competition == "Low":
            output += "  ✅ Favorable competitive landscape for entry\n"
        elif competition == "High":
            output += "  ⚠️ Crowded space - differentiation required\n"
        else:
            output += "  ℹ️ Moderate competition - targeted strategy needed\n"
        
        return output
    
    except Exception as e:
        return f"Error analyzing competition: {str(e)}"
