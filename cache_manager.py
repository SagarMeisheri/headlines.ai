"""
Cache manager for storing and retrieving search queries and results.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

CACHE_FILE = "search_cache.json"
CATEGORY_CACHE_FILE = "category_cache.json"
MAX_CACHED_SEARCHES = 20
CATEGORY_CACHE_TTL_MINUTES = 30  # Cache TTL for categories


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


# ============================================
# Category-specific cache functions
# ============================================

def load_category_cache() -> Dict[str, Dict]:
    """
    Load category cache from file.
    
    Returns:
        Dict mapping category name to cached data
    """
    if not os.path.exists(CATEGORY_CACHE_FILE):
        logging.info("cache_manager: No category cache file found, returning empty dict")
        return {}
    
    try:
        with open(CATEGORY_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            logging.info(f"cache_manager: Loaded category cache with {len(cache)} categories")
            return cache
    except Exception as e:
        logging.error(f"cache_manager: Error loading category cache: {str(e)}")
        return {}


def save_category_cache(cache: Dict[str, Dict]) -> None:
    """
    Save category cache to file.
    
    Args:
        cache: Dict mapping category name to cached data
    """
    try:
        with open(CATEGORY_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        logging.info(f"cache_manager: Saved category cache with {len(cache)} categories")
    except Exception as e:
        logging.error(f"cache_manager: Error saving category cache: {str(e)}")


def get_category_from_cache(category: str) -> Optional[Dict]:
    """
    Get cached data for a specific category.
    
    Args:
        category: Category name (e.g., "Tech", "Business")
        
    Returns:
        Dict with keys: headlines, summary (optional), timestamp, num_articles
        Returns None if not found or expired
    """
    cache = load_category_cache()
    
    if category not in cache:
        logging.info(f"cache_manager: Category '{category}' not found in cache")
        return None
    
    cached_data = cache[category]
    
    # Check if cache is expired
    if is_category_cache_expired(cached_data.get('timestamp')):
        logging.info(f"cache_manager: Category '{category}' cache expired")
        return None
    
    logging.info(f"cache_manager: Found valid cache for category '{category}'")
    return cached_data


def save_category_to_cache(category: str, headlines: List[Dict], summary: Optional[str] = None) -> None:
    """
    Save category data to cache.
    
    Args:
        category: Category name (e.g., "Tech", "Business")
        headlines: List of headline dictionaries
        summary: AI-generated summary (optional, can be added later)
    """
    cache = load_category_cache()
    
    cache[category] = {
        "headlines": headlines,
        "summary": summary,
        "timestamp": datetime.now().isoformat(),
        "num_articles": len(headlines)
    }
    
    logging.info(f"cache_manager: Saved category '{category}' with {len(headlines)} headlines to cache")
    save_category_cache(cache)


def update_category_summary(category: str, summary: str) -> None:
    """
    Update the summary for a cached category.
    
    Args:
        category: Category name
        summary: AI-generated summary
    """
    cache = load_category_cache()
    
    if category in cache:
        cache[category]["summary"] = summary
        save_category_cache(cache)
        logging.info(f"cache_manager: Updated summary for category '{category}'")
    else:
        logging.warning(f"cache_manager: Cannot update summary - category '{category}' not in cache")


def is_category_cache_expired(timestamp_str: Optional[str]) -> bool:
    """
    Check if a category cache entry is expired.
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        True if expired or invalid, False if still valid
    """
    if not timestamp_str:
        return True
    
    try:
        cached_time = datetime.fromisoformat(timestamp_str)
        expiry_time = cached_time + timedelta(minutes=CATEGORY_CACHE_TTL_MINUTES)
        is_expired = datetime.now() > expiry_time
        return is_expired
    except Exception:
        return True


def get_all_categories_from_cache() -> Dict[str, Dict]:
    """
    Get all cached categories that are still valid (not expired).
    
    Returns:
        Dict mapping category name to cached data (only non-expired entries)
    """
    cache = load_category_cache()
    valid_cache = {}
    
    for category, data in cache.items():
        if not is_category_cache_expired(data.get('timestamp')):
            valid_cache[category] = data
    
    logging.info(f"cache_manager: Retrieved {len(valid_cache)} valid categories from cache")
    return valid_cache


def clear_category_cache() -> None:
    """
    Clear all category cache.
    """
    try:
        if os.path.exists(CATEGORY_CACHE_FILE):
            os.remove(CATEGORY_CACHE_FILE)
            logging.info("cache_manager: Category cache cleared successfully")
    except Exception as e:
        logging.error(f"cache_manager: Error clearing category cache: {str(e)}")
