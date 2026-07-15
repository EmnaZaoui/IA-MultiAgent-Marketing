from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import (
    researcher_node,
    strategist_node,
    copywriter_node,
    compliance_node,
    increment_revision_node,
)


def route_after_compliance(state: AgentState) -> str:
    """Arête conditionnelle: implémente la boucle de critique QA -> Copywriter."""
    if state.get("error"):
        return "end"

    if state.get("critique_status") == "APPROVED":
        return "end"

    if state.get("revision_count", 0) >= state.get("max_retries", 3):
        return "end"

    return "retry"


def build_marketing_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("strategist", strategist_node)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("compliance", compliance_node)
    graph.add_node("increment_revision", increment_revision_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "strategist")
    graph.add_edge("strategist", "copywriter")
    graph.add_edge("copywriter", "compliance")

    graph.add_conditional_edges(
        "compliance",
        route_after_compliance,
        {"retry": "increment_revision", "end": END},
    )
    graph.add_edge("increment_revision", "copywriter")

    return graph.compile()



marketing_agent_graph = build_marketing_agent_graph()