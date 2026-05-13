import csv
import json
import os
import time
from datetime import datetime
from agent.state import TicketState

OUTPUT_DIR = "outputs"

CAMPOS_OBRIGATORIOS = {
    "ticket_id", "priority", "category",
    "service_type", "queue", "route_decision",
    "priority_justification", "classification_justification",
}

def run(state: TicketState) -> dict:
    campos_faltando = CAMPOS_OBRIGATORIOS - state.keys()
    if campos_faltando:
        raise RuntimeError(
            f"emit: campos obrigatórios ausentes no ticket "
            f"{state.get('ticket_id', 'DESCONHECIDO')}: {campos_faltando}"
        )

    rotas_validas = {"draft", "queue"}
    if state.get("route_decision") not in rotas_validas:
        raise RuntimeError(
            f"emit: route_decision inválido '{state.get('route_decision')}' "
            f"no ticket {state['ticket_id']}"
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    entry = {
        "ticket_id":                    state["ticket_id"],
        "priority":                     state["priority"],
        "category":                     state["category"],
        "service_type":                 state["service_type"],
        "queue":                        state["queue"],
        "route_decision":               state["route_decision"],
        "priority_justification":       state["priority_justification"],
        "classification_justification": state["classification_justification"],
        "draft_response":               state.get("draft_response", ""),
        "draft_closure":                state.get("draft_closure", ""),
    }

    # JSON individual por ticket
    json_path = os.path.join(OUTPUT_DIR, f"{state['ticket_id']}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)

    # CSV acumulativo (append)
    csv_path = os.path.join(OUTPUT_DIR, "results.csv")
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

    print(f"[emit] {state['ticket_id']} → {state['route_decision']} | salvo em {json_path}")
    return {}