from agent.state import TicketState


def run(state: TicketState) -> dict:
    """Nó queue_only — caminho para chamados que vão para fila sem resposta automática.

    Sem chamada LLM. Existe para:
    1. Tornar o caminho explícito no grafo
    2. Registrar route_decision = "queue" no estado para auditoria
    """
    return {"route_decision": "queue"}
