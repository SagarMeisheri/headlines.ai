import streamlit as st
import logging
from datetime import datetime
from google_news_rss import fetch_google_news
from utils import summarize_headlines
from cache_manager import (
    add_search_to_cache, 
    get_recent_searches, 
    get_search_by_query,
    clear_cache
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Page configuration
st.set_page_config(
    page_title="Headlines.AI - News Summarizer",
    page_icon="📰",
    layout="wide"
)

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'new'  # 'new' or 'cached'
if 'current_data' not in st.session_state:
    st.session_state.current_data = None

# Title and description
st.title("📰 Headlines.AI")
st.markdown("Search for news topics and get AI-powered summaries powered by NVIDIA Nemotron")

# Sidebar - Recent Searches Section
st.sidebar.header("📚 Recent Searches")
recent_searches = get_recent_searches(limit=10)

if recent_searches:
    st.sidebar.markdown("---")
    for idx, search in enumerate(recent_searches):
        search_date = datetime.fromisoformat(search['timestamp'])
        formatted_date = search_date.strftime("%b %d, %I:%M %p")
        
        # Create a button for each recent search
        if st.sidebar.button(
            f"🔍 {search['query'][:30]}{'...' if len(search['query']) > 30 else ''}",
            key=f"recent_{idx}",
            help=f"Searched on {formatted_date} - {search['num_articles']} articles",
            use_container_width=True
        ):
            st.session_state.current_view = 'cached'
            st.session_state.current_data = search
            st.rerun()
        
        st.sidebar.caption(f"📅 {formatted_date} • {search['num_articles']} articles")
        st.sidebar.markdown("")
    
    # Add clear cache button
    if st.sidebar.button("🗑️ Clear History", use_container_width=True):
        clear_cache()
        st.session_state.current_view = 'new'
        st.session_state.current_data = None
        st.rerun()
else:
    st.sidebar.info("No recent searches yet. Start searching to see your history here!")

st.sidebar.markdown("---")

# Input section
st.sidebar.header("🔎 New Search")
query = st.sidebar.text_input(
    "Enter search query",
    placeholder="e.g., artificial intelligence, climate change, etc.",
    help="Enter any topic you want to search for in the news"
)

days = st.sidebar.number_input(
    "Days to look back",
    min_value=1,
    max_value=30,
    value=7,
    help="Number of days to search back for news articles"
)

search_button = st.sidebar.button("🔍 Search News", type="primary", use_container_width=True)

# Main content area
if search_button:
    if not query:
        st.warning("⚠️ Please enter a search query")
    else:
        # Check if we have a cached version
        cached_search = get_search_by_query(query)
        
        if cached_search and cached_search.get('days') == days:
            # Use cached data
            logging.info(f"Using cached search for '{query}'")
            st.info("💾 Loading results from cache...")
            st.session_state.current_view = 'cached'
            st.session_state.current_data = cached_search
            st.rerun()
        else:
            # Perform new search
            logging.info(f"Step 1: Starting search for query: '{query}', days: {days}")
            
            # Show loading state
            with st.spinner(f'Fetching news for "{query}"...'):
                logging.info("Step 2: Calling fetch_google_news()")
                try:
                    headlines = fetch_google_news(query, days=days, verbose=False)
                    logging.info(f"Step 3: fetch_google_news() completed. Found {len(headlines)} headlines")
                except Exception as e:
                    logging.error(f"Error in fetch_google_news(): {str(e)}")
                    st.error(f"❌ Error fetching news: {str(e)}")
                    headlines = []
            
            if not headlines:
                logging.info("Step 4: No headlines found")
                st.error(f"❌ No news found for '{query}'. Try a different search term or increase the number of days.")
            else:
                logging.info(f"Step 5: Displaying {len(headlines)} articles")
                st.success(f"✅ Found {len(headlines)} articles for '{query}'")
                
                # Create two columns
                col1, col2 = st.columns([1, 1])
                
                # Left column: Headlines
                with col1:
                    st.subheader("📋 Headlines")
                    st.markdown("---")
                    
                    for idx, headline in enumerate(headlines, 1):
                        with st.container():
                            st.markdown(f"**{idx}. {headline['title']}**")
                            st.caption(f"📅 {headline['published']}")
                            st.markdown("")  # Add spacing
                
                # Right column: AI Summary
                with col2:
                    st.subheader("🤖 AI Summary")
                    st.markdown("---")
                    
                    logging.info("Step 6: Starting AI summarization")
                    with st.spinner("Generating AI summary..."):
                        try:
                            logging.info("Step 7: Calling summarize_headlines()")
                            summary = summarize_headlines(headlines)
                            logging.info("Step 8: summarize_headlines() completed successfully")
                            st.markdown(summary)
                            
                            # Save to cache
                            logging.info("Step 9: Saving search to cache")
                            add_search_to_cache(query, days, headlines, summary)
                            
                        except Exception as e:
                            logging.error(f"Error in summarize_headlines(): {str(e)}")
                            st.error(f"❌ Error generating summary: {str(e)}")
                            st.info("💡 Make sure your OPENROUTER_API_KEY is set in the .env file")
                    
                    logging.info("Step 10: All steps completed successfully")

elif st.session_state.current_view == 'cached' and st.session_state.current_data:
    # Display cached search results
    cached = st.session_state.current_data
    
    # Show cache indicator
    search_date = datetime.fromisoformat(cached['timestamp'])
    formatted_date = search_date.strftime("%B %d, %Y at %I:%M %p")
    st.info(f"📚 Viewing cached results from {formatted_date}")
    
    st.success(f"✅ Found {len(cached['headlines'])} articles for '{cached['query']}'")
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    # Left column: Headlines
    with col1:
        st.subheader("📋 Headlines")
        st.markdown("---")
        
        for idx, headline in enumerate(cached['headlines'], 1):
            with st.container():
                st.markdown(f"**{idx}. {headline['title']}**")
                st.caption(f"📅 {headline['published']}")
                st.markdown("")  # Add spacing
    
    # Right column: AI Summary
    with col2:
        st.subheader("🤖 AI Summary")
        st.markdown("---")
        st.markdown(cached['summary'])
    
    # Add button to clear cached view
    if st.button("🔄 Start New Search"):
        st.session_state.current_view = 'new'
        st.session_state.current_data = None
        st.rerun()

else:
    # Show instructions when no search has been made
    st.info("👈 Enter a search query in the sidebar and click 'Search News' to get started")
    
    # Show example queries
    st.markdown("### Example Queries")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("- Artificial Intelligence")
        st.markdown("- Climate Change")
        st.markdown("- Space Exploration")
    with col2:
        st.markdown("- Cryptocurrency")
        st.markdown("- Electric Vehicles")
        st.markdown("- Healthcare Innovation")
    with col3:
        st.markdown("- Economic Policy")
        st.markdown("- Sports News")
        st.markdown("- Technology Trends")

# Footer
st.markdown("---")
st.caption("Powered by Google News RSS & NVIDIA Nemotron via OpenRouter")

