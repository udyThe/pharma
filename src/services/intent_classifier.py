"""
Intent Classifier Service
LLM-based intent detection for intelligent agent routing.
Replaces keyword-based matching with semantic understanding.
"""
import os
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class IntentType(Enum):
    """Intent types matching AgentType for consistency."""
    MARKET = "market"
    PATENT = "patent"
    CLINICAL = "clinical"
    PATIENT = "patient"
    COMPETITOR = "competitor"
    TRADE = "trade"
    INTERNAL = "internal"
    WEB = "web"
    GENERAL = "general"


class AgentType(Enum):
    """Available agent types in the system."""
    MARKET = "market"
    PATENT = "patent"
    CLINICAL = "clinical"
    PATIENT = "patient"
    COMPETITOR = "competitor"
    TRADE = "trade"
    INTERNAL = "internal"
    WEB = "web"
    GENERAL = "general"


@dataclass
class IntentResult:
    """Result of intent classification."""
    primary_intent: str
    agents_needed: List[AgentType]
    confidence: float
    entities: Dict[str, any]  # Extracted entities like molecule names, therapy areas
    requires_synthesis: bool  # Whether multiple agents need to be combined
    suggested_followups: List[str]
    
    @property
    def intent_type(self) -> IntentType:
        """Map primary_intent to IntentType enum for compatibility."""
        # Map intent names to IntentType
        intent_map = {
            "market_analysis": IntentType.MARKET,
            "patent_analysis": IntentType.PATENT,
            "clinical_research": IntentType.CLINICAL,
            "patient_insights": IntentType.PATIENT,
            "competitive_intelligence": IntentType.COMPETITOR,
            "supply_chain": IntentType.TRADE,
            "internal_knowledge": IntentType.INTERNAL,
            "current_events": IntentType.WEB,
            "comprehensive_analysis": IntentType.GENERAL,
            "general_pharma": IntentType.GENERAL,
        }
        return intent_map.get(self.primary_intent, IntentType.GENERAL)


# Intent definitions with descriptions for the LLM
INTENT_DEFINITIONS = {
    "market_analysis": {
        "description": "Questions about market size, growth rates, competition levels, whitespace opportunities, CAGR, market share",
        "agents": [AgentType.MARKET],
        "examples": [
            "What is the market size for diabetes drugs?",
            "Which therapy areas have low competition?",
            "Show me whitespace opportunities in respiratory"
        ]
    },
    "patent_analysis": {
        "description": "Questions about patents, IP, patent expiry, freedom to operate, generic entry, patent landscape",
        "agents": [AgentType.PATENT],
        "examples": [
            "When does the Sitagliptin patent expire?",
            "Check FTO for entering the oncology space",
            "What patents protect Pembrolizumab?"
        ]
    },
    "clinical_research": {
        "description": "Questions about clinical trials, drug pipeline, phases, repurposing opportunities, trial data",
        "agents": [AgentType.CLINICAL],
        "examples": [
            "What trials are running for NSCLC?",
            "Show me Phase 3 oncology trials",
            "Find repurposing opportunities for Metformin"
        ]
    },
    "patient_insights": {
        "description": "Questions about patient sentiment, complaints, patient voice, social media analysis, patient needs",
        "agents": [AgentType.PATIENT],
        "examples": [
            "What are patients saying about injectable diabetes drugs?",
            "Analyze patient complaints in the RA space",
            "What do patients dislike about current treatments?"
        ]
    },
    "competitive_intelligence": {
        "description": "Questions about competitors, competitive strategy, war gaming, market positioning, competitive threats",
        "agents": [AgentType.COMPETITOR],
        "examples": [
            "What will competitors do if we launch a generic?",
            "Simulate competitive response to our entry",
            "Who are the main competitors for Rivaroxaban?"
        ]
    },
    "supply_chain": {
        "description": "Questions about imports, exports, API sourcing, trade data, supply chain, pricing",
        "agents": [AgentType.TRADE],
        "examples": [
            "Where can we source Metformin API?",
            "What are import volumes for oncology drugs?",
            "Show trade data for diabetes medications"
        ]
    },
    "internal_knowledge": {
        "description": "Questions about internal documents, company strategy, past decisions, field reports",
        "agents": [AgentType.INTERNAL],
        "examples": [
            "What does our strategy document say about oncology?",
            "Find internal reports on diabetes market",
            "What were our past learnings in respiratory?"
        ]
    },
    "current_events": {
        "description": "Questions about recent news, FDA approvals, announcements, current developments",
        "agents": [AgentType.WEB],
        "examples": [
            "What are the latest FDA approvals?",
            "Recent news about Pfizer oncology pipeline",
            "Any new drug approvals this month?"
        ]
    },
    "comprehensive_analysis": {
        "description": "Complex questions requiring multiple data sources and synthesis",
        "agents": [AgentType.MARKET, AgentType.PATENT, AgentType.CLINICAL, AgentType.COMPETITOR],
        "examples": [
            "Should we enter the NASH market?",
            "Full analysis of diabetes opportunity in India",
            "Evaluate our options for biosimilar entry"
        ]
    },
    "general_pharma": {
        "description": "General pharmaceutical questions, drug information, medical knowledge",
        "agents": [AgentType.GENERAL],
        "examples": [
            "How does Metformin work?",
            "What are the side effects of statins?",
            "Explain the mechanism of PD-1 inhibitors"
        ]
    }
}


class IntentClassifier:
    """
    LLM-based intent classifier for pharmaceutical queries.
    Uses Groq for fast, accurate intent detection.
    """
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    def classify_intent(self, query: str, conversation_context: Optional[List[Dict]] = None) -> IntentResult:
        """
        Classify the intent of a user query.
        Alias for classify() for backwards compatibility.
        """
        return self.classify(query, conversation_context)
    
    def classify(self, query: str, conversation_context: Optional[List[Dict]] = None) -> IntentResult:
        """
        Classify the intent of a user query.
        
        Args:
            query: User's natural language query
            conversation_context: Optional recent conversation for context
            
        Returns:
            IntentResult with classified intents and extracted entities
        """
        # First try rule-based classification for common patterns (faster)
        rule_result = self._rule_based_classify(query)
        if rule_result and rule_result.confidence >= 0.9:
            return rule_result
        
        # Fall back to LLM classification for complex queries
        try:
            return self._llm_classify(query, conversation_context)
        except Exception as e:
            print(f"LLM classification failed: {e}")
            # Fallback to rule-based
            return rule_result or self._default_result(query)
    
    def _rule_based_classify(self, query: str) -> Optional[IntentResult]:
        """Fast rule-based classification for common patterns."""
        q = query.lower()
        entities = self._extract_entities(query)
        
        # Market analysis patterns
        if any(w in q for w in ["market size", "market share", "cagr", "growth rate", "whitespace", "competition level", "low competition"]):
            return IntentResult(
                primary_intent="market_analysis",
                agents_needed=[AgentType.MARKET],
                confidence=0.95,
                entities=entities,
                requires_synthesis=False,
                suggested_followups=["What about patent landscape?", "Show clinical trial activity"]
            )
        
        # Patent patterns
        if any(w in q for w in ["patent", "expiry", "expire", "fto", "freedom to operate", "generic entry", "ip landscape"]):
            return IntentResult(
                primary_intent="patent_analysis",
                agents_needed=[AgentType.PATENT],
                confidence=0.95,
                entities=entities,
                requires_synthesis=False,
                suggested_followups=["Check market opportunity", "Analyze competitor patents"]
            )
        
        # Clinical trial patterns
        if any(w in q for w in ["clinical trial", "phase ", "pipeline", "repurpos", "trial data", "nct"]):
            return IntentResult(
                primary_intent="clinical_research",
                agents_needed=[AgentType.CLINICAL],
                confidence=0.95,
                entities=entities,
                requires_synthesis=False,
                suggested_followups=["What's the competitive landscape?", "Check patent status"]
            )
        
        # Patient voice patterns
        if any(w in q for w in ["patient complain", "patient voice", "sentiment", "patient feedback", "what are patients", "patient need"]):
            return IntentResult(
                primary_intent="patient_insights",
                agents_needed=[AgentType.PATIENT],
                confidence=0.95,
                entities=entities,
                requires_synthesis=False,
                suggested_followups=["Analyze market opportunity", "Check unmet needs"]
            )
        
        # Competitor patterns
        if any(w in q for w in ["competitor", "war game", "simulate", "competitive", "what will", "counter strategy"]):
            return IntentResult(
                primary_intent="competitive_intelligence",
                agents_needed=[AgentType.COMPETITOR],
                confidence=0.95,
                entities=entities,
                requires_synthesis=False,
                suggested_followups=["Check patent landscape", "Analyze market dynamics"]
            )
        
        # Trade/supply chain patterns
        if any(w in q for w in ["import", "export", "trade", "supply", "source", "api sourcing", "pricing"]):
            return IntentResult(
                primary_intent="supply_chain",
                agents_needed=[AgentType.TRADE],
                confidence=0.95,
                entities=entities,
                requires_synthesis=False,
                suggested_followups=["Check market data", "Analyze competitors"]
            )
        
        # News/current events patterns
        if any(w in q for w in ["latest", "recent", "news", "fda approv", "announced", "today", "this week", "this month", "2024", "2025"]):
            return IntentResult(
                primary_intent="current_events",
                agents_needed=[AgentType.WEB],
                confidence=0.90,
                entities=entities,
                requires_synthesis=False,
                suggested_followups=["Analyze impact on market", "Check competitive implications"]
            )
        
        # Internal docs patterns
        if any(w in q for w in ["internal", "our strategy", "our document", "company", "field report", "our analysis"]):
            return IntentResult(
                primary_intent="internal_knowledge",
                agents_needed=[AgentType.INTERNAL],
                confidence=0.90,
                entities=entities,
                requires_synthesis=False,
                suggested_followups=["Compare with market data", "Check latest developments"]
            )
        
        # Comprehensive analysis patterns
        if any(w in q for w in ["should we", "evaluate", "full analysis", "comprehensive", "enter the", "opportunity assessment"]):
            return IntentResult(
                primary_intent="comprehensive_analysis",
                agents_needed=[AgentType.MARKET, AgentType.PATENT, AgentType.CLINICAL, AgentType.COMPETITOR],
                confidence=0.85,
                entities=entities,
                requires_synthesis=True,
                suggested_followups=["Deep dive into specific area", "Check patient insights"]
            )
        
        # No strong match - return None to trigger LLM classification
        return None
    
    def _llm_classify(self, query: str, conversation_context: Optional[List[Dict]] = None) -> IntentResult:
        """Use LLM for complex intent classification."""
        from groq import Groq
        
        client = Groq(api_key=self.groq_api_key)
        
        # Build intent descriptions for the prompt
        intent_descriptions = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in INTENT_DEFINITIONS.items()
        ])
        
        context_str = ""
        if conversation_context:
            recent = conversation_context[-3:]
            context_str = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in recent])
            context_str = f"\nRecent conversation:\n{context_str}\n"
        
        system_prompt = f"""You are an intent classifier for a pharmaceutical business intelligence system.

Available intents:
{intent_descriptions}

Your task:
1. Classify the user's query into one or more intents
2. Extract key entities (molecule names, therapy areas, companies, regions)
3. Determine if synthesis across multiple agents is needed
4. Suggest follow-up questions

Respond in JSON format:
{{
    "primary_intent": "intent_name",
    "secondary_intents": ["intent2", "intent3"],
    "confidence": 0.0-1.0,
    "entities": {{
        "molecules": ["name1"],
        "therapy_areas": ["area1"],
        "companies": ["company1"],
        "regions": ["region1"]
    }},
    "requires_synthesis": true/false,
    "reasoning": "brief explanation"
}}"""

        user_message = f"{context_str}Query to classify: {query}"
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        # Parse the response
        try:
            result_text = response.choices[0].message.content
            # Extract JSON from response
            json_match = result_text
            if "```json" in result_text:
                json_match = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                json_match = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(json_match.strip())
            
            # Map intent to agents
            primary = result.get("primary_intent", "general_pharma")
            secondary = result.get("secondary_intents", [])
            
            agents = []
            for intent in [primary] + secondary:
                if intent in INTENT_DEFINITIONS:
                    agents.extend(INTENT_DEFINITIONS[intent]["agents"])
            
            # Deduplicate agents
            agents = list(dict.fromkeys(agents))
            
            if not agents:
                agents = [AgentType.GENERAL]
            
            return IntentResult(
                primary_intent=primary,
                agents_needed=agents,
                confidence=result.get("confidence", 0.7),
                entities=result.get("entities", {}),
                requires_synthesis=result.get("requires_synthesis", len(agents) > 1),
                suggested_followups=[]
            )
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing LLM response: {e}")
            return self._default_result(query)
    
    def _extract_entities(self, query: str) -> Dict[str, str]:
        """Extract common pharmaceutical entities from query."""
        entities = {}
        q = query.lower()
        
        # Known molecules (expand this list)
        molecules = [
            "sitagliptin", "metformin", "pembrolizumab", "rivaroxaban",
            "adalimumab", "trastuzumab", "nivolumab", "atezolizumab",
            "fluticasone", "salmeterol", "budesonide", "pirfenidone",
            "nintedanib", "osimertinib", "imatinib", "lenvatinib"
        ]
        
        for mol in molecules:
            if mol in q:
                entities["molecule"] = mol.title()
                break
        
        # Therapy areas
        therapy_areas = {
            "oncology": ["oncology", "cancer", "tumor", "carcinoma", "nsclc", "melanoma"],
            "diabetes": ["diabetes", "diabetic", "glucose", "insulin", "a1c", "hba1c"],
            "respiratory": ["respiratory", "copd", "asthma", "ipf", "lung", "pulmonary"],
            "cardiovascular": ["cardiovascular", "cardiac", "heart", "hypertension", "cholesterol"],
            "immunology": ["immunology", "autoimmune", "rheumatoid", "arthritis", "psoriasis"],
            "neurology": ["neurology", "neurological", "alzheimer", "parkinson", "ms", "multiple sclerosis"]
        }
        
        for area, keywords in therapy_areas.items():
            if any(kw in q for kw in keywords):
                entities["therapy_area"] = area.title()
                break
        
        # Regions
        regions = {
            "india": ["india", "indian"],
            "us": ["us", "usa", "united states", "america"],
            "eu": ["europe", "european", "eu"],
            "china": ["china", "chinese"],
            "japan": ["japan", "japanese"],
            "global": ["global", "worldwide", "international"]
        }
        
        for region, keywords in regions.items():
            if any(kw in q for kw in keywords):
                entities["region"] = region.upper()
                break
        
        return entities
    
    def _default_result(self, query: str) -> IntentResult:
        """Return default classification when all else fails."""
        entities = self._extract_entities(query)
        
        return IntentResult(
            primary_intent="general_pharma",
            agents_needed=[AgentType.GENERAL],
            confidence=0.5,
            entities=entities,
            requires_synthesis=False,
            suggested_followups=[
                "Would you like market analysis?",
                "Should I check the patent landscape?",
                "Want to see clinical trial data?"
            ]
        )


# Convenience function
def classify_query(query: str, context: Optional[List[Dict]] = None) -> IntentResult:
    """Classify a query and return intent result."""
    classifier = IntentClassifier()
    return classifier.classify(query, context)
