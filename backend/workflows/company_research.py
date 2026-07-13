# backend/workflows/company_research.py
from app.models import GraphDefinition, NodeDefinition, NodeType
from app.tools.tavily_client import search_news
from app.tools.github_client import get_repos
from app.tools.reddit_client import search_posts
from app.tools.llm_client import parse_job_posting, synthesize_brief

# The Central Node Registry
# NODE_REGISTRY = {
#     "tools.tavily_client.search_news": search_news,
#     "tools.github_client.get_repos": get_repos,
#     "tools.reddit_client.search_posts": search_posts,
#     "tools.llm_client.parse_job_posting": parse_job_posting,
#     "tools.llm_client.synthesize_brief": synthesize_brief
# }

# The Production Company Research Graph Definition
nodes = [
    NodeDefinition(
        id="search_news",
        type=NodeType.TOOL,
        handler="tavily_search",
        depends_on=[],
        input_mapping={"query": {"from_input": "company_name"}}
    ),
    NodeDefinition(
        id="github_signal",
        type=NodeType.TOOL,
        handler="github_search",
        depends_on=[],
        input_mapping={"query": {"from_input": "company_name"}}
    ),
    NodeDefinition(
        id="reddit_signal",
        type=NodeType.TOOL,
        handler="reddit_search",
        depends_on=[],
        input_mapping={"query": {"from_input": "company_name"}}
    ),
    NodeDefinition(
        id="parse_job",
        type=NodeType.LLM,
        handler="parse_job_posting",
        depends_on=[],
        input_mapping={
            "company_name": {"from_input": "company_name"},
            # NEW ADDITION: Map the optional JD to the 'raw_jd' key for the LLM tool
            "raw_jd": {"from_input": "job_description"} 
        }
    ),
    NodeDefinition(
        id="synthesize",
        type=NodeType.LLM,
        handler="synthesize_brief",
        # Synthesis waits for all 4 parallel tasks to finish
        depends_on=["search_news", "github_signal", "reddit_signal", "parse_job"], 
        input_mapping={
            "company_name": {"from_input": "company_name"},
            "news_data": {"from_node": "search_news"},
            "github_data": {"from_node": "github_signal"},
            "reddit_data": {"from_node": "reddit_signal"},
            "job_data": {"from_node": "parse_job"}
        }
    )
]

COMPANY_RESEARCH_GRAPH = GraphDefinition(
    name="Company Research Brief",
    nodes=nodes
)

NODE_REGISTRY = {
    "tavily_search": search_news,
    "github_search": get_repos,
    "reddit_search": search_posts,
    "parse_job_posting": parse_job_posting,
    "synthesize_brief": synthesize_brief
}