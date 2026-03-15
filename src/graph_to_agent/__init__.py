"""
Graph-to-Agent: Visual Agent Orchestration Framework

Build multi-agent LLM systems using graph-based visual programming.

Quick Start:
    from graph_to_agent import GraphOrchestrator

    # Create an orchestrator
    orchestrator = GraphOrchestrator()

    # Define a simple agent graph
    graph = {
        "nodes": [
            {"id": "1", "label": "user"},
            {"id": "2", "label": "You are a helpful assistant"},
            {"id": "3", "label": "system"},
            {"id": "4", "label": "I'll help you with any task"},
        ],
        "edges": [
            {"from": "1", "to": "2"},
            {"from": "2", "to": "3"},
            {"from": "3", "to": "4"},
        ]
    }

    # Convert to GPT messages
    messages = orchestrator.graph_to_messages(graph)

    # Execute (requires OPENAI_API_KEY env var)
    response = orchestrator.execute(graph)
"""

__version__ = "0.2.0"
__author__ = "Kilian Lehn"

from graph_to_agent.core.orchestrator import GraphOrchestrator
from graph_to_agent.core.engine import EngineRoom
from graph_to_agent.core.translator import GraphTranslator

__all__ = [
    "GraphOrchestrator",
    "EngineRoom",
    "GraphTranslator",
    "__version__",
]
