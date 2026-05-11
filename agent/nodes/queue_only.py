from agent.state import TicketState

CAMPOS_OBRIGATORIOS = {"ticket_id", "priority", "category"}

def run(state: TicketState) -> dict:

    # campos obrigatórios faltando
    campos_faltando = CAMPOS_OBRIGATORIOS - state.keys()
    if campos_faltando:
        raise RuntimeError(
            f"queue_only: campos obrigatórios ausentes no ticket "
            f"{state.get('ticket_id', 'DESCONHECIDO')}: {campos_faltando}"
        )

    # prioridade inválida
    prioridades_validas = {"Crítico", "Alto", "Médio", "Baixo"}
    if state["priority"] not in prioridades_validas:
        raise RuntimeError(
            f"queue_only: prioridade inválida '{state['priority']}' "
            f"no ticket {state['ticket_id']}. "
            f"Esperado: {prioridades_validas}"
        )

    # categoria inválida
    categorias_validas = {"Requisição", "Incidente", "Problema"}
    if state["category"] not in categorias_validas:
        raise RuntimeError(
            f"queue_only: categoria inválida '{state['category']}' "
            f"no ticket {state['ticket_id']}. "
            f"Esperado: {categorias_validas}"
        )

    return {"route_decision": "queue"}
