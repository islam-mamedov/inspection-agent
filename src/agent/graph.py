from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent import nodes

MAX_REWRITES = 2
MIN_RELEVANT = 2  # fewer than this = weak retrieval -> try rewriting


def decide_after_grading(state: AgentState) -> str:
    """The agent's key decision: is the evidence good enough?"""
    if len(state["relevant"]) >= MIN_RELEVANT:
        return "generate"
    if state["rewrite_count"] < MAX_REWRITES:
        return "rewrite"
    return "generate"  # out of retries - generate from whatever we have (or refuse)


def route_input(state: AgentState) -> str:
    return "analyze_image" if state["image_path"] else "plan_queries"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("analyze_image", nodes.analyze_image)
    g.add_node("plan_queries", nodes.plan_queries)
    g.add_node("retrieve", nodes.retrieve)
    g.add_node("grade", nodes.grade)
    g.add_node("rewrite", nodes.rewrite)
    g.add_node("generate", nodes.generate)

    g.set_conditional_entry_point(route_input,
                                  {"analyze_image": "analyze_image", "plan_queries": "plan_queries"})
    g.add_edge("analyze_image", "plan_queries")
    g.add_edge("plan_queries", "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", decide_after_grading,
                            {"generate": "generate", "rewrite": "rewrite"})
    g.add_edge("rewrite", "retrieve")
    g.add_edge("generate", END)
    return g.compile()