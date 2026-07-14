# diagnostic test to verify that all real API clients are working end-to-end in a single workflow run
import asyncio
import sys
from workflows.company_research import NODE_REGISTRY

async def main():
    test_company = "stripe"
    print(f"Starting end-to-end integration test of real API clients for: '{test_company}'\n")

    # 1. Test Tavily Web Search
    print("--- Testing Tavily Client ---")
    try:
        tavily_fn = NODE_REGISTRY["tools.tavily_client.search_news"]
        news_result = await tavily_fn({"query": f"{test_company} market news"})
        print(f"Tavily success! Retrieved {len(news_result.get('results', []))} results.")
    except Exception as e:
        print(f"Tavily client failed: {e}", file=sys.stderr)
        news_result = {}

    # 2. Test GitHub API Search
    print("\n--- Testing GitHub Client ---")
    try:
        github_fn = NODE_REGISTRY["tools.github_client.get_repos"]
        github_result = await github_fn({"org_name": test_company})
        print(f"GitHub success! Retrieved {len(github_result.get('repositories', []))} repos.")
    except Exception as e:
        print(f"GitHub client failed: {e}", file=sys.stderr)
        github_result = {}

    # 3. Test Reddit Client
    print("\n--- Testing Reddit Client (via threadpool) ---")
    try:
        reddit_fn = NODE_REGISTRY["tools.reddit_client.search_posts"]
        reddit_result = await reddit_fn({"query": test_company})
        print(f"Reddit success! Retrieved {len(reddit_result.get('posts', []))} posts.")
    except Exception as e:
        print(f"Reddit client failed: {e}", file=sys.stderr)
        reddit_result = {}

    # 4. Test LLM Parse Job Landscape
    print("\n--- Testing LLM Job Parser Client ---")
    try:
        jobs_fn = NODE_REGISTRY["tools.llm_client.parse_job_posting"]
        jobs_result = await jobs_fn({"company": test_company})
        print("LLM job parsing successful. Result keys returned:")
        print(list(jobs_result.keys()))
    except Exception as e:
        print(f"LLM jobs client failed: {e}", file=sys.stderr)
        jobs_result = {}

    # 5. Test Unified Brief Synthesis
    print("\n--- Testing Unified Synthesis Client ---")
    try:
        synthesis_payload = {
            "news": news_result,
            "github": github_result,
            "reddit": reddit_result,
            "jobs": jobs_result
        }
        synth_fn = NODE_REGISTRY["tools.llm_client.synthesize_brief"]
        brief_result = await synth_fn(synthesis_payload)
        print("Synthesis successful! executive_summary preview:")
        print(brief_result.get("executive_summary", "Missing executive summary"))
    except Exception as e:
        print(f"LLM synthesis client failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())