"""
Master Orchestrator Service
Improved agent coordination with intent-based routing, parallel execution,
and intelligent response synthesis.
"""
import os
import time
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from .intent_classifier import IntentClassifier, IntentResult, AgentType
from .guardrails import GuardrailsService, ValidationResult, ContentModerator
from src.services.groq_client import get_client

load_dotenv()


@dataclass
class AgentResponse:
    """Response from a single agent."""
    agent_type: AgentType
    content: str
    success: bool
    execution_time_ms: int
    data: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class OrchestratedResponse:
    """Final orchestrated response combining all agent outputs."""
    content: str
    agents_used: List[str]
    intent: IntentResult
    individual_responses: List[AgentResponse]
    total_time_ms: int
    was_synthesized: bool


class MasterOrchestrator:
    """
    Orchestrates multiple specialized agents to answer complex pharmaceutical queries.
    Uses LLM-based intent classification and intelligent response synthesis.
    """
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.max_parallel_agents = 4
    
    def process_query(
        self,
        query: str,
        conversation_context: Optional[List[Dict]] = None,
        user_id: Optional[int] = None
    ) -> OrchestratedResponse:
        """
        Process a user query through the full orchestration pipeline.
        
        Args:
            query: User's natural language query
            conversation_context: Recent conversation history for context
            user_id: User identifier for personalization
            
        Returns:
            OrchestratedResponse with synthesized content
        """
        start_time = time.time()
        
        # Step 1: Validate input
        validation = GuardrailsService.validate_input(query)
        if not validation.is_valid:
            return OrchestratedResponse(
                content=validation.message,
                agents_used=["Guardrails"],
                intent=IntentResult(
                    primary_intent="blocked",
                    agents_needed=[],
                    confidence=1.0,
                    entities={},
                    requires_synthesis=False,
                    suggested_followups=[]
                ),
                individual_responses=[],
                total_time_ms=int((time.time() - start_time) * 1000),
                was_synthesized=False
            )
        
        # Use sanitized input
        clean_query = validation.sanitized_input
        
        # Step 2: Classify intent
        intent = self.intent_classifier.classify(clean_query, conversation_context)
        
        # Step 3: Execute appropriate agents
        if intent.requires_synthesis or len(intent.agents_needed) > 1:
            responses = self._execute_parallel(clean_query, intent)
        else:
            responses = self._execute_single(clean_query, intent)
        
        # Step 4: Synthesize responses
        if len(responses) > 1 and intent.requires_synthesis:
            synthesized_content = self._synthesize_responses(clean_query, responses, intent)
            was_synthesized = True
        elif responses:
            synthesized_content = responses[0].content
            was_synthesized = False
        else:
            synthesized_content = "I couldn't find relevant information for your query. Please try rephrasing or ask about a specific topic."
            was_synthesized = False
        
        # Step 5: Apply output guardrails
        filtered_content, output_flags = GuardrailsService.validate_output(synthesized_content)
        
        # Step 6: Add context warnings if needed
        final_content = ContentModerator.add_context_warnings(filtered_content, clean_query)
        
        total_time = int((time.time() - start_time) * 1000)
        
        return OrchestratedResponse(
            content=final_content,
            agents_used=[r.agent_type.value.title() for r in responses if r.success],
            intent=intent,
            individual_responses=responses,
            total_time_ms=total_time,
            was_synthesized=was_synthesized
        )
    
    def _execute_single(self, query: str, intent: IntentResult) -> List[AgentResponse]:
        """Execute a single agent for simple queries."""
        if not intent.agents_needed:
            return [self._execute_general_agent(query, intent)]
        
        agent_type = intent.agents_needed[0]
        response = self._execute_agent(query, agent_type, intent)
        return [response]
    
    def _execute_parallel(self, query: str, intent: IntentResult) -> List[AgentResponse]:
        """Execute multiple agents in parallel."""
        responses = []
        
        with ThreadPoolExecutor(max_workers=self.max_parallel_agents) as executor:
            futures = {
                executor.submit(self._execute_agent, query, agent_type, intent): agent_type
                for agent_type in intent.agents_needed[:self.max_parallel_agents]
            }
            
            for future in as_completed(futures):
                agent_type = futures[future]
                try:
                    response = future.result(timeout=30)
                    responses.append(response)
                except Exception as e:
                    responses.append(AgentResponse(
                        agent_type=agent_type,
                        content="",
                        success=False,
                        execution_time_ms=0,
                        error=str(e)
                    ))
        
        return responses
    
    def _execute_agent(self, query: str, agent_type: AgentType, intent: IntentResult) -> AgentResponse:
        """Execute a specific agent type."""
        start_time = time.time()
        
        try:
            if agent_type == AgentType.MARKET:
                content, data = self._run_market_agent(query, intent)
            elif agent_type == AgentType.PATENT:
                content, data = self._run_patent_agent(query, intent)
            elif agent_type == AgentType.CLINICAL:
                content, data = self._run_clinical_agent(query, intent)
            elif agent_type == AgentType.PATIENT:
                content, data = self._run_patient_agent(query, intent)
            elif agent_type == AgentType.COMPETITOR:
                content, data = self._run_competitor_agent(query, intent)
            elif agent_type == AgentType.TRADE:
                content, data = self._run_trade_agent(query, intent)
            elif agent_type == AgentType.INTERNAL:
                content, data = self._run_internal_agent(query, intent)
            elif agent_type == AgentType.WEB:
                content, data = self._run_web_agent(query, intent)
            else:
                content, data = self._run_general_agent(query, intent)
            
            return AgentResponse(
                agent_type=agent_type,
                content=content,
                success=True,
                execution_time_ms=int((time.time() - start_time) * 1000),
                data=data
            )
            
        except Exception as e:
            return AgentResponse(
                agent_type=agent_type,
                content="",
                success=False,
                execution_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )
    
    def _run_market_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run market analysis agent."""
        from src.tools.iqvia_tool import find_low_competition_markets, query_iqvia_market
        
        entities = intent.entities
        therapy_area = entities.get("therapy_area", "Oncology")
        region = entities.get("region", "India")
        
        # Determine which tool to use based on query
        q = query.lower()
        if any(w in q for w in ["whitespace", "low competition", "opportunity"]):
            result = find_low_competition_markets._run(therapy_area=therapy_area, region=region)
        else:
            result = query_iqvia_market._run(therapy_area=therapy_area)
        
        return result, {"therapy_area": therapy_area, "region": region}
    
    def _run_patent_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run patent analysis agent."""
        from src.tools.patent_tool import check_patent_expiry, query_patents
        
        entities = intent.entities
        molecule = entities.get("molecule", "Rivaroxaban")
        
        q = query.lower()
        if any(w in q for w in ["expiry", "expire", "when"]):
            result = check_patent_expiry._run(molecule=molecule, country="US")
        else:
            result = query_patents._run(molecule=molecule)
        
        return result, {"molecule": molecule}
    
    def _run_clinical_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run clinical trials agent."""
        from src.tools.clinical_tool import find_repurposing_opportunities, query_clinical_trials
        
        entities = intent.entities
        molecule = entities.get("molecule")
        therapy_area = entities.get("therapy_area", "Oncology")
        
        q = query.lower()
        if molecule and any(w in q for w in ["repurpos", "new indication"]):
            result = find_repurposing_opportunities._run(molecule=molecule)
        else:
            result = query_clinical_trials._run(indication=therapy_area)
        
        return result, {"molecule": molecule, "therapy_area": therapy_area}
    
    def _run_patient_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run patient voice agent."""
        from src.tools.social_tool import analyze_patient_complaints
        
        entities = intent.entities
        therapy_area = entities.get("therapy_area", "Diabetes")
        
        result = analyze_patient_complaints._run(therapy_area=therapy_area)
        return result, {"therapy_area": therapy_area}
    
    def _run_competitor_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run competitor intelligence agent."""
        from src.tools.competitor_tool import war_game_scenario
        
        entities = intent.entities
        molecule = entities.get("molecule", "Rivaroxaban")
        
        result = war_game_scenario._run(
            molecule=molecule,
            proposed_strategy="Competitive entry assessment"
        )
        return result, {"molecule": molecule}
    
    def _run_trade_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run trade/supply chain agent."""
        from src.tools.exim_tool import query_trade_data
        
        entities = intent.entities
        molecule = entities.get("molecule", "Metformin")
        
        result = query_trade_data._run(molecule=molecule)
        return result, {"molecule": molecule}
    
    def _run_internal_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run internal documents agent."""
        from src.tools.internal_tool import search_internal_docs
        
        result = search_internal_docs._run(query=query)
        return result, {}
    
    def _run_web_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run web search agent."""
        from src.tools.web_tool import search_pharma_news
        
        result = search_pharma_news._run(query=query)
        return result, {}
    
    def _run_general_agent(self, query: str, intent: IntentResult) -> Tuple[str, Dict]:
        """Run general LLM agent for pharma questions."""
        client = get_client()
        
        system_prompt = """You are a pharmaceutical intelligence expert. Provide accurate, 
helpful information about medications, drug development, and pharmaceutical industry topics.
Be concise but comprehensive. Format with bullet points when appropriate."""

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.3,
            max_tokens=1024
        )
        
        return response.choices[0].message.content, {}
    
    def _execute_general_agent(self, query: str, intent: IntentResult) -> AgentResponse:
        """Execute the general agent."""
        start_time = time.time()
        try:
            content, data = self._run_general_agent(query, intent)
            return AgentResponse(
                agent_type=AgentType.GENERAL,
                content=content,
                success=True,
                execution_time_ms=int((time.time() - start_time) * 1000),
                data=data
            )
        except Exception as e:
            return AgentResponse(
                agent_type=AgentType.GENERAL,
                content=f"Error: {str(e)}",
                success=False,
                execution_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )
    
    def _synthesize_responses(
        self,
        query: str,
        responses: List[AgentResponse],
        intent: IntentResult
    ) -> str:
        """Synthesize multiple agent responses into a coherent answer."""
        from groq import Groq
        
        # Filter successful responses
        successful = [r for r in responses if r.success and r.content]
        
        if not successful:
            return "I couldn't gather sufficient information to answer your query."
        
        if len(successful) == 1:
            return successful[0].content
        
        # Build context from all responses
        context_parts = []
        for r in successful:
            context_parts.append(f"### {r.agent_type.value.title()} Analysis:\n{r.content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Use LLM to synthesize
        client = get_client()
        
        system_prompt = """You are a pharmaceutical strategy synthesizer. Your task is to combine 
multiple specialist analyses into a coherent, actionable executive summary.

Guidelines:
1. Identify key insights from each source
2. Highlight connections and patterns across analyses
3. Resolve any conflicting information
4. Provide clear strategic recommendations
5. Note any gaps or areas needing further investigation

Format your response as:
## Executive Summary
[2-3 sentence overview]

## Key Findings
[Bullet points of most important insights]

## Strategic Recommendations
[Numbered actionable recommendations]

## Risk Factors
[Key risks to consider]

## Next Steps
[Suggested follow-up actions]"""

        user_message = f"""Original Query: {query}

Specialist Analyses:
{context}

Please synthesize these analyses into a unified strategic response."""

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=2048
        )
        
        return response.choices[0].message.content


# Convenience function
def orchestrate_query(
    query: str,
    context: Optional[List[Dict]] = None,
    user_id: Optional[int] = None
) -> OrchestratedResponse:
    """Process a query through the orchestrator."""
    orchestrator = MasterOrchestrator()
    return orchestrator.process_query(query, context, user_id)
