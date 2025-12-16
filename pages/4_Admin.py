"""
Admin Page - Database Management
CRUD operations for pharma data.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

st.set_page_config(
    page_title="Admin - Pharma AI",
    page_icon="🔧",
    layout="wide"
)

# Check auth
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in from the main page first.")
    st.stop()

# Check admin role
user = st.session_state.get("user", {})
if user.get("role") not in ["admin", "manager"]:
    st.error("⛔ Access Denied. Admin or Manager role required.")
    st.stop()

st.title("🔧 Database Administration")
st.markdown("Manage pharmaceutical data, users, and system settings.")

# Tabs for different admin functions
tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Data", "💊 Patents", "👥 Users", "📄 Documents"])

# Import database services
try:
    from src.database.db import get_db_session
    from src.database.models import (
        MarketData, Patent, PatentStatus, ClinicalTrial, 
        Competitor, User, UserRole
    )
    from sqlalchemy import select, update, delete
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()


def format_date(date_val):
    """Format date for display."""
    if date_val:
        if hasattr(date_val, 'strftime'):
            return date_val.strftime("%Y-%m-%d")
        return str(date_val)
    return ""


# Tab 1: Market Data
with tab1:
    st.subheader("📊 Market Data Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Current Market Data")
        
        with get_db_session() as session:
            markets = session.execute(select(MarketData)).scalars().all()
            
            if markets:
                data = []
                for m in markets:
                    data.append({
                        "ID": m.id,
                        "Molecule": m.molecule,
                        "Therapy Area": m.therapy_area,
                        "Region": m.region,
                        "Market Size ($M)": f"${m.market_size_usd_mn:,.0f}",
                        "CAGR": f"{m.cagr_percent:.1f}%",
                        "Competition": m.competition_level or "N/A"
                    })
                
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No market data available.")
    
    with col2:
        st.markdown("### Add New Market Data")
        
        with st.form("add_market"):
            molecule = st.text_input("Molecule Name")
            therapy = st.text_input("Therapy Area")
            region = st.selectbox("Region", ["India", "US", "EU", "Global", "APAC"])
            size = st.number_input("Market Size (USD Millions)", min_value=0.0, step=100.0)
            cagr = st.number_input("CAGR %", min_value=0.0, max_value=50.0, step=0.1)
            competition = st.selectbox("Competition Level", ["Low", "Medium", "High"])
            
            if st.form_submit_button("Add Market Data", use_container_width=True):
                if molecule and therapy and region:
                    try:
                        with get_db_session() as session:
                            new_market = MarketData(
                                molecule=molecule,
                                therapy_area=therapy,
                                region=region,
                                market_size_usd_mn=size,
                                cagr_percent=cagr,
                                competition_level=competition
                            )
                            session.add(new_market)
                            session.commit()
                        st.success(f"Added market data for {molecule} in {region}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill in required fields.")


# Tab 2: Patents
with tab2:
    st.subheader("💊 Patent Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Current Patents")
        
        with get_db_session() as session:
            patents = session.execute(select(Patent)).scalars().all()
            
            if patents:
                data = []
                for p in patents:
                    data.append({
                        "ID": p.id,
                        "Molecule": p.molecule,
                        "Patent #": p.patent_number,
                        "Type": p.patent_type or "N/A",
                        "Expiry": format_date(p.expiry_date),
                        "Status": p.status.value if hasattr(p.status, 'value') else str(p.status),
                        "Country": p.country
                    })
                
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No patent data available.")
    
    with col2:
        st.markdown("### Add New Patent")
        
        with st.form("add_patent"):
            molecule = st.text_input("Molecule Name")
            patent_num = st.text_input("Patent Number")
            patent_type = st.selectbox("Patent Type", ["Composition of Matter", "Formulation", "Process", "Method of Use"])
            country = st.selectbox("Country", ["US", "EU", "India", "Japan", "China"])
            expiry = st.date_input("Expiry Date")
            status = st.selectbox("Status", ["Active", "Expired", "Pending"])
            
            if st.form_submit_button("Add Patent", use_container_width=True):
                if molecule and patent_num:
                    try:
                        with get_db_session() as session:
                            status_enum = getattr(PatentStatus, status.upper(), PatentStatus.ACTIVE)
                            new_patent = Patent(
                                molecule=molecule,
                                patent_number=patent_num,
                                patent_type=patent_type,
                                country=country,
                                expiry_date=datetime.combine(expiry, datetime.min.time()),
                                status=status_enum
                            )
                            session.add(new_patent)
                            session.commit()
                        st.success(f"Added patent for {molecule}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill in required fields.")


# Tab 3: Users
with tab3:
    st.subheader("👥 User Management")
    
    # Allow managers to view, but only admin can modify
    if user.get("role") not in ["admin", "manager"]:
        st.warning("Only administrators and managers can access user management.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Current Users")
            
            with get_db_session() as session:
                users_list = session.execute(select(User)).scalars().all()
                
                if users_list:
                    data = []
                    for u in users_list:
                        data.append({
                            "ID": u.id,
                            "Username": u.username,
                            "Email": u.email or "N/A",
                            "Role": u.role.value if hasattr(u.role, 'value') else str(u.role),
                            "Active": "✅" if u.is_active else "❌",
                            "Created": format_date(u.created_at)
                        })
                    
                    st.dataframe(data, use_container_width=True)
                else:
                    st.info("No users found.")
        
        with col2:
            st.markdown("### Add New User")
            
            # Both admin and manager can add users, but managers cannot add admin users
            is_admin = user.get("role") == "admin"
            is_manager = user.get("role") == "manager"
            
            if is_admin or is_manager:
                with st.form("add_user"):
                    username = st.text_input("Username")
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    
                    # Managers can only create analyst or manager users
                    if is_admin:
                        role_options = ["analyst", "manager", "admin"]
                    else:
                        role_options = ["analyst", "manager"]
                    
                    role = st.selectbox("Role", role_options)
                    
                    if st.form_submit_button("Add User", use_container_width=True):
                        if username and password:
                            try:
                                import hashlib
                                with get_db_session() as session:
                                    # Check if username exists
                                    existing = session.execute(
                                        select(User).where(User.username == username)
                                    ).scalar_one_or_none()
                                    
                                    if existing:
                                        st.error("Username already exists.")
                                    else:
                                        role_enum = getattr(UserRole, role.upper(), UserRole.ANALYST)
                                        new_user = User(
                                            username=username,
                                            email=email,
                                            password_hash=hashlib.sha256(password.encode()).hexdigest(),
                                            role=role_enum,
                                            is_active=True
                                        )
                                        session.add(new_user)
                                        session.commit()
                                        st.success(f"Added user {username}")
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.warning("Please fill in required fields.")
            else:
                st.info("Only administrators and managers can add users.")
            
            st.markdown("---")
            st.markdown("### Manage User")
            
            with get_db_session() as session:
                users_list = session.execute(select(User)).scalars().all()
                user_options = {u.username: u.id for u in users_list}
            
            if user_options:
                selected_user = st.selectbox("Select User", list(user_options.keys()))
                
                # Admin can modify all users, managers can modify non-admin users
                can_modify = False
                if is_admin:
                    can_modify = True
                elif is_manager:
                    # Check if selected user is not an admin
                    with get_db_session() as session:
                        selected_user_obj = session.get(User, user_options[selected_user])
                        if selected_user_obj and selected_user_obj.role != UserRole.ADMIN:
                            can_modify = True
                
                if can_modify:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("🔄 Reset Password", use_container_width=True):
                            if selected_user:
                                try:
                                    import hashlib
                                    with get_db_session() as session:
                                        user_to_update = session.get(User, user_options[selected_user])
                                        user_to_update.password_hash = hashlib.sha256("password123".encode()).hexdigest()
                                        session.commit()
                                    st.success(f"Password reset to 'password123' for {selected_user}")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    
                    with col_b:
                        if st.button("🚫 Deactivate", use_container_width=True):
                            if selected_user and selected_user != st.session_state.user.get("username"):
                                try:
                                    with get_db_session() as session:
                                        user_to_update = session.get(User, user_options[selected_user])
                                        user_to_update.is_active = not user_to_update.is_active
                                        session.commit()
                                    st.success(f"Toggled active status for {selected_user}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            else:
                                st.warning("Cannot deactivate your own account.")
                else:
                    st.info("You can only modify users with analyst or manager roles.")


# Tab 4: Documents
with tab4:
    st.subheader("📄 Internal Documents")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Document Library")
        
        try:
            from src.services.rag_service import get_rag_service
            rag = get_rag_service()
            docs = rag.documents
            
            if docs:
                data = []
                for d in docs:
                    data.append({
                        "ID": d.get("doc_id", ""),
                        "Title": d.get("title", "")[:50],
                        "Tags": ", ".join(d.get("tags", [])[:3]),
                        "Summary": d.get("summary", "")[:80] + "..."
                    })
                
                st.dataframe(data, use_container_width=True)
            else:
                st.info("No internal documents found.")
        except Exception as e:
            st.error(f"Error loading documents: {e}")
    
    with col2:
        st.markdown("### Add Document")
        
        with st.form("add_doc"):
            doc_id = st.text_input("Document ID (e.g., DOC-2024-001)")
            title = st.text_input("Title")
            summary = st.text_area("Summary", height=100)
            content = st.text_area("Content", height=150)
            tags = st.text_input("Tags (comma-separated)")
            
            if st.form_submit_button("Add Document", use_container_width=True):
                if title and summary:
                    try:
                        from src.services.rag_service import get_rag_service
                        rag = get_rag_service()
                        
                        success = rag.add_document({
                            "doc_id": doc_id or f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "title": title,
                            "summary": summary,
                            "content": content,
                            "tags": [t.strip() for t in tags.split(",")] if tags else []
                        })
                        
                        if success:
                            st.success(f"Added document: {title}")
                            st.rerun()
                        else:
                            st.error("Failed to add document.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill in title and summary.")
        
        st.markdown("---")
        st.markdown("### Document Search")
        
        search_query = st.text_input("Search documents...")
        if search_query:
            try:
                from src.services.rag_service import get_rag_service
                rag = get_rag_service()
                results = rag.search(search_query, n_results=5)
                
                if results:
                    for r in results:
                        with st.expander(f"📄 {r.title} (Score: {r.score:.2f})"):
                            st.write(f"**ID:** {r.doc_id}")
                            st.write(f"**Tags:** {', '.join(r.tags)}")
                            st.write(r.summary)
                else:
                    st.info("No matching documents found.")
            except Exception as e:
                st.error(f"Search error: {e}")


# Sidebar info
with st.sidebar:
    st.markdown("### Admin Info")
    st.markdown(f"**User:** {user.get('username', 'Unknown')}")
    st.markdown(f"**Role:** {user.get('role', 'Unknown')}")
    
    st.markdown("---")
    st.markdown("### Quick Stats")
    
    try:
        with get_db_session() as session:
            market_count = len(session.execute(select(MarketData)).scalars().all())
            patent_count = len(session.execute(select(Patent)).scalars().all())
            user_count = len(session.execute(select(User)).scalars().all())
        
        st.metric("Market Records", market_count)
        st.metric("Patents", patent_count)
        st.metric("Users", user_count)
    except:
        st.info("Stats unavailable")
    
    st.markdown("---")
    if st.button("🔄 Refresh Database", use_container_width=True):
        st.rerun()
