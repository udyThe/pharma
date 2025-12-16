"""
Pharma Agentic AI - Streamlit Frontend
Professional chat interface with authentication, conversation memory, and rate limiting.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import os
import time
import httpx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Initialize database on first import
try:
    from src.database.db import init_database
    init_database()
except Exception:
    pass

# Page config
st.set_page_config(
    page_title="Pharma Agentic AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #718096;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 8px;
    }
    .agent-tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 2px;
        background: #e2e8f0;
        color: #2d3748;
    }
    .status-bar {
        background: linear-gradient(90deg, #1a365d 0%, #2b6cb0 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    div[data-testid="stSidebar"] {
        background-color: #f8fafc;
    }
    .footer {
        text-align: center;
        color: #a0aec0;
        font-size: 0.8rem;
        padding: 1rem 0;
    }
    .user-badge {
        background: #48bb78;
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.8rem;
    }
    .rate-limit-bar {
        background: #edf2f7;
        border-radius: 4px;
        height: 6px;
        margin-top: 4px;
    }
    .rate-limit-fill {
        background: #4299e1;
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s;
    }
    .error-box {
        background: #fed7d7;
        border: 1px solid #fc8181;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    .success-box {
        background: #c6f6d5;
        border: 1px solid #68d391;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    .history-item {
        padding: 8px 12px;
        border-radius: 6px;
        margin: 4px 0;
        cursor: pointer;
        border: 1px solid #e2e8f0;
    }
    .history-item:hover {
        background: #edf2f7;
    }
</style>
""", unsafe_allow_html=True)


def init_session():
    """Initialize session state."""
    defaults = {
        "messages": [],
        "last_response": None,
        "last_agents": [],
        "last_query": "",
        # Auth
        "logged_in": False,
        "user": None,
        "session_token": None,
        # Conversation
        "conversation_id": None,
        "show_history": False,
        # UI state
        "show_login": True,
        "error_message": None,
        "success_message": None,
        # Async jobs
        "job_status": None,
        "job_polling": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def show_error(message: str):
    """Display error message."""
    st.markdown(f'<div class="error-box">❌ {message}</div>', unsafe_allow_html=True)


def show_success(message: str):
    """Display success message."""
    st.markdown(f'<div class="success-box">✅ {message}</div>', unsafe_allow_html=True)


def login_page():
    """Render login/register page."""
    st.markdown('<p class="main-header">💊 Pharma Agentic AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Agent Intelligence for Pharmaceutical Strategy</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "👤 Demo"])
        
        with tab1:
            st.markdown("### Sign In")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if username and password:
                    try:
                        from src.services.auth import AuthService
                        token, user_info, message = AuthService.login(username, password)
                        
                        if token:
                            st.session_state.logged_in = True
                            st.session_state.user = user_info
                            st.session_state.session_token = token
                            
                            # Load most recent conversation
                            try:
                                from src.services.conversation import ConversationService
                                conversations = ConversationService.get_user_conversations(user_info["id"], limit=1)
                                if conversations:
                                    recent = ConversationService.get_conversation(conversations[0]["id"])
                                    if recent and recent["messages"]:
                                        st.session_state.conversation_id = recent["id"]
                                        st.session_state.messages = [
                                            {"role": m["role"], "content": m["content"], "agents": m.get("agents", [])}
                                            for m in recent["messages"]
                                        ]
                            except Exception:
                                pass  # Start fresh if loading fails
                            
                            st.rerun()
                        else:
                            show_error(message)
                    except Exception as e:
                        show_error(f"Login failed: {str(e)}")
                else:
                    show_error("Please enter username and password")
        
        with tab2:
            st.markdown("### Create Account")
            new_username = st.text_input("Username", key="reg_username")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            if st.button("Register", use_container_width=True):
                if new_password != confirm_password:
                    show_error("Passwords don't match")
                elif not all([new_username, new_email, new_password]):
                    show_error("Please fill all fields")
                else:
                    try:
                        from src.services.auth import AuthService
                        success, message = AuthService.register(new_username, new_email, new_password)
                        
                        if success:
                            show_success(message + " Please login.")
                        else:
                            show_error(message)
                    except Exception as e:
                        show_error(f"Registration failed: {str(e)}")
        
        with tab3:
            st.markdown("### Quick Demo Access")
            st.info("Try the system without creating an account")
            
            demo_accounts = [
                ("demo", "demo", "Analyst"),
                ("analyst", "analyst123", "Analyst"),
                ("manager", "manager123", "Manager"),
            ]
            
            for username, password, role in demo_accounts:
                if st.button(f"Login as {role} ({username})", key=f"demo_{username}", use_container_width=True):
                    try:
                        from src.services.auth import AuthService
                        token, user_info, message = AuthService.login(username, password)
                        
                        if token:
                            st.session_state.logged_in = True
                            st.session_state.user = user_info
                            st.session_state.session_token = token
                            
                            # Load most recent conversation
                            try:
                                from src.services.conversation import ConversationService
                                conversations = ConversationService.get_user_conversations(user_info["id"], limit=1)
                                if conversations:
                                    recent = ConversationService.get_conversation(conversations[0]["id"])
                                    if recent and recent["messages"]:
                                        st.session_state.conversation_id = recent["id"]
                                        st.session_state.messages = [
                                            {"role": m["role"], "content": m["content"], "agents": m.get("agents", [])}
                                            for m in recent["messages"]
                                        ]
                            except Exception:
                                pass  # Start fresh if loading fails
                            
                            st.rerun()
                        else:
                            show_error(f"Demo login failed: {message}")
                    except Exception as e:
                        show_error(f"Demo login failed: {str(e)}")


def sidebar():
    """Render sidebar."""
    with st.sidebar:
        # User info
        if st.session_state.logged_in and st.session_state.user:
            user = st.session_state.user
            st.markdown(f"**👤 {user['username']}**")
            st.caption(f"Role: {user['role'].title()}")
            
            # ===== LOGOUT DISABLED =====
            # if st.button("🚪 Logout", use_container_width=True):
            #     try:
            #         from src.services.auth import AuthService
            #         AuthService.logout(st.session_state.session_token)
            #     except:
            #         pass
            #     st.session_state.logged_in = False
            #     st.session_state.user = None
            #     st.session_state.session_token = None
            #     st.session_state.messages = []
            #     st.session_state.conversation_id = None
            #     st.rerun()
            # ===== END LOGOUT DISABLED =====
            
            st.markdown("---")
        
        # Conversation history
        st.markdown("### 💬 Conversations")
        
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.session_state.last_response = None
            st.rerun()
        
        # Show recent conversations
        if st.session_state.logged_in and st.session_state.user:
            try:
                from src.services.conversation import ConversationService
                user_id = st.session_state.user["id"]
                conversations = ConversationService.get_user_conversations(user_id, limit=10)
                
                for conv in conversations:
                    title = conv["title"][:25] + "..." if len(conv["title"]) > 25 else conv["title"]
                    
                    # Create columns for conversation button and delete button
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        if st.button(f"📄 {title}", key=f"conv_{conv['id']}", use_container_width=True):
                            # Load conversation
                            full_conv = ConversationService.get_conversation(conv["id"])
                            if full_conv:
                                st.session_state.conversation_id = conv["id"]
                                st.session_state.messages = [
                                    {"role": m["role"], "content": m["content"], "agents": m.get("agents", [])}
                                    for m in full_conv["messages"]
                                ]
                                st.rerun()
                    
                    with col2:
                        if st.button("🗑️", key=f"del_{conv['id']}", help="Delete conversation"):
                            # Delete conversation
                            if ConversationService.delete_conversation(conv["id"]):
                                # Clear current conversation if it's the deleted one
                                if st.session_state.conversation_id == conv["id"]:
                                    st.session_state.conversation_id = None
                                    st.session_state.messages = []
                                st.rerun()
            except Exception as e:
                st.caption(f"Could not load history")
        
        st.markdown("---")
        
        # Agents info
        st.markdown("### 🤖 Agents")
        agents_info = [
            ("📊 Market", "IQVIA data, market size"),
            ("📜 Patent", "IP landscape, expiry"),
            ("🚢 Trade", "Import/export data"),
            ("🔬 Clinical", "Trials, pipeline"),
            ("💬 Patient", "Sentiment, complaints"),
            ("⚔️ Competitor", "War gaming"),
            ("📁 Internal", "Strategy docs"),
            ("🌐 Web", "Real-time news"),
            ("🤖 AI", "General knowledge"),
        ]
        for name, desc in agents_info:
            st.caption(f"**{name}** — {desc}")
        
        st.markdown("---")
        
        # ===== API USAGE SECTION REMOVED =====
        # Rate limit status
        # st.markdown("### 📊 API Usage")
        # try:
        #     from src.services.rate_limiter import RateLimiter
        #     stats = RateLimiter.get_usage_stats()
        #     
        #     for api, data in stats.items():
        #         used = data.get("global_calls", 0)
        #         limit = data.get("global_limit", 100)
        #         pct = min(100, int((used / limit) * 100)) if limit > 0 else 0
        #         color = "#48bb78" if pct < 70 else "#ecc94b" if pct < 90 else "#fc8181"
        #         
        #         st.caption(f"**{api.title()}**: {used}/{limit}")
        #         st.markdown(
        #             f'<div class="rate-limit-bar"><div class="rate-limit-fill" style="width:{pct}%;background:{color}"></div></div>',
        #             unsafe_allow_html=True
        #         )
        # except:
        #     st.caption("Rate limiting active")
        # ===== END API USAGE SECTION =====
        
        st.markdown("---")
        
        # Quick examples
        st.markdown("### 💡 Quick Examples")
        
        examples = [
            ("Whitespace", "Which respiratory diseases show low competition?"),
            ("Patent", "Check patent expiry for Sitagliptin"),
            ("Patient", "What are patients saying about injectables?"),
            ("War Game", "Simulate generic Rivaroxaban launch"),
        ]
        
        for label, query in examples:
            if st.button(label, key=f"ex_{label}", use_container_width=True):
                st.session_state.pending_query = query


def header():
    """Render header."""
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<p class="main-header">💊 Pharma Agentic AI</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Multi-Agent Intelligence for Pharmaceutical Strategy</p>', unsafe_allow_html=True)
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_response = None
            st.session_state.last_agents = []
            st.session_state.conversation_id = None
            st.rerun()


def search_web(query: str) -> str:
    """Search the web using Tavily for real-time information."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Check rate limit
    try:
        from src.services.rate_limiter import RateLimiter, RateLimitExceeded
        user_id = st.session_state.user["id"] if st.session_state.user else None
        allowed, current, limit = RateLimiter.check_limit("tavily", user_id)
        
        if not allowed:
            return f"⚠️ Rate limit reached ({current}/{limit} calls today). Try again tomorrow."
    except:
        pass
    
    try:
        from tavily import TavilyClient
        
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )
        
        # Record usage
        try:
            from src.services.rate_limiter import RateLimiter
            user_id = st.session_state.user["id"] if st.session_state.user else None
            RateLimiter.record_usage("tavily", user_id)
        except:
            pass
        
        results = []
        
        if response.get("answer"):
            results.append(f"**Summary:** {response['answer']}\n")
        
        if response.get("results"):
            results.append("**Sources:**")
            for r in response["results"][:5]:
                title = r.get("title", "No title")
                url = r.get("url", "")
                snippet = r.get("content", "")[:200]
                results.append(f"- **{title}**\n  {snippet}...\n  [Link]({url})")
        
        return "\n".join(results) if results else None
        
    except Exception as e:
        return None


def run_demo_query(query: str) -> tuple:
    """Run query using intelligent orchestrator with guardrails and intent classification."""
    try:
        # Import new services
        from src.services.guardrails import GuardrailsService
        from src.services.intent_classifier import IntentClassifier
        from src.services.rag_service import get_rag_context
        
        # Initialize services
        guardrails = GuardrailsService()
        
        # Step 1: Apply guardrails
        is_safe, safety_result = guardrails.validate_query(query)
        
        if not is_safe:
            return f"⚠️ **Query Not Allowed**\n\n{safety_result.get('reason', 'This query cannot be processed.')}\n\n*Please rephrase your question to focus on legitimate pharmaceutical business intelligence.*", ["Guardrails"]
        
        # Get sanitized query
        clean_query = guardrails.sanitize_input(query)
        
        # Step 2: Classify intent
        intent_classifier = IntentClassifier()
        intent_result = intent_classifier.classify_intent(clean_query)
        
        # Step 3: Get RAG context for relevant queries
        rag_context = ""
        if intent_result.intent_type.value in ["internal", "general"]:
            rag_context = get_rag_context(clean_query, max_tokens=1500)
        
        # Step 4: Route to appropriate tools based on intent
        responses = []
        agents_used = []
        
        intent_type = intent_result.intent_type.value
        entities = intent_result.entities
        
        # Market/Whitespace queries
        if intent_type == "market" or intent_result.confidence < 0.6:
            try:
                from src.tools.iqvia_tool import find_low_competition_markets, query_iqvia_market
                # Get entities from intent if available, otherwise let tool extract from query
                therapy_area = entities.get("therapy_areas", [None])[0] if entities.get("therapy_areas") else None
                region = entities.get("regions", [None])[0] if entities.get("regions") else None
                
                if "whitespace" in clean_query.lower() or "competition" in clean_query.lower():
                    responses.append(find_low_competition_markets._run(therapy_area=therapy_area, region=region, query=clean_query))
                else:
                    responses.append(query_iqvia_market._run(therapy_area=therapy_area, query=clean_query))
                agents_used.append("Market Analyst")
            except Exception as e:
                pass
        
        # Patent queries
        if intent_type == "patent":
            try:
                from src.tools.patent_tool import check_patent_expiry, query_patents
                # Get molecule from entities if available, otherwise pass None to let tool extract from query
                molecule = entities.get("molecules", [None])[0] if entities.get("molecules") else None
                
                if "expiry" in clean_query.lower() or "expire" in clean_query.lower():
                    responses.append(check_patent_expiry._run(molecule=molecule, country="US", query=clean_query))
                else:
                    responses.append(query_patents._run(molecule=molecule, query=clean_query))
                agents_used.append("Patent Analyst")
            except Exception as e:
                pass
        
        # Clinical/Trial queries
        if intent_type == "clinical":
            try:
                from src.tools.clinical_tool import find_repurposing_opportunities, query_clinical_trials
                molecule = entities.get("molecules", [None])[0] if entities.get("molecules") else None
                therapy_area = entities.get("therapy_areas", [None])[0] if entities.get("therapy_areas") else None
                
                if "repurpos" in clean_query.lower() and molecule:
                    responses.append(find_repurposing_opportunities._run(molecule=molecule, query=clean_query))
                else:
                    responses.append(query_clinical_trials._run(indication=therapy_area, query=clean_query))
                agents_used.append("Clinical Research")
            except Exception as e:
                pass
        
        # Patient voice queries
        if intent_type == "patient":
            try:
                from src.tools.social_tool import analyze_patient_complaints
                therapy_area = entities.get("therapy_areas", [None])[0] if entities.get("therapy_areas") else None
                responses.append(analyze_patient_complaints._run(therapy_area=therapy_area, query=clean_query))
                agents_used.append("Patient Voice")
            except Exception as e:
                pass
        
        # Competitor queries
        if intent_type == "competitor":
            try:
                from src.tools.competitor_tool import war_game_scenario, get_competitor_strategy
                # Get molecule/company from entities if available, otherwise let tool extract from query
                molecule = entities.get("molecules", [None])[0] if entities.get("molecules") else None
                company = entities.get("companies", [None])[0] if entities.get("companies") else None
                
                if "war game" in clean_query.lower() or "simulate" in clean_query.lower():
                    responses.append(war_game_scenario._run(molecule=molecule, proposed_strategy="Market entry", query=clean_query))
                elif company:
                    responses.append(get_competitor_strategy._run(company=company, query=clean_query))
                else:
                    responses.append(war_game_scenario._run(molecule=molecule, proposed_strategy="Competitive analysis", query=clean_query))
                agents_used.append("Competitor Intel")
            except Exception as e:
                pass
        
        # Trade queries
        if intent_type == "trade":
            try:
                from src.tools.exim_tool import query_exim_trade
                molecule = entities.get("molecules", [None])[0] if entities.get("molecules") else None
                responses.append(query_exim_trade._run(molecule=molecule, query=clean_query))
                agents_used.append("Trade Analyst")
            except Exception as e:
                pass
        
        # Internal document queries
        if intent_type == "internal":
            try:
                from src.tools.internal_tool import search_internal_docs
                responses.append(search_internal_docs._run(query=clean_query))
                agents_used.append("Internal Docs")
            except Exception as e:
                pass
        
        # Web search for current/news queries
        if intent_type == "web" or "latest" in clean_query.lower() or "news" in clean_query.lower():
            web_result = search_web(clean_query)
            if web_result:
                responses.append(web_result)
                agents_used.append("Web Search")
        
        # If we have tool responses, synthesize them
        if responses:
            # Combine responses
            combined = "\n\n---\n\n".join(responses)
            
            # Add RAG context if available
            if rag_context:
                combined = f"{combined}\n\n---\n\n**Additional Context from Internal Documents:**\n{rag_context}"
            
            # Filter response through guardrails
            filtered = guardrails.filter_response(combined)
            
            return filtered, agents_used
        
        # Fallback to LLM with RAG context
        return ask_llm_with_context(clean_query, rag_context, intent_result)
            
    except Exception as e:
        import traceback
        error_detail = str(e)[:200]
        return f"⚠️ **Something went wrong**\n\nI encountered an issue processing your request. Please try:\n- Rephrasing your question\n- Being more specific about the molecule or therapy area\n\n*Technical details: {error_detail}*", ["System"]


def ask_llm_with_context(query: str, rag_context: str = "", intent_result = None) -> tuple:
    """Use Groq LLM with RAG context and intent information."""
    import os
    from groq import Groq
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Check rate limit
    try:
        from src.services.rate_limiter import RateLimiter
        user_id = st.session_state.user["id"] if st.session_state.user else None
        allowed, current, limit = RateLimiter.check_limit("groq", user_id)
        
        if not allowed:
            return f"⚠️ **Rate limit reached** ({current}/{limit} calls today)\n\nYour daily API quota has been reached. Please try again tomorrow.", []
    except:
        pass
    
    try:
        # Get web context for current events
        web_context = ""
        if any(w in query.lower() for w in ["latest", "recent", "news", "2024", "2025", "fda", "approval"]):
            web_context = search_web(query) or ""
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Build enhanced system prompt
        system_prompt = """You are an expert pharmaceutical intelligence assistant with deep knowledge of:
- Drug development and clinical trials
- Patent landscapes and IP strategy
- Market dynamics and competitive intelligence
- Regulatory affairs (FDA, EMA, etc.)
- Healthcare economics and pricing
- Patient outcomes and real-world evidence

You have access to internal company documents and market data to provide accurate, actionable insights.

Guidelines:
1. Be concise but comprehensive
2. Use bullet points and clear formatting
3. Include relevant data points and metrics when available
4. Cite sources when referencing specific information
5. Provide strategic recommendations when appropriate
6. Always include appropriate disclaimers for medical/clinical information
7. If referring to previous context, use conversation history to understand references"""

        # Add intent context if available
        if intent_result:
            entities_str = ", ".join([f"{k}: {v}" for k, v in intent_result.entities.items() if v])
            system_prompt += f"\n\nThe user's query is about: {intent_result.intent_type.value}"
            if entities_str:
                system_prompt += f"\nKey entities mentioned: {entities_str}"
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if st.session_state.messages:
            for msg in st.session_state.messages[-6:]:
                role = "user" if msg["role"] == "user" else "assistant"
                content = msg["content"][:800] + "..." if len(msg["content"]) > 800 else msg["content"]
                messages.append({"role": role, "content": content})
        
        # Build user message with context
        user_message = f"Question: {query}"
        
        agents = ["AI Assistant"]
        
        if rag_context:
            user_message += f"\n\n{rag_context}"
            agents.append("Internal Docs")
        
        if web_context:
            user_message += f"\n\n## Recent Web Information:\n{web_context}"
            agents.append("Web Search")
        
        user_message += "\n\nPlease provide a comprehensive, well-structured answer."
        
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=messages,
            temperature=0.3,
            max_tokens=2048
        )
        
        # Record usage
        try:
            from src.services.rate_limiter import RateLimiter
            user_id = st.session_state.user["id"] if st.session_state.user else None
            RateLimiter.record_usage("groq", user_id)
        except:
            pass
        
        answer = response.choices[0].message.content
        
        # Filter through guardrails
        try:
            from src.services.guardrails import GuardrailsService
            guardrails = GuardrailsService()
            answer = guardrails.filter_response(answer)
        except:
            pass
        
        return answer, agents
        
    except Exception as e:
        error_msg = str(e)
        if "rate" in error_msg.lower() or "limit" in error_msg.lower():
            return f"⚠️ **API Rate Limited**\n\nThe AI service is temporarily unavailable. Please wait a moment and try again.", []
        return f"⚠️ **Service Unavailable**\n\nI couldn't connect to the AI service. Please try again.\n\n*Error: {error_msg[:100]}*", []


def export_report(format_type: str) -> tuple:
    """Export last response as PDF or Excel and return (file_path, file_bytes, filename)."""
    if not st.session_state.last_response:
        return None, None, None
    
    try:
        if format_type == "PDF":
            from src.services.report_generator import generate_pdf_report
            path = generate_pdf_report(
                title="Pharma Strategy Analysis",
                query=st.session_state.last_query or "Analysis Report",
                content=st.session_state.last_response,
                metadata={
                    "agents_used": st.session_state.last_agents,
                    "user": st.session_state.user.get("username", "anonymous") if st.session_state.user else "anonymous"
                }
            )
            if path and not path.startswith("Error"):
                with open(path, "rb") as f:
                    file_bytes = f.read()
                return path, file_bytes, Path(path).name
            return None, None, None
        else:
            from src.services.report_generator import generate_excel_report
            # Parse response into structured data
            lines = st.session_state.last_response.split("\n")
            findings = []
            recommendations = []
            current_section = "findings"
            
            for line in lines:
                line = line.strip()
                if "recommendation" in line.lower():
                    current_section = "recommendations"
                elif line.startswith("- ") or line.startswith("• "):
                    text = line[2:].strip()
                    if current_section == "findings":
                        findings.append(text)
                    else:
                        recommendations.append(text)
                elif line.startswith("* "):
                    text = line[2:].strip()
                    if current_section == "findings":
                        findings.append(text)
                    else:
                        recommendations.append(text)
            
            # If no bullets found, split by sentences
            if not findings:
                import re
                sentences = re.split(r'[.!?]\s+', st.session_state.last_response)
                findings = [s.strip() for s in sentences if len(s.strip()) > 20][:15]
            
            path = generate_excel_report(
                title="Pharma Strategy Analysis",
                query=st.session_state.last_query or "Analysis Report",
                data={
                    "findings": findings[:20],
                    "recommendations": recommendations[:10] if recommendations else ["See findings for detailed analysis"]
                },
                metadata={
                    "agents_used": st.session_state.last_agents,
                    "user": st.session_state.user.get("username", "anonymous") if st.session_state.user else "anonymous"
                }
            )
            if path and not path.startswith("Error"):
                with open(path, "rb") as f:
                    file_bytes = f.read()
                return path, file_bytes, Path(path).name
            return None, None, None
    except Exception as e:
        st.error(f"Export failed: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None, None, None


def process_message(query: str):
    """Process a user message."""
    start_time = time.time()
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Save to database if logged in
    if st.session_state.logged_in and st.session_state.user:
        try:
            from src.services.conversation import ConversationService
            user_id = st.session_state.user["id"]
            
            # Create new conversation if needed
            if not st.session_state.conversation_id:
                st.session_state.conversation_id = ConversationService.create_conversation(user_id)
            
            # Save message
            ConversationService.add_message(st.session_state.conversation_id, "user", query)
        except Exception:
            pass
    
    # Check if user is asking to export a report (not trade/export data)
    q_lower = query.lower()
    # Use specific phrases to avoid matching "export data" queries meant for EXIM tool
    export_phrases = [
        "export as", "export to", "export report", "export the", "export this",
        "download pdf", "download excel", "download report", "download the", "download this",
        "generate report", "generate pdf", "generate excel",
        "create pdf", "create excel", "create report",
        "save as", "save to", "save report", "save the", "save this"
    ]
    if any(phrase in q_lower for phrase in export_phrases):
        if "pdf" in q_lower:
            path, file_bytes, filename = export_report("PDF")
            if path and file_bytes:
                response = f"✅ **PDF Report Ready!**\n\nUse the **Download PDF** button below to save your report.\n\n📁 File: `{filename}`"
            else:
                response = "❌ No analysis available to export. Ask a question first, then you can export it."
        elif "excel" in q_lower:
            path, file_bytes, filename = export_report("Excel")
            if path and file_bytes:
                response = f"✅ **Excel Report Ready!**\n\nUse the **Download Excel** button below to save your report.\n\n📁 File: `{filename}`"
            else:
                response = "❌ No analysis available to export. Ask a question first, then you can export it."
        else:
            response = "📄 **Export Options:**\n\nUse the download buttons at the bottom of the chat to export your analysis:\n\n- **📥 Download PDF** - Professional PDF report\n- **📊 Download Excel** - Spreadsheet with structured data\n\n*Or say 'export as PDF' or 'export as Excel'*"
        
        st.session_state.messages.append({"role": "assistant", "content": response, "agents": []})
        return
    
    # Run the query via async API if enabled, otherwise fallback
    success = True
    error_msg = None
    response = ""
    agents_used = []
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")

    use_async = os.getenv("USE_ASYNC_QUEUE", "false").lower() == "true"

    if use_async:
        try:
            with st.spinner("🚀 Sending to orchestrator..."):
                with httpx.Client(timeout=5.0) as client:
                    submit = client.post(f"{api_base}/jobs", json={"query": query, "context": {}})
                    submit.raise_for_status()
                    job_id = submit.json()["job_id"]

                # Poll for completion
                poll_start = time.time()
                backoff = 1.0
                while True:
                    with httpx.Client(timeout=5.0) as client:
                        res = client.get(f"{api_base}/jobs/{job_id}")
                        if res.status_code == 404:
                            raise RuntimeError("Job not found after submission.")
                        res.raise_for_status()
                        payload = res.json()
                        status = payload.get("status")
                        if status in ("done", "failed"):
                            if status == "done":
                                response = payload.get("result", "")
                                agents_used = ["Orchestrator"]
                            else:
                                success = False
                                error_msg = payload.get("error", "Job failed")
                                response = f"⚠️ Job failed: {error_msg}"
                            break
                    if time.time() - poll_start > 60:
                        success = False
                        error_msg = "Job timed out"
                        response = "⚠️ The job is taking too long. Please try again later."
                        break
                    time.sleep(backoff)
                    backoff = min(5.0, backoff + 0.5)
        except Exception:
            # Fallback to local execution
            try:
                response, agents_used = run_demo_query(query)
            except Exception as e:
                success = False
                error_msg = str(e)
                response = f"⚠️ An error occurred: {str(e)}"
                agents_used = ["System"]
    else:
        # Synchronous local path
        try:
            response, agents_used = run_demo_query(query)
        except Exception as e:
            success = False
            error_msg = str(e)
            response = f"⚠️ An error occurred: {str(e)}"
            agents_used = ["System"]
    
    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Track query for analytics
    try:
        from src.services.query_tracker import QueryTracker
        user_id = st.session_state.user["id"] if st.session_state.user else None
        QueryTracker.log_query(
            query_text=query,
            agents_used=agents_used,
            user_id=user_id,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_msg
        )
    except Exception:
        pass  # Don't fail if tracking fails
    
    # Store response for potential export
    st.session_state.last_response = response
    st.session_state.last_agents = agents_used
    st.session_state.last_query = query
    
    # Add assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "agents": agents_used
    })
    
    # Save to database
    if st.session_state.logged_in and st.session_state.conversation_id:
        try:
            from src.services.conversation import ConversationService
            ConversationService.add_message(st.session_state.conversation_id, "assistant", response, agents_used)
        except Exception:
            pass


def chat_interface():
    """Main chat interface."""
    # Display message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("agents"):
                tags = " ".join([f'<span class="agent-tag">{a}</span>' for a in msg["agents"]])
                st.markdown(f"**Agents:** {tags}", unsafe_allow_html=True)
    
    # Handle pending example query
    if "pending_query" in st.session_state:
        query = st.session_state.pending_query
        del st.session_state.pending_query
        process_message(query)
        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Ask about pharmaceutical strategy, patents, trials, markets..."):
        process_message(prompt)
        st.rerun()


def export_buttons():
    """Export controls at bottom with download functionality."""
    if st.session_state.last_response:
        st.markdown("---")
        cols = st.columns([2, 1, 1])
        with cols[0]:
            st.caption("💡 *Download your analysis report*")
        with cols[1]:
            # PDF Download
            path, file_bytes, filename = export_report("PDF")
            if file_bytes:
                st.download_button(
                    label="📥 Download PDF",
                    data=file_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                if st.button("📥 PDF", use_container_width=True, disabled=True):
                    pass
        with cols[2]:
            # Excel Download
            path, file_bytes, filename = export_report("Excel")
            if file_bytes:
                st.download_button(
                    label="📊 Download Excel",
                    data=file_bytes,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                if st.button("📊 Excel", use_container_width=True, disabled=True):
                    pass


def main():
    """Main entry point."""
    init_session()
    
    # Check if logged in
    # ===== LOGIN DISABLED =====
    # if not st.session_state.logged_in:
    #     login_page()
    #     return
    # ===== END LOGIN DISABLED =====
    
    # Auto-login as guest user (bypass authentication)
    if not st.session_state.logged_in:
        st.session_state.logged_in = True
        st.session_state.user = {
            "id": "guest",
            "username": "Guest User",
            "role": "analyst",
            "email": "guest@pharma.ai"
        }
        st.session_state.session_token = "guest-token"
    
    # Main app
    sidebar()
    header()
    
    # Status bar with user info
    user = st.session_state.user
    status = f"🟢 {user['username']} ({user['role']}) — 9 Agents — Groq Llama 3.3 70B"
    st.markdown(f'<div class="status-bar">{status}</div>', unsafe_allow_html=True)
    
    chat_interface()
    export_buttons()
    
    # Footer
    st.markdown(
        f'<div class="footer">Pharma Agentic AI • {datetime.now().strftime("%Y")}</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
