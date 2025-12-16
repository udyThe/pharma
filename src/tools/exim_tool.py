"""
EXIM Trade Data Tool
Queries database for import/export supply chain analysis.
"""
import json
from crewai.tools import tool
from pathlib import Path
from typing import Optional
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def _extract_molecule_from_query(query: str) -> str:
    """Extract molecule name from natural language query."""
    if not query:
        return None
    
    query_lower = query.lower()
    
    # Check brand names first
    brand_to_molecule = {
        "dolo": "Paracetamol", "dolo650": "Paracetamol", "dolo 650": "Paracetamol",
        "calpol": "Paracetamol", "tylenol": "Paracetamol",
        "ozempic": "Semaglutide", "wegovy": "Semaglutide",
        "humira": "Adalimumab", "pan40": "Pantoprazole", "pan 40": "Pantoprazole",
        "azithral": "Azithromycin", "xarelto": "Rivaroxaban"
    }
    for brand, mol in brand_to_molecule.items():
        if brand in query_lower:
            return mol
    
    known_molecules = [
        "sitagliptin", "rivaroxaban", "pirfenidone", "roflumilast",
        "metformin", "atorvastatin", "omeprazole", "amlodipine",
        "paracetamol", "azithromycin", "pantoprazole", "semaglutide",
        "adalimumab", "escitalopram", "montelukast", "trastuzumab",
        "lenalidomide", "pembrolizumab", "tiotropium", "fluticasone", "omalizumab"
    ]
    
    for mol in known_molecules:
        if mol in query_lower:
            return mol.capitalize()
    
    # Try drug name suffixes
    words = query.replace(",", " ").replace(".", " ").split()
    drug_suffixes = ["mab", "nib", "lib", "vir", "stat", "pril", "olol", 
                     "sartan", "pine", "azole", "mycin", "cillin", "done",
                     "prazole", "gliptin", "formin", "xaban"]
    
    for word in words:
        word_clean = word.lower().strip()
        for suffix in drug_suffixes:
            if word_clean.endswith(suffix) and len(word_clean) > len(suffix) + 2:
                return word_clean.capitalize()
    
    return None


def _query_database(molecule: str = None):
    """Query trade data from database."""
    try:
        from src.database.db import get_db_session
        from src.database.models import TradeData
        
        with get_db_session() as session:
            query = session.query(TradeData)
            
            if molecule:
                query = query.filter(TradeData.molecule.ilike(f"%{molecule}%"))
            
            results = query.all()
            
            if not results:
                return None
            
            return [{
                "molecule": r.molecule,
                "total_import_volume_kg": r.total_import_volume_kg or 0,
                "average_price_per_kg": r.average_price_per_kg or 0,
                "major_source_countries": r.major_source_countries if r.major_source_countries else []
            } for r in results]
    except Exception as e:
        print(f"Database query error: {e}")
        return None


def _load_exim_data() -> list:
    """Load EXIM data from database, fallback to JSON."""
    db_data = _query_database()
    if db_data:
        return db_data
    
    data_path = Path(__file__).resolve().parent.parent.parent / "mock_data" / "exim_trade_data.json"
    if data_path.exists():
        with open(data_path, "r") as f:
            return json.load(f)
    return []


@tool("Query EXIM Trade Data")
def query_exim_trade(molecule: str = None, query: Optional[str] = None) -> str:
    """
    Query import/export trade data for a pharmaceutical molecule.
    
    Args:
        molecule: Name of the molecule/API to search for trade data.
        query: Natural language query to extract molecule from.
    
    Returns:
        Trade data including import volumes, source countries, and pricing.
    """
    try:
        # Extract from query if not provided
        if not molecule and query:
            molecule = _extract_molecule_from_query(query)
        
        if not molecule:
            molecule = query or "unspecified molecule"
        
        # Try database first
        db_data = _query_database(molecule)
        data = db_data if db_data else _load_exim_data()
        
        result = None
        for entry in data:
            if molecule.lower() in entry.get("molecule", "").lower():
                result = entry
                break
        
        if not result:
            return f"No EXIM trade data found for molecule: {molecule}. This API may not be in our database."
        
        # Calculate total value
        total_value = result["total_import_volume_kg"] * result["average_price_per_kg"]
        
        output = (
            f"**EXIM Trade Data for {result['molecule']}:**\n\n"
            f"📦 **Import Volume:** {result['total_import_volume_kg']:,} kg\n"
            f"💰 **Average Price:** ${result['average_price_per_kg']:,.2f}/kg\n"
            f"💵 **Estimated Total Value:** ${total_value:,.0f}\n\n"
            f"🌍 **Major Source Countries:**\n"
        )
        
        for country in result["major_source_countries"]:
            output += f"  - {country}\n"
        
        # Add supply chain insights
        if result["average_price_per_kg"] > 10000:
            output += "\n⚠️ **High-value API** - Likely biologic or specialty drug"
        elif result["average_price_per_kg"] < 500:
            output += "\n✅ **Commodity API** - Multiple suppliers available"
        
        return output
    
    except Exception as e:
        return f"Error querying EXIM data: {str(e)}"


@tool("Analyze Supply Chain")
def analyze_supply_chain(molecule: str = None, query: Optional[str] = None) -> str:
    """
    Analyze supply chain concentration and pricing for a molecule.
    
    Args:
        molecule: Name of the molecule to analyze.
        query: Natural language query to extract molecule from.
    
    Returns:
        Supply chain risk assessment and sourcing recommendations.
    """
    try:
        if not molecule and query:
            molecule = _extract_molecule_from_query(query)
        
        if not molecule:
            molecule = query or "unspecified molecule"
        
        db_data = _query_database(molecule)
        data = db_data if db_data else _load_exim_data()
        
        result = None
        for entry in data:
            if molecule.lower() in entry.get("molecule", "").lower():
                result = entry
                break
        
        if not result:
            return f"No supply chain data found for: {molecule}"
        
        countries = result["major_source_countries"]
        price = result["average_price_per_kg"]
        volume = result["total_import_volume_kg"]
        
        # Assess concentration risk
        if len(countries) == 1:
            concentration_risk = "HIGH"
            risk_desc = "Single source country - significant supply risk"
        elif len(countries) == 2:
            concentration_risk = "MEDIUM"
            risk_desc = "Limited diversification - moderate supply risk"
        else:
            concentration_risk = "LOW"
            risk_desc = "Multiple source countries - diversified supply"
        
        # China dependency check
        china_dependent = "China" in countries
        
        output = (
            f"**Supply Chain Analysis for {result['molecule']}:**\n\n"
            f"**Concentration Risk:** {concentration_risk}\n"
            f"  {risk_desc}\n\n"
            f"**Source Countries:** {', '.join(countries)}\n"
        )
        
        if china_dependent:
            output += "⚠️ **China Dependency Alert:** Consider alternate sourcing\n"
        
        output += (
            f"\n**Pricing Analysis:**\n"
            f"  - Current Price: ${price:,.2f}/kg\n"
            f"  - Annual Import Value: ${price * volume:,.0f}\n"
        )
        
        # Recommendations
        output += "\n**Recommendations:**\n"
        if concentration_risk == "HIGH":
            output += "  - Qualify additional suppliers from alternate regions\n"
        if china_dependent:
            output += "  - Explore India or European API manufacturers\n"
        if price > 50000:
            output += "  - Consider backward integration for cost control\n"
        
        return output
    
    except Exception as e:
        return f"Error analyzing supply chain: {str(e)}"
