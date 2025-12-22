"""
Cache manager for storing and retrieving search queries and results.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

CACHE_FILE = "search_cache.json"
MAX_CACHED_SEARCHES = 20


def load_cache() -> List[Dict]:
    """
    Load cached searches from file.
    
    Returns:
        List of cached search dictionaries
    """
    if not os.path.exists(CACHE_FILE):
        logging.info("cache_manager: No cache file found, returning empty list")
        return []
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            logging.info(f"cache_manager: Loaded {len(cache)} cached searches")
            return cache
    except Exception as e:
        logging.error(f"cache_manager: Error loading cache: {str(e)}")
        return []


def save_cache(cache: List[Dict]) -> None:
    """
    Save cache to file.
    
    Args:
        cache: List of cached search dictionaries
    """
    try:
        # Keep only the most recent MAX_CACHED_SEARCHES
        cache = cache[-MAX_CACHED_SEARCHES:]
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        logging.info(f"cache_manager: Saved {len(cache)} searches to cache")
    except Exception as e:
        logging.error(f"cache_manager: Error saving cache: {str(e)}")


def add_search_to_cache(query: str, days: int, headlines: List[Dict], summary: str) -> None:
    """
    Add a new search to cache.
    
    Args:
        query: Search query string
        days: Number of days searched
        headlines: List of headlines
        summary: AI-generated summary
    """
    cache = load_cache()
    
    # Create new search entry
    search_entry = {
        "query": query,
        "days": days,
        "timestamp": datetime.now().isoformat(),
        "headlines": headlines,
        "summary": summary,
        "num_articles": len(headlines)
    }
    
    # Remove any existing search with the same query (to avoid duplicates)
    cache = [s for s in cache if s.get("query", "").lower() != query.lower()]
    
    # Add new search at the end (most recent)
    cache.append(search_entry)
    
    logging.info(f"cache_manager: Added search for '{query}' to cache")
    save_cache(cache)


def get_recent_searches(limit: int = 10) -> List[Dict]:
    """
    Get recent searches from cache.
    
    Args:
        limit: Maximum number of searches to return
        
    Returns:
        List of recent searches (most recent first)
    """
    cache = load_cache()
    # Return in reverse order (most recent first)
    return list(reversed(cache[-limit:]))


def get_search_by_query(query: str) -> Optional[Dict]:
    """
    Get a specific search from cache by query.
    
    Args:
        query: Search query string
        
    Returns:
        Search dictionary if found, None otherwise
    """
    cache = load_cache()
    for search in reversed(cache):
        if search.get("query", "").lower() == query.lower():
            logging.info(f"cache_manager: Found cached search for '{query}'")
            return search
    
    logging.info(f"cache_manager: No cached search found for '{query}'")
    return None


def clear_cache() -> None:
    """
    Clear all cached searches.
    """
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            logging.info("cache_manager: Cache cleared successfully")
    except Exception as e:
        logging.error(f"cache_manager: Error clearing cache: {str(e)}")
