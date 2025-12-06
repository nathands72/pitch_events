"""
Streamlit web app for the Realtime Startup Pitch Event Finder.
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional
import json

from models.event_schema import SearchQuery, RankedEvent, CanonicalEvent
from agents.search_agent import SearchAgent
from agents.parser_agent import ParserAgent
from agents.embedder_agent import EmbedderAgent
from agents.ranker_agent import RankerAgent
from utils.vector_db import get_vector_db
from utils.config import get_settings


# Page config
st.set_page_config(
    page_title="Pitch Event Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium design
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .event-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .event-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 6px;
        font-size: 0.75rem;
        background: #f0f0f0;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "saved_events" not in st.session_state:
        st.session_state.saved_events = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def render_landing():
    """Render landing page with search interface."""
    
    st.markdown('<h1 class="main-header">🎯 Pitch Event Finder</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Find real-time startup pitch events tailored for founders and investors</p>',
        unsafe_allow_html=True
    )
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            intent = st.text_area(
                "What are you looking for?",
                placeholder="e.g., I'm a seed-stage fintech founder looking to pitch in Bangalore",
                height=100
            )
            
            persona = st.radio(
                "I am a:",
                options=["founder", "investor"],
                horizontal=True
            )
        
        with col2:
            location = st.text_input(
                "Location (optional)",
                placeholder="e.g., Bangalore, San Francisco, or leave empty for online events"
            )
            
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                date_from = st.date_input(
                    "From date",
                    value=datetime.now()
                )
            with col_date2:
                date_to = st.date_input(
                    "To date",
                    value=datetime.now() + timedelta(days=90)
                )
        
        # Advanced filters in expander
        with st.expander("Advanced Filters"):
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                industry = st.multiselect(
                    "Industry",
                    options=["fintech", "healthtech", "saas", "ai", "ecommerce", "other"]
                )
                
                pitch_only = st.checkbox("Only events with pitch slots", value=True)
            
            with col_adv2:
                max_price = st.number_input(
                    "Max ticket price (USD)",
                    min_value=0,
                    value=100,
                    step=10
                )
                
                online_only = st.checkbox("Online events only", value=False)
        
        submitted = st.form_submit_button("🔍 Search Events", use_container_width=True)
        
        if submitted and intent:
            # Create search query
            query = SearchQuery(
                intent=intent,
                persona=persona,
                location=location if location else None,
                date_from=datetime.combine(date_from, datetime.min.time()),
                date_to=datetime.combine(date_to, datetime.max.time()),
                industry=industry if industry else None,
                max_price=max_price,
                pitch_only=pitch_only,
                online_only=online_only,
            )
            
            # Execute search
            with st.spinner("🔎 Searching for events..."):
                results = execute_search(query)
                st.session_state.search_results = results
            
            st.success(f"Found {len(results)} matching events!")
            st.rerun()


def execute_search(query: SearchQuery) -> List[RankedEvent]:
    """Execute the full search pipeline."""
    
    # Initialize agents
    search_agent = SearchAgent()
    parser_agent = ParserAgent()
    embedder_agent = EmbedderAgent()
    ranker_agent = RankerAgent()
    vector_db = get_vector_db()
    
    # Step 1: Search for raw hits
    raw_hits = search_agent.search(query)
    
    if not raw_hits:
        return []
    
    # Step 2: Parse and normalize (simplified - in production would fetch full content)
    events = []
    for hit in raw_hits[:10]:  # Limit for demo
        # For MVP, create minimal event from search result
        # In production, FetcherAgent would retrieve full content first
        try:
            parsed = parser_agent.parse(
                raw_data={
                    "url": hit["url"],
                    "snippet": hit["snippet"],
                    "title": hit["title"],
                },
                source=hit["source"]
            )
            
            if parsed:
                events.append(parsed)
        except Exception as e:
            st.warning(f"Failed to parse event: {e}")
            continue
    
    if not events:
        return []
    
    # Step 3: Embed and store in vector DB
    for event in events:
        try:
            embedding, summary = embedder_agent.embed_event(event)
            event.short_summary = summary
            vector_db.add_event(event, embedding)
        except Exception as e:
            st.warning(f"Failed to embed event: {e}")
    
    # Step 4: Retrieve from vector DB with query embedding
    query_embedding, _ = embedder_agent.embed_event(
        # Create a dummy event from query for embedding
        CanonicalEvent(
            title=query.intent,
            description=query.intent,
            start_utc=query.date_from or datetime.utcnow(),
            end_utc=query.date_to or datetime.utcnow(),
            venue={"type": "online"},
            registration={"type": "free"},
            organizer={"name": ""},
        )
    )
    
    candidates = vector_db.search(
        query_embedding=query_embedding,
        top_k=20,
        filters={"status": "active"} if not query.pitch_only else {"has_pitch_slots": True}
    )
    
    # Step 5: Rank results
    ranked = ranker_agent.rank(query, candidates)
    
    return ranked[:10]  # Top 10


def render_results():
    """Render search results."""
    
    if not st.session_state.search_results:
        st.info("👆 Use the search form above to find pitch events")
        return
    
    st.markdown("## 🎯 Matching Events")
    
    for ranked_event in st.session_state.search_results:
        render_event_card(ranked_event)


def render_event_card(ranked_event: RankedEvent):
    """Render a single event card."""
    
    event = ranked_event.event
    
    with st.container():
        st.markdown('<div class="event-card">', unsafe_allow_html=True)
        
        # Header with title and score
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"### {event.title}")
        
        with col2:
            score_pct = int(ranked_event.score * 100)
            st.markdown(
                f'<div class="score-badge">{score_pct}% Match</div>',
                unsafe_allow_html=True
            )
        
        # Event details
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.markdown(f"📅 **{event.start_utc.strftime('%B %d, %Y')}**")
            st.markdown(f"⏰ {event.start_utc.strftime('%I:%M %p')}")
        
        with col_info2:
            if event.venue.type == "online":
                st.markdown("🌐 **Online Event**")
            else:
                location = event.venue.city or "TBD"
                st.markdown(f"📍 **{location}**")
        
        with col_info3:
            if event.registration.price == 0:
                st.markdown("💰 **Free**")
            else:
                st.markdown(f"💰 **{event.registration.currency} {event.registration.price}**")
        
        # Description
        if event.short_summary:
            st.markdown(event.short_summary)
        else:
            st.markdown(event.description[:200] + "...")
        
        # Match explanation
        st.markdown(f"**Why this matches:** {ranked_event.explanation}")
        
        # Tags
        if event.tags:
            tags_html = "".join([f'<span class="tag">{tag}</span>' for tag in event.tags])
            st.markdown(tags_html, unsafe_allow_html=True)
        
        # Pitch slots info
        if event.pitch_slots and event.pitch_slots.available:
            st.success("✅ Pitch slots available!")
            if event.pitch_slots.application_deadline:
                deadline = event.pitch_slots.application_deadline.strftime("%B %d, %Y")
                st.warning(f"⏰ Application deadline: {deadline}")
        
        # Action buttons
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            if event.registration and event.registration.url:
                st.link_button("🎫 Register", str(event.registration.url))
        
        with col_btn2:
            if event.pitch_slots and event.pitch_slots.application_url:
                st.link_button("🎤 Apply to Pitch", event.pitch_slots.application_url)
        
        with col_btn3:
            if st.button("💾 Save", key=f"save_{event.event_id}"):
                st.session_state.saved_events.append(event)
                st.success("Saved!")
        
        with col_btn4:
            if event.organizer.contact_email:
                st.link_button("📧 Contact", f"mailto:{event.organizer.contact_email}")
        
        # Provenance
        if event.sources:
            sources_text = " · ".join([s.source for s in event.sources])
            last_checked = event.sources[0].fetched_at.strftime("%Y-%m-%d %H:%M")
            st.caption(f"Sources: {sources_text} · Last checked: {last_checked}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main app entry point."""
    
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📚 About")
        st.markdown(
            "Find real-time startup pitch events using AI-powered search "
            "across multiple platforms."
        )
        
        st.markdown("### 🔑 Features")
        st.markdown("""
        - Real-time web search via Tavily
        - Multi-platform aggregation
        - Smart ranking & matching
        - Pitch slot detection
        - RAG-powered assistant
        """)
        
        st.markdown("---")
        
        if st.session_state.saved_events:
            st.markdown(f"### 💾 Saved Events ({len(st.session_state.saved_events)})")
            for event in st.session_state.saved_events:
                st.markdown(f"- {event.title}")
        
        st.markdown("---")
        st.caption("Powered by Tavily, OpenAI & Chroma")
    
    # Main content
    render_landing()
    render_results()


if __name__ == "__main__":
    main()
