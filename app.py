import streamlit as st
import logging
from datetime import datetime
from google_news_rss import fetch_google_news, fetch_all_categories
from utils import summarize_headlines, summarize_headlines_stream
from cache_manager import (
    add_search_to_cache, 
    get_recent_searches, 
    get_search_by_query,
    clear_cache,
    get_category_from_cache,
    save_category_to_cache,
    update_category_summary,
    get_all_categories_from_cache,
    clear_category_cache
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ===========================================
# Categories Configuration
# ===========================================
CATEGORIES = {
    "Tech": "technology news",
    "Business": "business news",
    "Sports": "sports news",
    "Entertainment": "entertainment news",
    "Health": "health news",
    "Science": "science news",
    "Politics": "politics news",
    "World": "world news"
}

# Page configuration
st.set_page_config(
    page_title="Headlines.AI - News Summarizer",
    page_icon="📰",
    layout="wide"
)

# ===========================================
# Session State Initialization
# ===========================================
if 'current_data' not in st.session_state:
    st.session_state.current_data = None  # Custom search data (shown as dynamic tab)
if 'pending_search' not in st.session_state:
    st.session_state.pending_search = None  # {query, days} - triggers search inside tab
if 'category_data' not in st.session_state:
    st.session_state.category_data = {}  # {category: {headlines, summary, timestamp}}
if 'fetch_triggered' not in st.session_state:
    st.session_state.fetch_triggered = False
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

# ===========================================
# Cache-First Load Strategy
# ===========================================
def load_categories_from_cache():
    """Load all categories from cache into session state."""
    cached_categories = get_all_categories_from_cache()
    for category, data in cached_categories.items():
        if category not in st.session_state.category_data:
            st.session_state.category_data[category] = data
    return cached_categories

def fetch_fresh_categories(days: int = 7):
    """Fetch fresh data for all categories in parallel."""
    logging.info("Fetching fresh data for all categories...")
    fresh_data = fetch_all_categories(CATEGORIES, days=days)
    
    for category, headlines in fresh_data.items():
        if headlines:
            # Update session state
            st.session_state.category_data[category] = {
                'headlines': headlines,
                'summary': None,  # Summary generated on-demand
                'timestamp': datetime.now().isoformat(),
                'num_articles': len(headlines)
            }
            # Save to cache
            save_category_to_cache(category, headlines)
    
    st.session_state.last_refresh = datetime.now()
    return fresh_data

# ===========================================
# Render Functions
# ===========================================
def render_headlines_list(headlines, limit=None):
    """Render a list of headlines."""
    display_headlines = headlines[:limit] if limit else headlines
    for idx, headline in enumerate(display_headlines, 1):
        with st.container():
            st.markdown(f"**{idx}. {headline['title']}**")
            source = headline.get('source', 'Unknown')
            st.caption(f"📅 {headline['published']} • 📰 {source}")
            st.markdown("")

def render_category_tab(category: str):
    """Render content for a single category tab."""
    data = st.session_state.category_data.get(category)
    
    if not data or not data.get('headlines'):
        # No data yet - show loading state and fetch
        with st.spinner(f"Loading {category} news..."):
            headlines = fetch_google_news(CATEGORIES[category], days=7, verbose=False)
            if headlines:
                st.session_state.category_data[category] = {
                    'headlines': headlines,
                    'summary': None,
                    'timestamp': datetime.now().isoformat(),
                    'num_articles': len(headlines)
                }
                save_category_to_cache(category, headlines)
                data = st.session_state.category_data[category]
            else:
                st.warning(f"No news found for {category}. Try refreshing.")
                return
    
    headlines = data['headlines']
    summary = data.get('summary')
    
    st.success(f"✅ Found {len(headlines)} articles for {category}")
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    # Left column: Headlines
    with col1:
        st.subheader("📋 Headlines")
        st.markdown("---")
        render_headlines_list(headlines)
    
    # Right column: AI Summary (lazy loading)
    with col2:
        st.subheader("🤖 AI Summary")
        st.markdown("---")
        
        if summary:
            st.markdown(summary)
        else:
            # Generate summary on demand with streaming
            if st.button(f"Generate Summary for {category}", key=f"summarize_{category}"):
                try:
                    # Use st.write_stream for real-time streaming output
                    summary = st.write_stream(summarize_headlines_stream(headlines))
                    # Save the complete summary to session state and cache
                    st.session_state.category_data[category]['summary'] = summary
                    update_category_summary(category, summary)
                except Exception as e:
                    st.error(f"❌ Error generating summary: {str(e)}")
                    st.info("💡 Make sure your OPENROUTER_API_KEY is set in the .env file")
            else:
                st.info("👆 Click the button above to generate an AI summary of these headlines")

def render_dashboard():
    """Render the dashboard tab with headlines from all categories."""
    st.subheader("📊 News Dashboard")
    st.markdown("Top headlines from all categories")
    st.markdown("---")
    
    # Show last refresh time
    if st.session_state.last_refresh:
        st.caption(f"Last refreshed: {st.session_state.last_refresh.strftime('%B %d, %Y at %I:%M %p')}")
    
    # Create a 2-column grid for categories
    categories_list = list(CATEGORIES.keys())
    
    for i in range(0, len(categories_list), 2):
        col1, col2 = st.columns(2)
        
        # First column
        with col1:
            category = categories_list[i]
            render_dashboard_card(category)
        
        # Second column (if exists)
        if i + 1 < len(categories_list):
            with col2:
                category = categories_list[i + 1]
                render_dashboard_card(category)

def render_dashboard_card(category: str):
    """Render a category card for the dashboard."""
    data = st.session_state.category_data.get(category)
    
    with st.container():
        st.markdown(f"### {get_category_emoji(category)} {category}")
        
        if data and data.get('headlines'):
            headlines = data['headlines'][:5]  # Top 5 headlines
            for headline in headlines:
                st.markdown(f"• {headline['title'][:80]}{'...' if len(headline['title']) > 80 else ''}")
            
            st.caption(f"📰 {data['num_articles']} total articles")
        else:
            st.info(f"Click the {category} tab to load news")
        
        st.markdown("---")

def get_category_emoji(category: str) -> str:
    """Get emoji for a category."""
    emojis = {
        "Tech": "💻",
        "Business": "💼",
        "Sports": "⚽",
        "Entertainment": "🎬",
        "Health": "🏥",
        "Science": "🔬",
        "Politics": "🏛️",
        "World": "🌍"
    }
    return emojis.get(category, "📰")

def render_custom_search_tab():
    """Render custom search results in a tab."""
    # Check if there's a pending search to execute
    if st.session_state.pending_search:
        pending = st.session_state.pending_search
        query = pending['query']
        days = pending['days']
        
        # Clear button in header
        col_header, col_clear = st.columns([4, 1])
        with col_header:
            st.subheader(f"🔍 Searching: {query}")
        with col_clear:
            if st.button("✕ Cancel", key="cancel_search", help="Cancel this search"):
                st.session_state.pending_search = None
                st.session_state.current_data = None
                st.rerun()
        
        # Check cache first
        cached_search = get_search_by_query(query)
        if cached_search and cached_search.get('days') == days:
            st.session_state.current_data = cached_search
            st.session_state.pending_search = None
            st.rerun()
            return
        
        # Fetch headlines
        with st.spinner(f'Fetching news for "{query}"...'):
            headlines = fetch_google_news(query, days=days, verbose=False)
        
        if not headlines:
            st.error(f"❌ No news found for '{query}'. Try a different search term.")
            st.session_state.pending_search = None
            return
        
        st.success(f"✅ Found {len(headlines)} articles")
        
        # Create two columns
        col1, col2 = st.columns([1, 1])
        
        # Left column: Headlines (show immediately)
        with col1:
            st.subheader("📋 Headlines")
            st.markdown("---")
            render_headlines_list(headlines)
        
        # Right column: Generate summary with streaming
        with col2:
            st.subheader("🤖 AI Summary")
            st.markdown("---")
            try:
                summary = st.write_stream(summarize_headlines_stream(headlines))
                # Save to cache and session state
                add_search_to_cache(query, days, headlines, summary)
                st.session_state.current_data = {
                    'query': query,
                    'days': days,
                    'headlines': headlines,
                    'summary': summary,
                    'timestamp': datetime.now().isoformat(),
                    'num_articles': len(headlines)
                }
                st.session_state.pending_search = None
            except Exception as e:
                st.error(f"❌ Error generating summary: {str(e)}")
                st.info("💡 Make sure your OPENROUTER_API_KEY is set in the .env file")
        return
    
    # Display existing search results
    if not st.session_state.current_data:
        st.info("👈 Use the sidebar to search for a specific topic")
        return
    
    cached = st.session_state.current_data
    
    # Header with clear button
    col_header, col_clear = st.columns([4, 1])
    with col_header:
        search_date = datetime.fromisoformat(cached['timestamp'])
        formatted_date = search_date.strftime("%B %d, %Y at %I:%M %p")
        st.caption(f"🕐 Searched: {formatted_date}")
    with col_clear:
        if st.button("✕ Clear", key="clear_search", help="Close this search tab"):
            st.session_state.current_data = None
            st.rerun()
    
    st.success(f"✅ Found {len(cached['headlines'])} articles for '{cached['query']}'")
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    # Left column: Headlines
    with col1:
        st.subheader("📋 Headlines")
        st.markdown("---")
        render_headlines_list(cached['headlines'])
    
    # Right column: AI Summary
    with col2:
        st.subheader("🤖 AI Summary")
        st.markdown("---")
        st.markdown(cached['summary'])

# ===========================================
# Main App Layout
# ===========================================

# Title and description
st.title("📰 Headlines.AI")
st.markdown("AI-powered news aggregator with category tabs • Powered by NVIDIA Nemotron")

# ===========================================
# Sidebar
# ===========================================
st.sidebar.header("⚙️ Controls")

# Refresh All button
if st.sidebar.button("🔄 Refresh All Categories", type="primary", use_container_width=True):
    with st.spinner("Refreshing all categories..."):
        fetch_fresh_categories(days=7)
    st.rerun()

# Show last refresh time in sidebar
if st.session_state.last_refresh:
    st.sidebar.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%I:%M %p')}")

st.sidebar.markdown("---")

# Custom Search Section
st.sidebar.header("🔎 Custom Search")
query = st.sidebar.text_input(
    "Enter search query",
    placeholder="e.g., artificial intelligence, climate change",
    help="Search for any topic not covered by the category tabs"
)

days = st.sidebar.number_input(
    "Days to look back",
    min_value=1,
    max_value=30,
    value=7,
    help="Number of days to search back for news articles"
)

search_button = st.sidebar.button("🔍 Search", use_container_width=True)

st.sidebar.markdown("---")

# Recent Searches Section
st.sidebar.header("📚 Recent Searches")
recent_searches = get_recent_searches(limit=5)

if recent_searches:
    for idx, search in enumerate(recent_searches):
        search_date = datetime.fromisoformat(search['timestamp'])
        formatted_date = search_date.strftime("%b %d, %I:%M %p")
        
        if st.sidebar.button(
            f"🔍 {search['query'][:25]}{'...' if len(search['query']) > 25 else ''}",
            key=f"recent_{idx}",
            help=f"{formatted_date} - {search['num_articles']} articles",
            use_container_width=True
        ):
            st.session_state.current_data = search
            st.rerun()
    
    if st.sidebar.button("🗑️ Clear History", use_container_width=True):
        clear_cache()
        clear_category_cache()
        st.session_state.current_data = None
        st.session_state.pending_search = None
        st.session_state.category_data = {}
        st.session_state.fetch_triggered = False
        st.rerun()
else:
    st.sidebar.info("No recent searches yet")

# ===========================================
# Initial Load - Cache First Strategy
# ===========================================
if not st.session_state.fetch_triggered:
    st.session_state.fetch_triggered = True
    # Load from cache first
    cached_categories = load_categories_from_cache()
    
    # Only fetch fresh data if cache is empty or incomplete
    if len(cached_categories) < len(CATEGORIES):
        with st.spinner("📡 Fetching latest headlines from all categories..."):
            fetch_fresh_categories(days=7)
    else:
        # Cache was valid, just set the last refresh time from cache
        st.session_state.last_refresh = datetime.now()

# ===========================================
# Handle Custom Search
# ===========================================
if search_button and query:
    # Set pending search - actual search happens inside the tab
    st.session_state.pending_search = {'query': query, 'days': days}
    st.session_state.current_data = None  # Clear any previous search
    st.rerun()

# ===========================================
# Main Content - Tabbed Interface
# ===========================================

# Build tab names: Dashboard + Categories + optional Search tab
tab_names = ["📊 Dashboard"] + [f"{get_category_emoji(cat)} {cat}" for cat in CATEGORIES.keys()]

# Add search tab if there's a pending or completed search
has_search_tab = False
if st.session_state.pending_search:
    query = st.session_state.pending_search['query']
    tab_names.append(f"🔍 {query[:20]}{'...' if len(query) > 20 else ''}")
    has_search_tab = True
elif st.session_state.current_data:
    query = st.session_state.current_data['query']
    tab_names.append(f"🔍 {query[:20]}{'...' if len(query) > 20 else ''}")
    has_search_tab = True

tabs = st.tabs(tab_names)

# Dashboard tab
with tabs[0]:
    render_dashboard()

# Individual category tabs
for idx, category in enumerate(CATEGORIES.keys(), 1):
    with tabs[idx]:
        render_category_tab(category)

# Custom search tab (if active)
if has_search_tab:
    with tabs[-1]:
        render_custom_search_tab()

# ===========================================
# Footer
# ===========================================
st.markdown("---")
st.caption("Powered by Google News RSS & NVIDIA Nemotron via OpenRouter")
