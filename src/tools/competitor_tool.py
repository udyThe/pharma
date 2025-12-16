"""
Competitor Intelligence Tool
Queries database for competitor strategy and war gaming analysis.
"""
from crewai.tools import tool
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def _extract_entity_from_query(query: str, entity_type: str = "molecule") -> str:
    """Extract molecule or company name from a natural language query."""
    if not query:
        return None
    
    query_lower = query.lower()
    
    if entity_type == "molecule":
        # Known molecules in our database
        known_molecules = [
            "pembrolizumab", "sitagliptin", "rivaroxaban", "pirfenidone",
            "roflumilast", "tiotropium", "omalizumab", "fluticasone",
            "metformin", "trastuzumab"
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
    
    elif entity_type == "company":
        known_companies = [
            "pfizer", "novartis", "roche", "merck", "sanofi", "gsk", 
            "astrazeneca", "johnson", "abbvie", "bristol", "lilly",
            "teva", "sun pharma", "cipla", "dr. reddy"
        ]
        
        for company in known_companies:
            if company in query_lower:
                return company.title()
    
    return None


def _query_database(molecule: str = None, company: str = None):
    """Query competitors from database."""
    try:
        from src.database.db import get_db_session
        from src.database.models import Competitor
        
        with get_db_session() as session:
            query = session.query(Competitor)
            
            if molecule:
                query = query.filter(Competitor.molecule.ilike(f"%{molecule}%"))
            if company:
                query = query.filter(Competitor.competitor_name.ilike(f"%{company}%"))
            
            results = query.all()
            
            if not results:
                return None
            
            return [{
                "competitor": r.competitor_name,
                "molecule": r.molecule,
                "predicted_strategy": r.predicted_strategy,
                "likelihood": r.likelihood or "Medium",
                "impact": r.impact or "Moderate market share impact"
            } for r in results]
    except Exception as e:
        print(f"Database query error: {e}")
        return None


@tool("Get Competitor Strategy")
def get_competitor_strategy(company: str = None, query: str = None) -> str:
    """
    Get strategic intelligence for a specific competitor company.
    
    Args:
        company: Name of competitor company.
        query: Natural language query to extract company from.
    
    Returns:
        Competitor strategies and market positions.
    """
    try:
        if not company and query:
            company = _extract_entity_from_query(query, "company")
        
        if not company:
            return "Could not identify a specific company. Please specify a competitor name (e.g., 'Pfizer', 'Novartis', 'Teva')."
        
        results = _query_database(company=company)
        
        if not results:
            return f"No competitor intelligence found for: {company}. This company may not be in our database."
        
        output = [f"**Competitor Intelligence for {company}:**\n"]
        
        for intel in results:
            likelihood_emoji = "🔴" if intel["likelihood"] == "High" else ("🟡" if intel["likelihood"] == "Medium" else "🟢")
            
            output.append(
                f"**{intel['molecule']}**\n"
                f"  Strategy: {intel['predicted_strategy']}\n"
                f"  {likelihood_emoji} Likelihood: {intel['likelihood']}\n"
                f"  Impact: {intel['impact']}\n"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error querying competitor strategy: {str(e)}"


@tool("Query Competitor Intelligence")
def query_competitor_intel(molecule: str = None, query: str = None) -> str:
    """
    Query competitive intelligence for a specific molecule.
    
    Args:
        molecule: Molecule name to get competitor strategies for.
        query: Natural language query to extract molecule from.
    
    Returns:
        Predicted competitor strategies, likelihood, and impact.
    """
    try:
        if not molecule and query:
            molecule = _extract_entity_from_query(query, "molecule")
        
        if not molecule:
            molecule = query or "unspecified molecule"
        
        results = _query_database(molecule=molecule)
        
        if not results:
            return f"No competitor intelligence found for: {molecule}. This molecule may not be in our database."
        
        output = [f"**Competitor Intelligence for {molecule}:**\n"]
        
        for intel in results:
            likelihood_emoji = "🔴" if intel["likelihood"] == "High" else ("🟡" if intel["likelihood"] == "Medium" else "🟢")
            
            output.append(
                f"**{intel['competitor']}**\n"
                f"  Strategy: {intel['predicted_strategy']}\n"
                f"  {likelihood_emoji} Likelihood: {intel['likelihood']}\n"
                f"  Impact: {intel['impact']}\n"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error querying competitor intel: {str(e)}"


@tool("War Game Scenario")
def war_game_scenario(molecule: str = None, proposed_strategy: str = "Market entry", query: str = None) -> str:
    """
    Simulate a war game scenario: predict competitor responses to your proposed strategy.
    
    Args:
        molecule: Molecule for which strategy is being proposed.
        proposed_strategy: Your proposed strategic move.
        query: Natural language query to extract molecule from.
    
    Returns:
        Predicted competitor counter-moves and risk assessment.
    """
    try:
        if not molecule and query:
            molecule = _extract_entity_from_query(query, "molecule")
        
        if not molecule:
            molecule = query or "unspecified molecule"
        
        results = _query_database(molecule=molecule)
        
        if not results:
            return f"No competitor data available for war gaming: {molecule}. This molecule may not be in our database."
        
        output = [
            f"**War Game Simulation: {molecule}**\n",
            f"**Your Proposed Strategy:** {proposed_strategy}\n",
            f"\n**Predicted Competitor Responses:**\n"
        ]
        
        risk_score = 0
        counter_moves = []
        
        for intel in results:
            likelihood = intel["likelihood"]
            
            if likelihood == "High":
                risk_score += 3
            elif likelihood == "Medium":
                risk_score += 2
            else:
                risk_score += 1
            
            counter_move = _generate_counter_move(intel, proposed_strategy)
            counter_moves.append((intel["competitor"], counter_move, likelihood, intel["impact"]))
        
        for competitor, counter, likelihood, impact in counter_moves:
            output.append(
                f"**{competitor}:**\n"
                f"  Likely Counter: {counter}\n"
                f"  Probability: {likelihood} | Impact: {impact}\n"
            )
        
        avg_risk = risk_score / len(results) if results else 0
        risk_level = "HIGH" if avg_risk > 2.5 else ("MEDIUM" if avg_risk > 1.5 else "LOW")
        
        output.append(f"\n**Overall Risk Assessment: {risk_level}**\n")
        
        output.append("\n**Strategic Recommendations:**\n")
        if risk_level == "HIGH":
            output.append("  ⚠️ High competitive response expected - consider phased approach\n")
            output.append("  ⚠️ Build war chest for potential price competition\n")
            output.append("  ⚠️ Secure supply chain before announcement\n")
        elif risk_level == "MEDIUM":
            output.append("  ℹ️ Prepare for moderate competitive response\n")
            output.append("  ℹ️ Focus on differentiation beyond price\n")
        else:
            output.append("  ✅ Limited competitive response expected\n")
            output.append("  ✅ First-mover advantage possible\n")
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error running war game: {str(e)}"


def _generate_counter_move(intel: dict, proposed_strategy: str) -> str:
    """Generate a predicted counter-move based on intel and proposed strategy."""
    base_strategy = intel["predicted_strategy"]
    
    if "price" in proposed_strategy.lower() or "discount" in proposed_strategy.lower():
        return f"Likely to match or undercut pricing. {base_strategy}"
    elif "launch" in proposed_strategy.lower() or "generic" in proposed_strategy.lower():
        return f"May accelerate own launch timeline. {base_strategy}"
    else:
        return base_strategy


@tool("Assess Competitive Threats")
def assess_competitive_threats(molecule: str = None, query: str = None) -> str:
    """
    Provide a threat assessment summary for a molecule.
    
    Args:
        molecule: Molecule to assess competitive threats for.
        query: Natural language query to extract molecule from.
    
    Returns:
        Threat level summary with recommended counter-strategies.
    """
    try:
        if not molecule and query:
            molecule = _extract_entity_from_query(query, "molecule")
        
        if not molecule:
            molecule = query or "unspecified molecule"
        
        results = _query_database(molecule=molecule)
        
        if not results:
            return f"No threat data available for: {molecule}. This molecule may not be in our database."
        
        high_threats = [r for r in results if r["likelihood"] == "High"]
        medium_threats = [r for r in results if r["likelihood"] == "Medium"]
        
        overall_threat = "HIGH" if len(high_threats) >= 2 else ("MEDIUM" if len(high_threats) >= 1 else "LOW")
        
        output = (
            f"**Competitive Threat Assessment: {molecule}**\n\n"
            f"**Overall Threat Level: {overall_threat}**\n"
            f"  - High Probability Threats: {len(high_threats)}\n"
            f"  - Medium Probability Threats: {len(medium_threats)}\n\n"
        )
        
        if high_threats:
            output += "**Critical Threats:**\n"
            for threat in high_threats:
                output += f"  🔴 {threat['competitor']}: {threat['predicted_strategy']}\n"
        
        output += "\n**Recommended Counter-Strategies:**\n"
        
        counter_strategies = [
            "Build brand loyalty before generic entry",
            "Develop next-generation formulation",
            "Establish authorized generic program",
            "Secure key opinion leader endorsements",
            "Create patient switching barriers"
        ]
        
        for i, strategy in enumerate(counter_strategies[:3], 1):
            output += f"  {i}. {strategy}\n"
        
        return output
    
    except Exception as e:
        return f"Error assessing threats: {str(e)}"
