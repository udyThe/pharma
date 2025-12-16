"""
Master Agent / Orchestrator
Hierarchical CrewAI orchestration for pharmaceutical intelligence.
"""
from crewai import Agent, Crew, Task, Process, LLM
import os
from dotenv import load_dotenv

from .worker_agents import (
    create_iqvia_agent,
    create_patent_agent,
    create_exim_agent,
    create_clinical_agent,
    create_social_agent,
    create_competitor_agent,
    create_internal_agent,
    create_web_agent
)

# Load environment
load_dotenv()


def get_manager_llm():
    """Get the manager LLM for hierarchical orchestration."""
    return LLM(
        model=f"groq/{os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2
    )


def create_master_agent() -> Agent:
    """Create the Master Orchestrator agent."""
    return Agent(
        role="Pharma Strategy Orchestrator",
        goal="Orchestrate specialized agents to answer complex pharmaceutical strategy questions comprehensively",
        backstory="""You are the Chief Strategy Officer's right hand, responsible for orchestrating 
        multiple specialist teams to answer strategic questions. You understand how to decompose 
        complex queries into sub-tasks, assign them to the right specialists, and synthesize their 
        findings into actionable executive summaries. You ensure no stone is left unturned and 
        all relevant data sources are consulted. You present findings clearly with strategic recommendations.""",
        llm=get_manager_llm(),
        verbose=True,
        allow_delegation=True
    )


def classify_intent(query: str) -> list:
    """
    Classify user query intent to determine which agents are needed.
    
    Returns a list of agent types needed for this query.
    """
    query_lower = query.lower()
    agents_needed = []
    
    # Market/Whitespace analysis
    if any(word in query_lower for word in ["market", "size", "growth", "cagr", "whitespace", "opportunity", "competition level"]):
        agents_needed.append("iqvia")
    
    # Patent/FTO analysis
    if any(word in query_lower for word in ["patent", "expiry", "fto", "freedom to operate", "generic", "ip"]):
        agents_needed.append("patent")
    
    # Supply chain/Trade
    if any(word in query_lower for word in ["import", "export", "trade", "supply", "source", "api", "pricing"]):
        agents_needed.append("exim")
    
    # Clinical trials/Pipeline
    if any(word in query_lower for word in ["trial", "clinical", "phase", "pipeline", "repurpos", "indication"]):
        agents_needed.append("clinical")
    
    # Patient voice/Social
    if any(word in query_lower for word in ["patient", "complaint", "sentiment", "forum", "social", "voice", "injectable"]):
        agents_needed.append("social")
    
    # Competitor/War gaming
    if any(word in query_lower for word in ["competitor", "war game", "simulate", "launch", "threat", "counter"]):
        agents_needed.append("competitor")
    
    # Internal knowledge
    if any(word in query_lower for word in ["internal", "strategy", "swot", "field report", "our"]):
        agents_needed.append("internal")
    
    # Web/News
    if any(word in query_lower for word in ["news", "recent", "approval", "fda", "announcement"]):
        agents_needed.append("web")
    
    # Default: If no specific intent matched, use core agents
    if not agents_needed:
        agents_needed = ["iqvia", "patent", "clinical"]
    
    return agents_needed


def create_task_for_query(query: str, agent_type: str, agent: Agent) -> Task:
    """Create a task for a specific agent based on the query."""
    
    task_descriptions = {
        "iqvia": f"""Analyze market data related to this query: {query}
        
        Provide:
        1. Relevant market size and growth data
        2. Competition levels and top competitors
        3. Patient burden and unmet need indicators
        4. Whitespace opportunities if applicable
        
        Be specific with numbers and cite the data source.""",
        
        "patent": f"""Analyze patent landscape related to this query: {query}
        
        Provide:
        1. Relevant patent expiry dates
        2. Freedom to Operate (FTO) assessment
        3. Generic entry feasibility
        4. IP risks and recommendations
        
        Include specific patent numbers and dates.""",
        
        "exim": f"""Analyze trade and supply chain data related to this query: {query}
        
        Provide:
        1. Import/export volumes and trends
        2. Major source countries
        3. Pricing information
        4. Supply chain risks and recommendations""",
        
        "clinical": f"""Analyze clinical trial landscape related to this query: {query}
        
        Provide:
        1. Active trials and phases
        2. Competition density
        3. Repurposing opportunities
        4. Unmet medical needs""",
        
        "social": f"""Analyze patient voice data related to this query: {query}
        
        Provide:
        1. Patient sentiment analysis
        2. Key complaint themes
        3. Direct patient quotes
        4. Innovation opportunities based on patient needs""",
        
        "competitor": f"""Analyze competitive landscape related to this query: {query}
        
        Provide:
        1. Competitor strategies and likely moves
        2. Threat assessment
        3. War game simulation if applicable
        4. Counter-strategy recommendations""",
        
        "internal": f"""Search internal documents related to this query: {query}
        
        Provide:
        1. Relevant internal strategy insights
        2. Past field reports and learnings
        3. Company capabilities that apply
        4. Alignment with corporate strategy""",
        
        "web": f"""Search for recent news related to this query: {query}
        
        Provide:
        1. Recent FDA/regulatory news
        2. Competitor announcements
        3. Market developments
        4. Emerging trends"""
    }
    
    return Task(
        description=task_descriptions.get(agent_type, f"Analyze: {query}"),
        expected_output="Detailed analysis with specific data points, insights, and recommendations",
        agent=agent
    )


def create_synthesis_task(query: str, master_agent: Agent) -> Task:
    """Create the final synthesis task for the master agent."""
    return Task(
        description=f"""Synthesize all the specialist analyses to answer this strategic question:
        
        ORIGINAL QUERY: {query}
        
        Your task:
        1. Review all specialist inputs
        2. Identify key insights and patterns
        3. Resolve any conflicting information
        4. Provide a unified strategic recommendation
        5. Highlight risks and opportunities
        6. Suggest next steps
        
        Format your response as an executive summary with:
        - Key Findings (bullet points)
        - Strategic Recommendation
        - Risk Assessment
        - Next Steps""",
        expected_output="""A comprehensive executive summary that synthesizes all specialist analyses 
        into actionable strategic recommendations with clear next steps.""",
        agent=master_agent
    )


def create_master_crew(query: str) -> Crew:
    """
    Create a hierarchical crew to answer a pharmaceutical strategy query.
    
    Args:
        query: The user's natural language question
    
    Returns:
        Configured Crew ready to execute
    """
    # Classify intent to determine which agents are needed
    agents_needed = classify_intent(query)
    
    # Create agent instances
    agent_creators = {
        "iqvia": create_iqvia_agent,
        "patent": create_patent_agent,
        "exim": create_exim_agent,
        "clinical": create_clinical_agent,
        "social": create_social_agent,
        "competitor": create_competitor_agent,
        "internal": create_internal_agent,
        "web": create_web_agent
    }
    
    agents = []
    tasks = []
    
    for agent_type in agents_needed:
        if agent_type in agent_creators:
            agent = agent_creators[agent_type]()
            agents.append(agent)
            task = create_task_for_query(query, agent_type, agent)
            tasks.append(task)
    
    # Create master agent
    master_agent = create_master_agent()
    
    # Add synthesis task
    synthesis_task = create_synthesis_task(query, master_agent)
    tasks.append(synthesis_task)
    agents.append(master_agent)
    
    # Create hierarchical crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.hierarchical,
        manager_llm=get_manager_llm(),
        verbose=True
    )
    
    return crew


def run_query(query: str) -> str:
    """
    Execute a pharmaceutical strategy query through the multi-agent system.
    
    Args:
        query: Natural language question
    
    Returns:
        Synthesized response from the agent crew
    """
    crew = create_master_crew(query)
    result = crew.kickoff()
    return str(result)


# Example golden tasks for testing
GOLDEN_TASKS = {
    "whitespace": "Which respiratory diseases show low competition but high patient burden in India?",
    "repurposing": "Identify potential repurposing opportunities for Pembrolizumab.",
    "fto_check": "Check patent expiry for Sitagliptin in the US.",
    "patient_voice": "What are patients complaining about regarding current Diabetes injectables?",
    "war_game": "Simulate a launch of generic Rivaroxaban in 2025. What will competitors do?"
}
