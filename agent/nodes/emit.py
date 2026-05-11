import csv
import os
from agent.state import TicketState

_batch: list[dict] = []

CAMPOS_OBRIGATORIOS = {
    "ticket_id", "priority", "category",
    "service_type", "queue", "route_decision",
    "priority_justification", "classification_justification",
}

def run(state: TicketState) -> dict:

    # campos obrigatórios faltando
    campos_faltando = CAMPOS_OBRIGATORIOS - state.keys()
    if campos_faltando:
        raise RuntimeError(
            f"emit: campos obrigatórios ausentes no ticket "
            f"{state.get('ticket_id', 'DESCONHECIDO')}: {campos_faltando}"
        )

    # route_decision inválido
    rotas_validas = {"draft", "queue"}
    if state.get("route_decision") not in rotas_validas:
        raise RuntimeError(
            f"emit: route_decision inválido '{state.get('route_decision')}' "
            f"no ticket {state['ticket_id']}. "
            f"Esperado: {rotas_validas}"
        )

    _batch.append({
        "ticket_id":                    state["ticket_id"],
        "priority":                     state["priority"],
        "category":                     state["category"],
        "service_type":                 state["service_type"],
        "queue":                        state["queue"],
        "route_decision":               state["route_decision"],
        "priority_justification":       state["priority_justification"],
        "classification_justification": state["classification_justification"],
        "has_draft":                    bool(state.get("draft_response")),
    })

    return {}

def save_csv(path: str = "outputs/results.csv"):

    # nada para salvar
    if not _batch:
        raise RuntimeError("emit: nenhum chamado foi processado, CSV não gerado.")

    try:
        os.makedirs("outputs", exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_batch[0].keys())
            writer.writeheader()
            writer.writerows(_batch)
        print(f"{len(_batch)} chamados salvos em {path}")

    except PermissionError:
        raise RuntimeError(
            f"emit: sem permissão para salvar o arquivo em '{path}'"
        )
    except OSError as e:
        raise RuntimeError(
            f"emit: erro ao salvar CSV em '{path}': {e}"
        )
