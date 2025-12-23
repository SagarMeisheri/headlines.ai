import feedparser
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import time
import logging
import requests

def fetch_google_news(query, days=7, verbose=False):
    """
    Fetch Google News headlines for a given search query
    
    Args:
        query (str): Search query string
        days (int): Number of days to look back (default: 7)
        verbose (bool): Whether to print results (default: True)
        
    Returns:
        list: List of dictionaries containing 'title' and 'published' keys,
              or empty list if no results or error occurs

    Use these parameters to further refine your search results:

    hl=[language-code] – Interface language (e.g., en-US, fr, es)

    gl=[country-code] – Geographic location (e.g., US, UK, CA)

    ceid=[country]:[language] – Edition ID

    For instance, to get Canadian tech news in French:

    https://news.google.com/rss/search?q=technologie&hl=fr-CA&gl=CA&ceid=CA:fr
    """
    rss_url = f"https://news.google.com/rss/search?q={quote(query)}+when:{days}d"
    logging.info(f"fetch_google_news: Constructed RSS URL: {rss_url}")
    
    if verbose:
        print(f'\nFetching news for: "{query}" (Last {days} days)...\n')
    
    try:
        logging.info("fetch_google_news: Fetching RSS feed with timeout")
        # Fetch RSS feed with a timeout to prevent hanging
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
        logging.info(f"fetch_google_news: RSS feed fetched successfully (status: {response.status_code})")
        
        logging.info("fetch_google_news: Parsing RSS feed with feedparser")
        feed = feedparser.parse(response.content)
        logging.info(f"fetch_google_news: feedparser.parse() completed")
        
        total_articles = len(feed.entries)
        logging.info(f"fetch_google_news: Found {total_articles} entries in feed")
        
        if total_articles == 0:
            logging.info("fetch_google_news: No articles found")
            if verbose:
                print(f'No news found for "{query}".')
            return []
        
        if verbose:
            print(f'✅ Found {total_articles} articles for "{query}".\n')
        
        # Collect articles data
        logging.info("fetch_google_news: Starting to collect article data")
        headlines = []
        for index, item in enumerate(feed.entries, 1):
            headline_data = {
                'title': item.title,
                'published': item.published,
                'source': item.source.title
            }
            headlines.append(headline_data)
            
            if verbose:
                print(f'{index}. {item.title}')
                print(f'   📅 Published: {item.published}')
                print(f'   📰 Source: {item.source.title}\n')
        
        logging.info(f"fetch_google_news: Collected {len(headlines)} headlines, returning")
        return headlines
        
    except Exception as error:
        logging.error(f'fetch_google_news: Exception occurred: {str(error)}', exc_info=True)
        if verbose:
            print(f'Error fetching news for "{query}": {str(error)}')
        return []

def fetch_multiple_news():
    """
    Fetch news for multiple predefined queries concurrently
    """
    # Define search queries
    queries = [
        # "politics",
        # "sports",
        # "economy",
        # "entertainment",
        # "science",
        # "health",
        # "education",
        # "environment",
        # "business",
        # "champions trophy",
        # "indian cricket team",
        # "india vs pakistan",
    ]
    
    days = input("Enter number of days (default 7): ") or "7"
    days = int(days)
    
    # Fetch all queries concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(lambda q: fetch_google_news(q, days), queries)

def fetch_all_categories(categories: Dict[str, str], days: int = 7) -> Dict[str, List[Dict]]:
    """
    Fetch news for all categories in parallel.
    
    Args:
        categories: Dict mapping category name to search query
                   e.g., {"Tech": "technology news", "Business": "business news"}
        days: Number of days to look back (default: 7)
        
    Returns:
        Dict mapping category name to list of headlines
        e.g., {"Tech": [{"title": "...", "published": "...", "source": "..."}]}
    """
    results = {}
    logging.info(f"fetch_all_categories: Starting parallel fetch for {len(categories)} categories")
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Submit all fetch tasks
        future_to_category = {
            executor.submit(fetch_google_news, query, days, False): category
            for category, query in categories.items()
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_category):
            category = future_to_category[future]
            try:
                headlines = future.result()
                results[category] = headlines
                logging.info(f"fetch_all_categories: {category} completed with {len(headlines)} headlines")
            except Exception as e:
                logging.error(f"fetch_all_categories: {category} failed with error: {str(e)}")
                results[category] = []  # Empty list on error
    
    logging.info(f"fetch_all_categories: All categories fetched. Total: {sum(len(h) for h in results.values())} headlines")
    return results


if __name__ == "__main__":
    # fetch_multiple_news()
    fetch_google_news("technology news", 7)