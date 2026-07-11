from pydantic import BaseModel
from typing import Literal, Optional
from enum import Enum

class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

class NodeType(str, Enum):
    TOOL = "tool"       # e.g. tavily search, github search, reddit search
    LLM = "llm"         # e.g. synthesis, job-posting parse
    FUNCTION = "function"  # plain python logic, no external call

class NodeDefinition(BaseModel):
    id: str                  # unique within a graph, e.g. "search_news"
    type: NodeType
    handler: str              # dotted path or registry key, e.g. "tools.tavily_client.search_news"
    depends_on: list[str] = []
    max_retries: int = 2
    input_mapping: dict = {}  # how to build this node's input from prior node outputs + run input

class GraphDefinition(BaseModel):
    name: str
    nodes: list[NodeDefinition]