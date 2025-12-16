"""
Social Media Listening Tool
Queries database for patient voice analysis.
"""
import json
from typing import Optional
from crewai.tools import tool
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def _extract_entity_from_query(query: str, entity_type: str = "therapy_area") -> str:
    """Extract entities from natural language query."""
    if not query:
        return None
    
    query_lower = query.lower()
    
    if entity_type == "therapy_area":
        areas = {
            "diabetes": ["diabetes", "diabetic", "injectable", "insulin", "glp-1", "weight", "obesity"],
            "respiratory": ["respiratory", "inhaler", "copd", "asthma", "pulmonary"],
            "oncology": ["oncology", "cancer", "chemo", "tumor"],
            "cardiovascular": ["cardiac", "heart", "cardiovascular", "blood pressure", "cholesterol"],
            "cns": ["depression", "anxiety", "mental", "psychiatric", "neuro", "brain"],
            "autoimmune": ["autoimmune", "rheumatoid", "crohn", "arthritis", "psoriasis"],
            "analgesic": ["pain", "fever", "headache", "analgesic"],
            "gastrointestinal": ["gerd", "acid", "reflux", "gastro", "ulcer", "stomach"]
        }
        for area, keywords in areas.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return area.capitalize() if area not in ["cns"] else area.upper()
    
    elif entity_type == "molecule":
        # Brand name mappings
        brand_to_molecule = {
            "ozempic": "Semaglutide", "wegovy": "Semaglutide",
            "mounjaro": "Tirzepatide", "humira": "Adalimumab",
            "dolo": "Paracetamol", "calpol": "Paracetamol",
            "pan": "Pantoprazole", "nexito": "Escitalopram"
        }
        for brand, mol in brand_to_molecule.items():
            if brand in query_lower:
                return mol
        
        known_molecules = [
            "insulin", "semaglutide", "tirzepatide", "metformin", "sitagliptin",
            "adalimumab", "escitalopram", "pantoprazole", "paracetamol",
            "atorvastatin", "amlodipine", "rivaroxaban", "azithromycin", "montelukast",
            "tiotropium", "fluticasone", "pirfenidone", "pembrolizumab", "trastuzumab", "lenalidomide"
        ]
        for mol in known_molecules:
            if mol in query_lower:
                return mol.capitalize()
    
    return None


def _query_database(therapy_area: str = None, molecule: str = None):
    """Query social posts from database."""
    try:
        from src.database.db import get_db_session
        from src.database.models import SocialPost
        
        with get_db_session() as session:
            query = session.query(SocialPost)
            
            if therapy_area:
                query = query.filter(SocialPost.therapy_area.ilike(f"%{therapy_area}%"))
            if molecule:
                query = query.filter(SocialPost.molecule.ilike(f"%{molecule}%"))
            
            results = query.all()
            
            if not results:
                return None
            
            return [{
                "molecule": r.molecule,
                "therapy_area": r.therapy_area,
                "source": r.source,
                "date": r.post_date.strftime("%Y-%m-%d") if r.post_date else "N/A",
                "post_text": r.post_text,
                "sentiment": r.sentiment or 0,
                "complaint_theme": r.complaint_theme
            } for r in results]
    except Exception as e:
        print(f"Database query error: {e}")
        return None


def _load_social_data() -> list:
    """Load social data from database, fallback to JSON."""
    db_data = _query_database()
    if db_data:
        return db_data
    
    data_path = Path(__file__).resolve().parent.parent.parent / "mock_data" / "social_media_posts.json"
    if data_path.exists():
        with open(data_path, "r") as f:
            return json.load(f)
    return []


@tool("Query Social Media Sentiment")
def query_social_media(molecule: Optional[str] = None, therapy_area: Optional[str] = None) -> str:
    """
    Query patient social media posts for sentiment and complaint analysis.
    
    Args:
        molecule: Drug name to search for patient feedback
        therapy_area: Therapeutic area (e.g., 'Diabetes', 'Respiratory')
    
    Returns:
        Patient posts with sentiment scores and complaint themes.
    """
    try:
        data = _load_social_data()
        results = []
        
        for post in data:
            if molecule and molecule.lower() not in post.get("molecule", "").lower():
                continue
            if therapy_area and therapy_area.lower() not in post.get("therapy_area", "").lower():
                continue
            results.append(post)
        
        if not results:
            return f"No social media data found for molecule='{molecule}', therapy_area='{therapy_area}'"
        
        output = []
        for post in results:
            sentiment = post["sentiment"]
            sentiment_label = "Positive" if sentiment > 0.3 else ("Negative" if sentiment < -0.3 else "Neutral")
            sentiment_emoji = "😊" if sentiment > 0.3 else ("😞" if sentiment < -0.3 else "😐")
            
            output.append(
                f"**{post['molecule']}** - {post['source']} ({post['date']})\n"
                f"  Sentiment: {sentiment_emoji} {sentiment_label} ({sentiment:.1f})\n"
                f"  Theme: {post.get('complaint_theme', 'N/A')}\n"
                f"  Quote: \"{post['post_text']}\"\n"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error querying social media: {str(e)}"


@tool("Analyze Patient Complaints")
def analyze_patient_complaints(therapy_area: str = None, query: Optional[str] = None) -> str:
    """
    Analyze common patient complaints for a therapy area to identify innovation opportunities.
    
    Args:
        therapy_area: Therapeutic area to analyze (e.g., 'Diabetes', 'Respiratory')
        query: Natural language query to extract therapy area from
    
    Returns:
        Summary of complaint themes and innovation opportunities.
    """
    try:
        # Extract from query if not provided
        if not therapy_area and query:
            therapy_area = _extract_entity_from_query(query, "therapy_area")
        
        if not therapy_area:
            therapy_area = query or "unspecified"
        
        # Try database first
        db_data = _query_database(therapy_area=therapy_area)
        data = db_data if db_data else _load_social_data()
        
        # Filter by therapy area
        posts = [p for p in data if therapy_area.lower() in p.get("therapy_area", "").lower()]
        
        if not posts:
            return f"No patient data found for therapy area: {therapy_area}"
        
        # Aggregate complaint themes
        themes = {}
        molecules = set()
        total_sentiment = 0
        
        for post in posts:
            theme = post.get("complaint_theme", "Other")
            themes[theme] = themes.get(theme, 0) + 1
            molecules.add(post["molecule"])
            total_sentiment += post["sentiment"]
        
        avg_sentiment = total_sentiment / len(posts)
        
        # Sort themes by frequency
        sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)
        
        output = (
            f"**Patient Voice Analysis for {therapy_area}:**\n\n"
            f"**Posts Analyzed:** {len(posts)}\n"
            f"**Molecules Discussed:** {', '.join(molecules)}\n"
            f"**Average Sentiment:** {avg_sentiment:.2f} "
            f"({'Positive' if avg_sentiment > 0.3 else 'Negative' if avg_sentiment < -0.3 else 'Neutral'})\n\n"
            f"**Top Complaint Themes:**\n"
        )
        
        for theme, count in sorted_themes:
            pct = (count / len(posts)) * 100
            output += f"  - {theme}: {count} mentions ({pct:.0f}%)\n"
        
        # Innovation opportunities
        output += "\n**Innovation Opportunities:**\n"
        
        opportunity_map = {
            "Needle pain": "Develop oral or transdermal formulation",
            "Side effects": "Invest in better-tolerated next-gen compounds",
            "Storage issues": "Develop room-temperature stable formulation",
            "Cost": "Launch value brand or patient assistance program",
            "Ease of use": "Simplify device or reduce dosing frequency",
            "Device complexity": "Develop simpler delivery device",
            "Convenience": "Create more portable/discreet formulation"
        }
        
        for theme, _ in sorted_themes[:3]:
            if theme in opportunity_map:
                output += f"  ✅ {opportunity_map[theme]} (addresses '{theme}')\n"
        
        return output
    
    except Exception as e:
        return f"Error analyzing complaints: {str(e)}"


@tool("Get Patient Quotes")
def get_patient_quotes(molecule: str, limit: int = 5) -> str:
    """
    Get direct patient quotes about a specific drug for qualitative insights.
    
    Args:
        molecule: Drug name to get patient quotes for
        limit: Maximum number of quotes to return (default: 5)
    
    Returns:
        Direct patient quotes with sources and dates.
    """
    try:
        data = _load_social_data()
        
        quotes = [p for p in data if molecule.lower() in p.get("molecule", "").lower()]
        
        if not quotes:
            return f"No patient quotes found for: {molecule}"
        
        quotes = quotes[:limit]
        
        output = [f"**Patient Voices on {molecule}:**\n"]
        
        for q in quotes:
            sentiment = "👍" if q["sentiment"] > 0.3 else ("👎" if q["sentiment"] < -0.3 else "➖")
            output.append(
                f"{sentiment} \"{q['post_text']}\"\n"
                f"   — {q['source']}, {q['date']}\n"
            )
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error getting quotes: {str(e)}"
