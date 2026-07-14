import httpx
import logging
from ..config import settings

logger = logging.getLogger(__name__)

_synthetic_failures: dict[str, int] = {}

async def search_news(node_input: dict) -> dict:
    """
    Performs an asynchronous web search using the Tavily API.
    
    Expected input format: {"query": "some search query"}
    """
    query = node_input.get("query")
    if not query:
        raise ValueError("Missing required key 'query' in node input.")
    
    
     # Stateful Fault Injection Logic
    inject_failure = node_input.get("inject_failure", False)
    run_id = node_input.get("workflow_run_id", "local-test")

    if inject_failure:
        current_fails = _synthetic_failures.get(run_id, 0)
        if current_fails < 2:
            _synthetic_failures[run_id] = current_fails + 1
            logger.warning(f"[FAULT INJECTION] Simulating synthetic failure for run {run_id} (Attempt {current_fails + 1}/2)")
            raise RuntimeError("Synthetic Connection Timeout (Simulated Downstream Error).")
        else:
            logger.info(f"[FAULT INJECTION] Attempt limit reached for run {run_id}. Allowing third attempt to pass.")

    api_key = settings.tavily_api_key
    if not api_key:
        raise ValueError("Tavily API key is missing from environment variables.")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": f"{query} competitors list market share",
        "search_depth": "basic",
        "include_answer": False,
        "max_results": 5
    }

    logger.info(f"Querying Tavily search API for: '{query}'")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"Tavily search API error (Status {response.status_code}): {error_text}")
            response.raise_for_status()

        data = response.json()
        
        # Clean and format the raw results for downstream consumption by an LLM
        formatted_results = []
        for item in data.get("results", []):
            formatted_results.append({
                "title": item.get("title", "No Title"),
                "url": item.get("url", ""),
                "content": item.get("content", "")
            })

        return {
            "query": query,
            "results": formatted_results,
            "sources": [
                {"title": item["title"], "url": item["url"]} 
                for item in formatted_results
            ]
        }