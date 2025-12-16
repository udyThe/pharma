"""
Worker Agents Definition
CrewAI agents specialized for pharmaceutical data analysis.
"""
from crewai import Agent, LLM
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize Groq LLM
def get_llm():
    """Get the Groq LLM instance."""
    return LLM(
        model=f"groq/{os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1
    )


def create_iqvia_agent(tools: list = None) -> Agent:
    """Create the IQVIA Market Analyst agent."""
    from src.tools.iqvia_tool import query_iqvia_market, find_low_competition_markets
    
    return Agent(
        role="Market Data Specialist",
        goal="Analyze pharmaceutical market data to identify market size, growth rates, competition levels, and whitespace opportunities",
        backstory="""You are a senior market analyst with 15 years of experience in pharmaceutical market intelligence. 
        You have deep expertise in analyzing IQVIA data to identify market trends, competitive dynamics, and growth opportunities.
        You excel at identifying 'whitespace' - therapeutic areas or geographies with high patient burden but low competition.
        You always provide data-driven insights with specific numbers and actionable recommendations.""",
        tools=tools or [query_iqvia_market, find_low_competition_markets],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_patent_agent(tools: list = None) -> Agent:
    """Create the Patent Landscape Analyst agent."""
    from src.tools.patent_tool import query_patents, check_patent_expiry, assess_fto_risk
    
    return Agent(
        role="IP Legal Analyst",
        goal="Analyze patent landscapes to determine freedom to operate, expiry dates, and generic entry opportunities",
        backstory="""You are a pharmaceutical patent attorney with expertise in analyzing drug patents globally.
        You specialize in identifying patent expiry dates, assessing Freedom to Operate (FTO) risks, 
        and advising on generic entry strategies. You understand composition of matter patents, 
        formulation patents, and process patents. You always provide clear recommendations on IP risks.""",
        tools=tools or [query_patents, check_patent_expiry, assess_fto_risk],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_exim_agent(tools: list = None) -> Agent:
    """Create the EXIM Trade Analyst agent."""
    from src.tools.exim_tool import query_exim_trade, analyze_supply_chain
    
    return Agent(
        role="Supply Chain & Trade Analyst",
        goal="Analyze pharmaceutical import/export data to understand supply chain dynamics, pricing, and sourcing strategies",
        backstory="""You are a supply chain expert with deep knowledge of pharmaceutical API trade flows.
        You track import volumes, source countries, and pricing trends to identify supply risks and opportunities.
        You advise on China dependency risks, alternate sourcing, and backward integration opportunities.
        You always consider geopolitical factors affecting pharmaceutical supply chains.""",
        tools=tools or [query_exim_trade, analyze_supply_chain],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_clinical_agent(tools: list = None) -> Agent:
    """Create the Clinical Trials Analyst agent."""
    from src.tools.clinical_tool import query_clinical_trials, find_repurposing_opportunities, analyze_competition_density
    
    return Agent(
        role="R&D Pipeline Analyst",
        goal="Analyze clinical trial landscapes to identify competition density, repurposing opportunities, and unmet medical needs",
        backstory="""You are a clinical development strategist with expertise in analyzing global clinical trial data.
        You identify emerging therapies, repurposing opportunities, and gaps in the pipeline.
        You understand trial phases (I-IV), can assess competition density, and identify white spaces.
        You focus on finding high-potential indications with low competition and high unmet need.""",
        tools=tools or [query_clinical_trials, find_repurposing_opportunities, analyze_competition_density],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_social_agent(tools: list = None) -> Agent:
    """Create the Social Listening / Patient Voice agent."""
    from src.tools.social_tool import query_social_media, analyze_patient_complaints, get_patient_quotes
    
    return Agent(
        role="Patient Voice Analyst",
        goal="Analyze patient social media posts to understand real-world experiences, complaints, and unmet needs",
        backstory="""You are a qualitative researcher specialized in patient-centered insights.
        You analyze patient forums, social media, and communities to understand the lived experience of patients.
        You identify common complaint themes (needle pain, side effects, cost, convenience) that represent 
        innovation opportunities. You translate patient voices into actionable product recommendations.
        You always include direct patient quotes to support your findings.""",
        tools=tools or [query_social_media, analyze_patient_complaints, get_patient_quotes],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_competitor_agent(tools: list = None) -> Agent:
    """Create the Competitor / War Gamer agent."""
    from src.tools.competitor_tool import query_competitor_intel, war_game_scenario, assess_competitive_threats
    
    return Agent(
        role="Strategic War Gamer",
        goal="Simulate competitor responses and stress-test strategic plans through war gaming scenarios",
        backstory="""You are a competitive intelligence expert who thinks like a competitor.
        You predict how rivals will respond to market moves - price cuts, launches, litigation, etc.
        You run war game simulations to stress-test strategies before execution.
        You always play devil's advocate and identify risks that others might miss.
        You provide counter-strategy recommendations to mitigate competitive threats.""",
        tools=tools or [query_competitor_intel, war_game_scenario, assess_competitive_threats],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_internal_agent(tools: list = None) -> Agent:
    """Create the Internal Knowledge / Corporate Strategist agent."""
    from src.tools.internal_tool import search_internal_docs, get_document_by_id, list_documents_by_tag
    
    return Agent(
        role="Corporate Strategist",
        goal="Search and synthesize internal strategy documents, field reports, and institutional knowledge",
        backstory="""You are a strategy consultant embedded within the organization.
        You have access to all internal strategy decks, field reports, SWOT analyses, and past learnings.
        You connect the dots between external data and internal capabilities.
        You ensure that recommendations align with company strategy and leverage existing assets.
        You cite specific internal documents to support your recommendations.""",
        tools=tools or [search_internal_docs, get_document_by_id, list_documents_by_tag],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_web_agent(tools: list = None) -> Agent:
    """Create the Web Intelligence agent."""
    from src.tools.web_tool import web_search, get_recent_news
    
    return Agent(
        role="External Intelligence Researcher",
        goal="Search the web for recent pharmaceutical news, FDA approvals, competitor announcements, and market developments",
        backstory="""You are a pharmaceutical intelligence analyst who monitors global news and developments.
        You track FDA approvals, EMA decisions, clinical trial results, and competitor press releases.
        You identify emerging trends and breaking news that could impact strategic decisions.
        You always cite sources and provide context for news items.""",
        tools=tools or [web_search, get_recent_news],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )


def create_all_agents() -> dict:
    """Create and return all worker agents as a dictionary."""
    return {
        "iqvia_agent": create_iqvia_agent(),
        "patent_agent": create_patent_agent(),
        "exim_agent": create_exim_agent(),
        "clinical_agent": create_clinical_agent(),
        "social_agent": create_social_agent(),
        "competitor_agent": create_competitor_agent(),
        "internal_agent": create_internal_agent(),
        "web_agent": create_web_agent()
    }
