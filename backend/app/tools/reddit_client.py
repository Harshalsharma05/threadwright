# This tool retrieves social signals and public sentiment about a company from Reddit.
# Architectural Detail: Because the Python Reddit API Wrapper (praw) is a synchronous library, running it directly inside an async def function would block the main execution thread, halting the entire async event loop. To prevent this, we wrap the blocking PRAW calls in asyncio.to_thread, which executes them in a separate thread pool.

import asyncio
import logging
import praw
from ..config import settings

logger = logging.getLogger(__name__)

def _sync_reddit_search(query: str) -> list[dict]:
    """
    Synchronous helper to execute the PRAW API request.
    Executed in a separate worker thread to avoid blocking the event loop.
    """
    # Defensive checks for API keys
    if not all([settings.reddit_client_id, settings.reddit_client_secret, settings.reddit_user_agent]):
        logger.warning("Reddit API credentials not fully configured. Returning simulated fallback data.")
        return [
            {
                "title": f"Is {query} a good company to work for?",
                "url": "https://reddit.com/r/cscareerquestions/mock",
                "score": 42,
                "num_comments": 15
            },
            {
                "title": f"Why {query} is dominating the current market trend",
                "url": "https://reddit.com/r/technology/mock",
                "score": 120,
                "num_comments": 34
            }
        ]

    reddit = praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent
    )

    logger.info(f"Querying Reddit API for: '{query}'")
    
    # Perform general keyword search across r/all
    search_results = reddit.subreddit("all").search(query, sort="relevance", limit=5)
    
    posts = []
    for post in search_results:
        posts.append({
            "title": post.title,
            "url": f"https://reddit.com{post.permalink}",
            "score": post.score,
            "num_comments": post.num_comments
        })
    return posts


async def search_posts(node_input: dict) -> dict:
    """
    Asynchronously queries Reddit posts for social signal analysis.
    Wraps blocking PRAW queries using asyncio.to_thread.
    
    Expected input format: {"query": "some search query"}
    """
    query = node_input.get("query")
    if not query:
        raise ValueError("Missing required key 'query' in node input.")

    # Execute blocking task in a background thread
    posts = await asyncio.to_thread(_sync_reddit_search, query)

    return {
        "query": query,
        "posts": posts
    }