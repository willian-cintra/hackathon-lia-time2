from langgraph.graph import StateGraph, START, END
from agent.state import TicketState
from agent.nodes import ingest, score_priority, classify_type
from agent.nodes import draft_response, queue_only, emit


def route_fn(state: TicketState) -> str:
    if (
        state.get("priority") in ("Médio", "Baixo")
        and state.get("category") == "Requisição"
    ):
        return "draft"
    return "queue"


def build_graph() -> StateGraph:
    g = StateGraph(TicketState)

    g.add_node("ingest",         ingest.run)
    g.add_node("score_priority", score_priority.run)
    g.add_node("classify_type",  classify_type.run)
    g.add_node("draft_response", draft_response.run)
    g.add_node("queue_only",     queue_only.run)
    g.add_node("emit",           emit.run)

    g.add_edge(START,            "ingest")
    g.add_edge("ingest",         "score_priority")
    g.add_edge("score_priority", "classify_type")

    g.add_conditional_edges(
        "classify_type",
        route_fn,
        {"draft": "draft_response", "queue": "queue_only"}
    )

    g.add_edge("draft_response", "emit")
    g.add_edge("queue_only",     "emit")
    g.add_edge("emit",           END)

    return g.compile()


graph = build_graph()
