"""
Patent Landscape Tool
Queries database for patent expiry and FTO analysis.
"""
from datetime import datetime
from crewai.tools import tool
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def _extract_molecule_from_query(query: str) -> str:
    """
    Extract molecule/drug name from a natural language query.
    Returns None if no molecule can be identified.
    """
    if not query:
        return None
    
    query_lower = query.lower()
    
    # Known molecules in our database
    known_molecules = [
        "pembrolizumab", "sitagliptin", "rivaroxaban", "pirfenidone",
        "roflumilast", "tiotropium", "omalizumab", "fluticasone",
        "metformin", "trastuzumab", "ozempic", "semaglutide"
    ]
    
    # Check for known molecules
    for mol in known_molecules:
        if mol in query_lower:
            return mol.capitalize()
    
    # Common words to skip when looking for drug names
    skip_words = {
        "check", "patent", "expiry", "expire", "expires", "for", "the", "a", "an",
        "what", "when", "where", "how", "is", "are", "was", "were", "will", "about",
        "find", "get", "show", "tell", "me", "information", "info", "data", "details",
        "drug", "molecule", "medicine", "pharmaceutical", "latest", "related", "to",
        "in", "of", "on", "at", "by", "with", "from", "and", "or", "us", "india"
    }
    
    # Try to extract word after "for" (e.g., "Check patent expiry for coldact")
    if " for " in query_lower:
        parts = query_lower.split(" for ")
        if len(parts) > 1:
            # Get first word after "for"
            after_for = parts[-1].strip().split()[0] if parts[-1].strip() else None
            if after_for and after_for not in skip_words and len(after_for) > 2:
                return after_for.capitalize()
    
    # Try to find molecule-like words (ending in common suffixes)
    words = query.replace(",", " ").replace(".", " ").replace("?", " ").split()
    drug_suffixes = ["mab", "nib", "lib", "vir", "stat", "pril", "olol", 
                     "sartan", "pine", "azole", "mycin", "cillin", "done",
                     "prazole", "gliptin", "formin", "xaban", "tide"]
    
    for word in words:
        word_clean = word.lower().strip()
        for suffix in drug_suffixes:
            if word_clean.endswith(suffix) and len(word_clean) > len(suffix) + 2:
                return word_clean.capitalize()
    
    # Last resort: find the last non-common word
    for word in reversed(words):
        word_clean = word.lower().strip()
        if word_clean not in skip_words and len(word_clean) > 2:
            return word.strip().capitalize()
    
    return None


def _query_database(molecule: str = None):
    """Query patents from database."""
    try:
        from src.database.db import get_db_session
        from src.database.models import Patent
        
        with get_db_session() as session:
            if molecule:
                # Search for specific molecule (case-insensitive)
                patents = session.query(Patent).filter(
                    Patent.molecule.ilike(f"%{molecule}%")
                ).all()
            else:
                # Get all patents
                patents = session.query(Patent).all()
            
            if not patents:
                return None
            
            # Group by molecule
            results = {}
            for p in patents:
                mol_name = p.molecule
                if mol_name not in results:
                    results[mol_name] = {"molecule": mol_name, "patents": []}
                results[mol_name]["patents"].append({
                    "patent_number": p.patent_number,
                    "type": p.patent_type,
                    "expiry_date": p.expiry_date.strftime("%Y-%m-%d") if p.expiry_date else None,
                    "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
                    "country": p.country
                })
            
            return list(results.values())
    except Exception as e:
        print(f"Database query error: {e}")
        return None


def _fetch_and_cache_drug_info(molecule: str) -> dict:
    """
    Fetch drug info using Tavily web search.
    Falls back to this when database has no results.
    """
    try:
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            return None
        
        from tavily import TavilyClient
        
        client = TavilyClient(api_key=tavily_key)
        
        # Create specific search query - focused on the drug and patent info
        query = f'"{molecule}" patent expiry status generic version manufacturer active ingredient'
        
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_answer=True
        )
        
        if not response:
            return None
        
        result = {
            "molecule": molecule,
            "source": "tavily_web_search",
            "info": {}
        }
        
        # Extract answer if available
        if response.get("answer"):
            result["info"]["summary"] = response["answer"]
        
        # Filter and extract relevant sources - only keep those that mention the drug
        molecule_lower = molecule.lower()
        relevant_sources = []
        
        for r in response.get("results", []):
            content = (r.get("content") or "").lower()
            title = (r.get("title") or "").lower()
            
            # Only include if the drug name appears in content or title
            if molecule_lower in content or molecule_lower in title:
                relevant_sources.append({
                    "title": r.get("title", "")[:80],
                    "snippet": r.get("content", "")[:250],
                    "url": r.get("url", "")
                })
        
        # If no relevant sources, use top 3 general results
        if not relevant_sources:
            for r in response.get("results", [])[:3]:
                relevant_sources.append({
                    "title": r.get("title", "")[:80],
                    "snippet": r.get("content", "")[:250],
                    "url": r.get("url", "")
                })
        
        result["info"]["sources"] = relevant_sources[:3]  # Limit to 3 sources
        result["info"]["data_source"] = "Tavily Web Search"
        
        return result
        
    except Exception as e:
        print(f"Tavily search error: {e}")
        return None




@tool("Query Patent Data")
def query_patents(molecule: str = None, query: str = None) -> str:
    """
    Query patent data for a specific molecule including expiry dates and status.
    Falls back to external APIs (PubChem, ChEMBL, OpenFDA) if not in database.
    
    Args:
        molecule: Name of the molecule/drug to search for patent information.
        query: Natural language query to extract molecule name from (used if molecule is None).
    
    Returns:
        Patent details including patent numbers, types, expiry dates, and status.
    """
    try:
        if not molecule and query:
            molecule = _extract_molecule_from_query(query)
        if not molecule:
            # Try to extract any drug name from query
            if query:
                words = query.replace(",", " ").replace(".", " ").replace("?", " ").split()
                # Look for capitalized words that might be drug names
                for word in words:
                    if len(word) > 3 and word[0].isupper():
                        molecule = word
                        break
            if not molecule:
                molecule = query or "unspecified molecule"
        
        # First, try database
        data = _query_database(molecule)
        
        if data:
            result = data[0]  # Get first matching molecule
            
            # Format output
            output = [f"**Patent Landscape for {result['molecule']}:**\n"]
            
            for patent in result.get("patents", []):
                expiry_date = patent["expiry_date"]
                status = patent["status"]
                
                # Calculate days until expiry
                try:
                    expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                    today = datetime.now()
                    days_remaining = (expiry - today).days
                    
                    if days_remaining < 0:
                        time_info = f"Expired {abs(days_remaining)} days ago"
                    elif days_remaining < 365:
                        time_info = f"Expires in {days_remaining} days (< 1 year)"
                    else:
                        years = days_remaining // 365
                        time_info = f"Expires in ~{years} years"
                except:
                    time_info = "Date parsing error"
                
                output.append(
                    f"- **{patent['patent_number']}** ({patent['type']})\n"
                    f"  Status: {status} | Expiry: {expiry_date}\n"
                    f"  {time_info}"
                )
            
            return "\n".join(output)
        
        # Database had no results - try Tavily web search
        external_data = _fetch_and_cache_drug_info(molecule)
        
        if external_data:
            info = external_data.get("info", {})
            output = [f"**Information for {molecule}** *(from {info.get('data_source', 'Web Search')})*\n"]
            
            # Show AI-generated summary if available
            if info.get("summary"):
                output.append(f"**Summary:**\n{info['summary']}\n")
            
            # Show sources
            sources = info.get("sources", [])
            if sources:
                output.append("**Sources:**")
                for src in sources[:3]:
                    title = src.get("title", "Untitled")
                    snippet = src.get("snippet", "")[:200]
                    url = src.get("url", "")
                    output.append(f"- **{title}**")
                    if snippet:
                        output.append(f"  {snippet}...")
                    if url:
                        output.append(f"  [Link]({url})")
            
            output.append("\n---")
            output.append("*Data fetched via Tavily web search. For official patent data, consult USPTO Orange Book.*")
            
            return "\n".join(output)
        
        # No data found anywhere
        return (
            f"No data found for '{molecule}' in database or external sources.\n\n"
            "**Suggestions:**\n"
            "- Check the spelling of the molecule/drug name\n"
            "- Try using the generic name (INN) instead of brand name\n"
            "- Try common alternatives like: Pembrolizumab, Sitagliptin, Rivaroxaban"
        )
    
    except Exception as e:
        return f"Error querying patent data: {str(e)}"


@tool("Check Patent Expiry")
def check_patent_expiry(molecule: str = None, country: str = "US", query: str = None) -> str:
    """
    Check when patents expire for a molecule to assess generic entry opportunity.
    
    Args:
        molecule: Name of the molecule to check.
        country: Country for patent check (default: US).
        query: Natural language query to extract molecule name from (used if molecule is None).
    
    Returns:
        Patent expiry date and whether generic entry is possible.
    """
    try:
        if not molecule and query:
            molecule = _extract_molecule_from_query(query)
        if not molecule:
            # Try to extract any capitalized word from query as drug name
            if query:
                words = query.replace(",", " ").replace(".", " ").replace("?", " ").split()
                for word in words:
                    if len(word) > 3 and word[0].isupper():
                        molecule = word
                        break
            if not molecule:
                molecule = query or "unspecified molecule"
        
        data = _query_database(molecule)
        
        if not data:
            # Try external APIs for drug information
            external_data = _fetch_and_cache_drug_info(molecule)
            
            if external_data:
                info = external_data.get("info", {})
                output = [f"**Information for {molecule}** *(from {info.get('data_source', 'Web Search')})*\n"]
                
                # Show AI-generated summary if available
                if info.get("summary"):
                    output.append(f"**Summary:**\n{info['summary']}\n")
                
                # Show sources
                sources = info.get("sources", [])
                if sources:
                    output.append("**Sources:**")
                    for src in sources[:3]:
                        title = src.get("title", "Untitled")
                        snippet = src.get("snippet", "")[:200]
                        output.append(f"- **{title}**")
                        if snippet:
                            output.append(f"  {snippet}...")
                
                output.append("\n---")
                output.append("*Data via Tavily web search. For official patent expiry data, consult USPTO Orange Book.*")
                
                return "\n".join(output)
            
            return (
                f"No data found for '{molecule}' in database or external sources.\n\n"
                "**Suggestions:**\n"
                "- Check the spelling of the drug name\n"
                "- Try the generic name (INN) instead of brand name\n"
                "- Available in database: Pembrolizumab, Sitagliptin, Rivaroxaban, Pirfenidone"
            )
        
        result = data[0]
        
        # Find earliest unexpired and latest expired patents
        today = datetime.now()
        active_patents = []
        expired_patents = []
        
        for patent in result.get("patents", []):
            expiry = datetime.strptime(patent["expiry_date"], "%Y-%m-%d")
            patent_info = {
                "number": patent["patent_number"],
                "type": patent["type"],
                "expiry": patent["expiry_date"],
                "days": (expiry - today).days
            }
            
            if patent["status"] == "Expired" or expiry < today:
                expired_patents.append(patent_info)
            else:
                active_patents.append(patent_info)
        
        output = [f"**Patent Expiry Analysis for {result['molecule']} ({country}):**\n"]
        
        if not active_patents:
            output.append("✅ **GENERIC ENTRY POSSIBLE** - All patents expired\n")
            output.append("Expired Patents:")
            for p in expired_patents:
                output.append(f"  - {p['number']} ({p['type']}): Expired {p['expiry']}")
        else:
            # Sort by expiry date
            active_patents.sort(key=lambda x: x["days"])
            earliest = active_patents[0]
            
            if earliest["days"] < 365:
                output.append(f"⚠️ **PATENT EXPIRING SOON** - {earliest['days']} days remaining\n")
            else:
                years = earliest["days"] // 365
                output.append(f"🔒 **PATENT PROTECTED** - ~{years} years remaining\n")
            
            output.append("Active Patents:")
            for p in active_patents:
                output.append(f"  - {p['number']} ({p['type']}): Expires {p['expiry']}")
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error checking patent expiry: {str(e)}"


@tool("Assess FTO Risk")
def assess_fto_risk(molecule: str = None, query: str = None) -> str:
    """
    Assess Freedom to Operate (FTO) risk for a molecule.
    
    Args:
        molecule: Name of the molecule to assess.
        query: Natural language query to extract molecule name from (used if molecule is None).
    
    Returns:
        FTO risk level (High/Medium/Low) with explanation.
    """
    try:
        if not molecule and query:
            molecule = _extract_molecule_from_query(query)
        if not molecule:
            molecule = query or "unspecified molecule"
        
        data = _query_database(molecule)
        
        if not data:
            return f"No patent data found for {molecule}. FTO risk: UNCLEAR - molecule not in database."
        
        result = data[0]
        today = datetime.now()
        active_com_patents = 0  # Composition of Matter
        active_form_patents = 0  # Formulation
        
        for patent in result.get("patents", []):
            expiry = datetime.strptime(patent["expiry_date"], "%Y-%m-%d")
            if expiry > today:
                if "composition" in patent["type"].lower():
                    active_com_patents += 1
                else:
                    active_form_patents += 1
        
        # Determine risk level
        if active_com_patents > 0:
            risk_level = "HIGH"
            explanation = "Active Composition of Matter patent blocks generic development"
        elif active_form_patents > 0:
            risk_level = "MEDIUM"
            explanation = "Formulation patents exist but can potentially be designed around"
        else:
            risk_level = "LOW"
            explanation = "No active blocking patents - clear path for generic development"
        
        return (
            f"**FTO Risk Assessment for {result['molecule']}:**\n\n"
            f"Risk Level: **{risk_level}**\n"
            f"Explanation: {explanation}\n\n"
            f"Active Composition Patents: {active_com_patents}\n"
            f"Active Formulation Patents: {active_form_patents}"
        )
    
    except Exception as e:
        return f"Error assessing FTO risk: {str(e)}"
