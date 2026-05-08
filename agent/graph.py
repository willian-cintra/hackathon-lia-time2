from langgraph.graph import StateGraph, START, END
from agent.state import TicketState
from agent.nodes import ingest, score_priority, classify_type
from agent.nodes import draft_response, queue_only, emit


def route_fn(state: TicketState) -> str:
    """Função de roteamento — DETERMINÍSTICA, sem LLM.

    Retorna 'draft' apenas quando TODAS as condições são satisfeitas:
    - Prioridade <= Médio (não é Crítico nem Alto)
    - Categoria = Requisição (Incidente e Problema sempre vão para fila)
    - Sem sinalização de revisão humana pendente

    Qualquer desvio → 'queue'
    """
    if (
        state.get("priority") in ("Médio", "Baixo")
        and state.get("category") == "Requisição"
        and not state.get("needs_human_review", False)
    ):
        return "draft"
    return "queue"


def build_graph() -> StateGraph:
    """Constrói e compila o StateGraph do agente de triagem.

    Ordem dos nós fiel ao BPMN da AGETIC (Versão 4):
    1. ingest          → valida e normaliza entrada
    2. score_priority  → BPMN §1: Priorizar chamado (urgência × impacto → ANS)
    3. classify_type   → BPMN §2: Escalonar chamado (tipo + serviço + fila)
    4. route_fn        → aresta condicional: draft ou queue
    5a. draft_response → atendimento 1° nível (chamados simples)
    5b. queue_only     → registra rota para chamados que vão para fila
    6. emit            → serializa resultado e acumula no batch
    """
    builder = StateGraph(TicketState)

    # Registra nós
    builder.add_node("ingest",         ingest.run)
    builder.add_node("score_priority", score_priority.run)
    builder.add_node("classify_type",  classify_type.run)
    builder.add_node("draft_response", draft_response.run)
    builder.add_node("queue_only",     queue_only.run)
    builder.add_node("emit",           emit.run)

    # Arestas fixas
    builder.add_edge(START,            "ingest")
    builder.add_edge("ingest",         "score_priority")
    builder.add_edge("score_priority", "classify_type")

    # Aresta condicional após classify_type
    builder.add_conditional_edges(
        "classify_type",
        route_fn,
        {"draft": "draft_response", "queue": "queue_only"},
    )

    # Convergência para emit
    builder.add_edge("draft_response", "emit")
    builder.add_edge("queue_only",     "emit")
    builder.add_edge("emit",           END)

    return builder.compile()


# Instância global reutilizável
graph = build_graph()
