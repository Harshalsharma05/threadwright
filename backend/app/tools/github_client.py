# This tool queries the public GitHub REST API to measure developer engagement and activity related to a company name or organization. It uses httpx.AsyncClient and includes the optional GITHUB_TOKEN header to avoid strict rate-limiting on anonymous requests.
import httpx
import logging
from ..config import settings

logger = logging.getLogger(__name__)

async def get_repos(node_input: dict) -> dict:
    """
    Queries public repositories on GitHub matching a company name or query.
    
    Expected input format: {"org_name": "company_name"} or {"query": "search_query"}
    """
    # Accept either org_name or query as input keys
    query = node_input.get("org_name") or node_input.get("query")
    if not query:
        raise ValueError("Missing required key 'org_name' or 'query' in node input.")

    # Format query to check for organization matches or general keyword searches
    search_query = f"org:{query}" if "org_name" in node_input else query
    url = f"https://api.github.com/search/repositories?q={search_query}&sort=stars&order=desc"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "threadwright-orchestrator"
    }

    # Inject Authorization header if a GITHUB_TOKEN is configured
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
        logger.debug("GitHub Token injected into request headers.")
    else:
        logger.warning("No GitHub Token provided. Requests will be subject to lower rate limits.")

    logger.info(f"Querying GitHub search API with: '{search_query}'")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        
        # If trying to search by org fail-safes (e.g. if the org name doesn't exist),
        # fall back to a general repository keyword search.
        if response.status_code == 422 and "org_name" in node_input:
            logger.warning(f"Organization search failed for '{query}'. Retrying with general keyword search.")
            fallback_url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
            response = await client.get(fallback_url, headers=headers)

        if response.status_code != 200:
            error_text = response.text
            logger.error(f"GitHub API error (Status {response.status_code}): {error_text}")
            response.raise_for_status()

        data = response.json()
        items = data.get("items", [])[:5]  # Take top 5 most relevant repositories

        formatted_repos = []
        for repo in items:
            formatted_repos.append({
                "name": repo.get("full_name", "No Name"),
                "url": repo.get("html_url", ""),
                "description": repo.get("description", ""),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", "Unknown")
            })

        return {
            "search_query": query,
            "repositories": formatted_repos,
            "sources": [
                {"title": repo["name"], "url": repo["url"]} 
                for repo in formatted_repos
            ]
        }