"""
IQVIA Market Data Tool
Queries market data from database for molecule/region analysis.
"""
import json
from typing import Optional, List
from crewai.tools import tool
from pathlib import Path


def _extract_entity_from_query(query: str, entity_type: str = "molecule") -> str:
    """Extract entities from a natural language query."""
    if not query:
        return None
    
    query_lower = query.lower()
    
    if entity_type == "therapy_area":
        therapy_areas = {
            "respiratory": ["respiratory", "copd", "asthma", "lung", "pulmonary", "inhaler"],
            "oncology": ["oncology", "cancer", "tumor", "carcinoma", "melanoma", "leukemia"],
            "diabetes": ["diabetes", "diabetic", "glucose", "insulin", "metformin", "gliptin", "obesity", "weight"],
            "cardiovascular": ["cardiac", "cardio", "heart", "cardiovascular", "hypertension", "blood pressure", "cholesterol"],
            "cns": ["neuro", "brain", "alzheimer", "parkinson", "epilepsy", "depression", "anxiety", "mental", "psychiatric"],
            "autoimmune": ["immune", "autoimmune", "rheumatoid", "psoriasis", "crohn", "arthritis"],
            "analgesic": ["pain", "analgesic", "fever", "headache", "paracetamol", "dolo"],
            "gastrointestinal": ["gerd", "acid", "reflux", "gastro", "ulcer", "gi", "stomach"],
            "anti-infective": ["antibiotic", "infection", "bacterial", "azithromycin"]
        }
        
        for area, keywords in therapy_areas.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return area.capitalize() if area not in ["cns", "gi"] else area.upper()
        return None
    
    elif entity_type == "region":
        regions = {
            "india": ["india", "indian"],
            "us": ["us", "usa", "united states", "america"],
            "europe": ["europe", "eu", "european"],
            "global": ["global", "worldwide", "world"]
        }
        
        for region, keywords in regions.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return region.upper() if region == "us" else region.capitalize()
        return None
    
    elif entity_type == "molecule":
        known_molecules = [
            "pembrolizumab", "sitagliptin", "rivaroxaban", "pirfenidone",
            "roflumilast", "tiotropium", "omalizumab", "fluticasone",
            "paracetamol", "azithromycin", "pantoprazole", "atorvastatin",
            "metformin", "semaglutide", "adalimumab", "escitalopram",
            "montelukast", "trastuzumab", "lenalidomide", "amlodipine"
        ]
        
        # Also check brand names
        brand_to_molecule = {
            "dolo": "Paracetamol", "dolo650": "Paracetamol", "dolo 650": "Paracetamol",
            "calpol": "Paracetamol", "crocin": "Paracetamol", "tylenol": "Paracetamol",
            "januvia": "Sitagliptin", "xarelto": "Rivaroxaban",
            "keytruda": "Pembrolizumab", "opdivo": "Nivolumab",
            "ozempic": "Semaglutide", "wegovy": "Semaglutide",
            "humira": "Adalimumab", "pan": "Pantoprazole", "pan40": "Pantoprazole", "pan 40": "Pantoprazole",
            "lipitor": "Atorvastatin", "azithral": "Azithromycin",
            "nexito": "Escitalopram", "lexapro": "Escitalopram",
            "herceptin": "Trastuzumab", "revlimid": "Lenalidomide",
            "norvasc": "Amlodipine", "singulair": "Montelukast", "montair": "Montelukast"
        }
        
        for brand, mol in brand_to_molecule.items():
            if brand in query_lower:
                return mol
        
        for mol in known_molecules:
            if mol in query_lower:
                return mol.capitalize()
    
    return None


def _load_iqvia_data() -> list:
    """Load IQVIA market data from JSON file, with optional DB merge."""
    all_data = []
    
    # First try database
    try:
        from ..database.db import get_db_session
        from ..database.models import MarketData
        
        with get_db_session() as db:
            records = db.query(MarketData).all()
            if records:
                for r in records:
                    all_data.append({
                        "molecule": r.molecule,
                        "region": r.region,
                        "therapy_area": r.therapy_area,
                        "indication": r.indication,
                        "market_size_usd_mn": r.market_size_usd_mn,
                        "cagr_percent": r.cagr_percent,
                        "top_competitors": r.top_competitors or [],
                        "generic_penetration": r.generic_penetration,
                        "patient_burden": r.patient_burden,
                        "competition_level": r.competition_level
                    })
    except Exception:
        pass
    
    # Always also load JSON file and merge (JSON has more data)
    data_path = Path(__file__).resolve().parent.parent.parent / "mock_data" / "iqvia_market_data.json"
    if data_path.exists():
        with open(data_path, "r") as f:
            json_data = json.load(f)
            # Add JSON entries that aren't already in DB data
            existing_molecules = {d.get("molecule", "").lower() for d in all_data}
            for entry in json_data:
                if entry.get("molecule", "").lower() not in existing_molecules:
                    all_data.append(entry)
    
    return all_data


@tool("Query IQVIA Market Data")
def query_iqvia_market(molecule: Optional[str] = None, region: Optional[str] = None, therapy_area: Optional[str] = None, query: Optional[str] = None) -> str:
    """
    Query IQVIA market data for pharmaceutical market intelligence.
    
    Args:
        molecule: Name of the molecule/drug to search for.
        region: Geographic region to filter by.
        therapy_area: Therapeutic area to filter by.
        query: Natural language query to extract parameters from.
    
    Returns:
        Market data including market size, CAGR, competitors, and generic penetration.
    """
    try:
        # Extract from query if parameters not provided
        if query:
            if not molecule:
                molecule = _extract_entity_from_query(query, "molecule")
            if not region:
                region = _extract_entity_from_query(query, "region")
            if not therapy_area:
                therapy_area = _extract_entity_from_query(query, "therapy_area")
        
        data = _load_iqvia_data()
        results = []
        
        for entry in data:
            # Filter by molecule if provided
            if molecule and molecule.lower() not in entry.get("molecule", "").lower():
                continue
            # Filter by region if provided
            if region and region.lower() not in entry.get("region", "").lower():
                continue
            # Filter by therapy area if provided
            if therapy_area and therapy_area.lower() not in entry.get("therapy_area", "").lower():
                continue
            results.append(entry)
        
        if not results:
            filters = []
            if molecule:
                filters.append(f"molecule='{molecule}'")
            if region:
                filters.append(f"region='{region}'")
            if therapy_area:
                filters.append(f"therapy_area='{therapy_area}'")
            
            filter_str = ", ".join(filters) if filters else "the specified criteria"
            return f"No market data found for {filter_str}. Try different search terms or check available data in the database."
        
        # Format results
        output = []
        for r in results:
            output.append(
                f"**{r['molecule']}** ({r['region']}):\n"
                f"  - Therapy Area: {r.get('therapy_area', 'N/A')}\n"
                f"  - Market Size: ${r['market_size_usd_mn']}M USD\n"
                f"  - CAGR: {r['cagr_percent']}%\n"
                f"  - Top Competitors: {', '.join(r['top_competitors'])}\n"
                f"  - Generic Penetration: {r['generic_penetration']}\n"
                f"  - Patient Burden: {r.get('patient_burden', 'N/A')}\n"
                f"  - Competition Level: {r.get('competition_level', 'N/A')}"
            )
        
        return "\n\n".join(output)
    
    except Exception as e:
        return f"Error querying market data: {str(e)}"


@tool("Find Low Competition Markets")
def find_low_competition_markets(therapy_area: Optional[str] = None, region: Optional[str] = None, query: Optional[str] = None) -> str:
    """
    Find markets with low competition and high patient burden - ideal for whitespace analysis.
    
    Args:
        therapy_area: Therapeutic area to analyze.
        region: Geographic region to filter.
        query: Natural language query to extract parameters from.
    
    Returns:
        List of molecules with low competition and high patient burden.
    """
    try:
        # Extract from query if parameters not provided
        if query:
            if not therapy_area:
                therapy_area = _extract_entity_from_query(query, "therapy_area")
            if not region:
                region = _extract_entity_from_query(query, "region")
        
        # Default values if still not found
        if not therapy_area:
            therapy_area = "Respiratory"  # Just for getting results, not hardcoded output
        if not region:
            region = "India"
        
        data = _load_iqvia_data()
        opportunities = []
        
        for entry in data:
            # Check therapy area match
            if therapy_area.lower() not in entry.get("therapy_area", "").lower():
                continue
            # Check region match
            if region.lower() not in entry.get("region", "").lower():
                continue
            # Check for low competition
            competition = entry.get("competition_level", entry.get("generic_penetration", ""))
            if competition.lower() in ["low", "medium"]:
                opportunities.append({
                    "molecule": entry["molecule"],
                    "indication": entry.get("indication", entry.get("therapy_area")),
                    "market_size": entry["market_size_usd_mn"],
                    "cagr": entry["cagr_percent"],
                    "competition": competition,
                    "patient_burden": entry.get("patient_burden", "N/A")
                })
        
        if not opportunities:
            return f"No low competition opportunities found in {therapy_area} for {region}. Try different therapy areas like: Respiratory, Oncology, Diabetes, Cardiology."
        
        # Sort by CAGR (highest first)
        opportunities.sort(key=lambda x: x["cagr"], reverse=True)
        
        output = [f"**Whitespace Opportunities in {therapy_area} ({region}):**\n"]
        for opp in opportunities:
            output.append(
                f"- **{opp['molecule']}** ({opp['indication']})\n"
                f"  Market: ${opp['market_size']}M | CAGR: {opp['cagr']}% | "
                f"Competition: {opp['competition']} | Patient Burden: {opp['patient_burden']}"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error finding opportunities: {str(e)}"
