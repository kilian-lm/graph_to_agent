#!/usr/bin/env python3
"""
Expert Wire-Box Example

This example demonstrates the "Wire-Box" concept - allowing domain experts
to encode their knowledge into reusable agent pools.

The idea is that experts in fields like psychology, physics, medicine, etc.
can create structured agent interactions that unlock domain-specific
reasoning patterns in LLMs.

Graph Structure (Multi-Agent Review):

    Expert1 (Skeptic) ──────┐
                            ├──> Meta-Agent (Synthesizer)
    Expert2 (Optimist) ─────┘

Each expert agent provides a different perspective on the problem,
and the meta-agent synthesizes their views.
"""

import json


def create_multi_perspective_graph(problem_description):
    """
    Create a multi-agent graph where multiple expert perspectives
    are synthesized by a meta-agent.
    """
    return {
        "nodes": [
            # Agent 1: The Skeptic
            {"id": "user_skeptic", "label": "user"},
            {
                "id": "skeptic_briefing",
                "label": f"""You are Agent-Skeptic. Your role is to critically examine proposals
and identify potential flaws, risks, and unintended consequences.
Analyze the following from a skeptical perspective: {problem_description}""",
            },
            {"id": "system_skeptic", "label": "system"},
            {
                "id": "skeptic_ack",
                "label": "Understood. I will provide a critical analysis focusing on risks and flaws.",
            },
            # Agent 2: The Optimist
            {"id": "user_optimist", "label": "user"},
            {
                "id": "optimist_briefing",
                "label": f"""You are Agent-Optimist. Your role is to identify opportunities,
potential benefits, and positive outcomes.
Analyze the following from an optimistic perspective: {problem_description}""",
            },
            {"id": "system_optimist", "label": "system"},
            {
                "id": "optimist_ack",
                "label": "Understood. I will focus on opportunities and positive potential.",
            },
            # Meta-Agent: The Synthesizer
            {"id": "user_meta", "label": "user"},
            {
                "id": "meta_briefing",
                "label": """You are the Meta-Agent. You have received analyses from two expert agents:
1. Agent-Skeptic (critical perspective)
2. Agent-Optimist (opportunity-focused perspective)

Synthesize their viewpoints into a balanced recommendation.
Consider: What risks need mitigation? What opportunities should be pursued?
Provide a final recommendation.""",
            },
            {"id": "system_meta", "label": "system"},
            {
                "id": "meta_ack",
                "label": "I will synthesize both perspectives into a balanced recommendation.",
            },
            # Variable placeholders for agent responses
            {"id": "user_synthesis", "label": "user"},
            {
                "id": "synthesis_input",
                "label": """Agent-Skeptic's analysis: @variable_skeptic

Agent-Optimist's analysis: @variable_optimist

Please provide your synthesis and final recommendation.""",
            },
        ],
        "edges": [
            # Skeptic chain
            {"from": "user_skeptic", "to": "skeptic_briefing"},
            {"from": "skeptic_briefing", "to": "system_skeptic"},
            {"from": "system_skeptic", "to": "skeptic_ack"},
            # Optimist chain
            {"from": "user_optimist", "to": "optimist_briefing"},
            {"from": "optimist_briefing", "to": "system_optimist"},
            {"from": "system_optimist", "to": "optimist_ack"},
            # Meta-agent chain
            {"from": "user_meta", "to": "meta_briefing"},
            {"from": "meta_briefing", "to": "system_meta"},
            {"from": "system_meta", "to": "meta_ack"},
            {"from": "meta_ack", "to": "user_synthesis"},
            {"from": "user_synthesis", "to": "synthesis_input"},
        ],
    }


def identify_subgraphs(nodes, edges):
    """
    Identify disconnected subgraphs (separate agent chains).
    Returns list of root node IDs for each subgraph.
    """
    # Find all nodes that are never targets
    target_ids = {edge["to"] for edge in edges}
    root_nodes = [node["id"] for node in nodes if node["id"] not in target_ids]
    return root_nodes


def populate_variables(graph, variable_values):
    """
    Replace @variable_* placeholders with actual values.

    Args:
        graph: The graph data structure
        variable_values: Dict mapping variable names to values
                        e.g., {'skeptic': 'Risk analysis...', 'optimist': 'Opportunity...'}
    """
    for node in graph["nodes"]:
        for var_name, var_value in variable_values.items():
            placeholder = f"@variable_{var_name}"
            if placeholder in node["label"]:
                node["label"] = node["label"].replace(placeholder, var_value)
    return graph


def main():
    """Main execution demonstrating the Wire-Box pattern."""
    print("Graph-to-Agent: Expert Wire-Box Example")
    print("=" * 60)

    # Define a problem for multi-agent analysis
    problem = """
    A startup is considering pivoting from B2C to B2B model.
    They have 6 months of runway and 10,000 existing users.
    Should they proceed with the pivot?
    """

    print(f"\nProblem Description:\n{problem}")

    # Create the multi-perspective graph
    graph = create_multi_perspective_graph(problem)

    print("\n1. Created Wire-Box with agents:")
    print("   - Agent-Skeptic (critical analysis)")
    print("   - Agent-Optimist (opportunity analysis)")
    print("   - Meta-Agent (synthesis)")

    # Identify the subgraphs (each agent chain)
    roots = identify_subgraphs(graph["nodes"], graph["edges"])
    print(f"\n2. Identified {len(roots)} agent chains (root nodes: {roots})")

    # Simulate agent responses (in real usage, these come from GPT)
    simulated_responses = {
        "skeptic": """RISKS IDENTIFIED:
1. Losing 10,000 existing users means losing product-market fit validation
2. B2B sales cycles are longer - 6 months may not be enough
3. Different skill sets needed for B2B (enterprise sales, compliance)
4. Pivot signals instability to potential investors""",
        "optimist": """OPPORTUNITIES IDENTIFIED:
1. B2B typically has higher LTV and more predictable revenue
2. Existing users could become initial B2B champions
3. 6 months is enough for a focused MVP and first enterprise deals
4. Pivot shows adaptability - many successful companies pivoted""",
    }

    # Populate variables
    graph = populate_variables(graph, simulated_responses)

    print("\n3. After variable substitution, the synthesis prompt contains:")
    for node in graph["nodes"]:
        if "synthesis_input" in node["id"]:
            print(f"\n{node['label'][:500]}...")

    print("\n4. Execution Flow:")
    print("   Step 1: Run Skeptic agent chain -> get @variable_skeptic")
    print("   Step 2: Run Optimist agent chain -> get @variable_optimist")
    print("   Step 3: Substitute variables into Meta-agent chain")
    print("   Step 4: Run Meta-agent for final synthesis")

    print("\n" + "=" * 60)
    print("This Wire-Box pattern allows domain experts to encode")
    print("multi-perspective analysis workflows that can be reused")
    print("across different problem domains.")


if __name__ == "__main__":
    main()
