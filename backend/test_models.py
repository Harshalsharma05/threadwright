# backend/test_models.py
import sys
from app.models import GraphDefinition, NodeType

def test_graph_validation():
    print("Testing Pydantic model validation on target workflow...")
    
    # Target 5-node workflow
    sample_workflow = {
        "name": "company_research_flow",
        "nodes": [
            {
                "id": "search_news",
                "type": NodeType.TOOL,
                "handler": "tools.tavily_client.search_news",
                "depends_on": [],
                "max_retries": 2,
                "input_mapping": {"query": "company_name"}
            },
            {
                "id": "github_signal",
                "type": NodeType.TOOL,
                "handler": "tools.github_client.get_repos",
                "depends_on": [],
                "max_retries": 2,
                "input_mapping": {"org_name": "company_name"}
            },
            {
                "id": "reddit_signal",
                "type": NodeType.TOOL,
                "handler": "tools.reddit_client.search_posts",
                "depends_on": [],
                "max_retries": 1,
                "input_mapping": {"query": "company_name"}
            },
            {
                "id": "parse_job",
                "type": NodeType.LLM,
                "handler": "tools.llm_client.parse_job_posting",
                "depends_on": [],
                "max_retries": 2,
                "input_mapping": {"company": "company_name"}
            },
            {
                "id": "synthesize",
                "type": NodeType.LLM,
                "handler": "tools.llm_client.synthesize_brief",
                "depends_on": ["search_news", "github_signal", "reddit_signal", "parse_job"],
                "max_retries": 2,
                "input_mapping": {
                    "news": "search_news",
                    "github": "github_signal",
                    "reddit": "reddit_signal",
                    "jobs": "parse_job"
                }
            }
        ]
    }

    try:
        validated_graph = GraphDefinition(**sample_workflow)
        print("Graph definition parsed and validated successfully.")
        print(f"Graph Name: {validated_graph.name}")
        print(f"Total Nodes: {len(validated_graph.nodes)}")
        
        # Verify basic dependency structure
        synthesis_node = next(n for n in validated_graph.nodes if n.id == "synthesize")
        print(f"Synthesis node dependency count: {len(synthesis_node.depends_on)}")
        assert len(synthesis_node.depends_on) == 4, "Synthesis node should depend on 4 upstream nodes."
        
    except Exception as e:
        print(f"Model validation failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_graph_validation()