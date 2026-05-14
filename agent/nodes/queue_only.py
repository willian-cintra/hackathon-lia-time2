# agent/nodes/queue_only.py
import json
import os
from datetime import datetime
from agent.state import TicketState
from agent.config import QUEUE_PATH
from agent.logger import get_logger

logger = get_logger(__name__)

CAMPOS_OBRIGATORIOS = {"ticket_id", "priority", "category"}
PRIORIDADES_VALIDAS = {"Crítico", "Alto", "Médio", "Baixo"}
CATEGORIAS_VALIDAS  = {"Requisição", "Incidente", "Problema"}

def run(state: TicketState) -> dict:
    campos_faltando = CAMPOS_OBRIGATORIOS - state.keys()
    if campos_faltando:
        raise RuntimeError(
            f"queue_only: campos ausentes no ticket "
            f"{state.get('ticket_id', 'DESCONHECIDO')}: {campos_faltando}"
        )

    if state["priority"] not in PRIORIDADES_VALIDAS:
        raise RuntimeError(
            f"queue_only: prioridade inválida '{state['priority']}' "
            f"no ticket {state['ticket_id']}"
        )

    if state["category"] not in CATEGORIAS_VALIDAS:
        raise RuntimeError(
            f"queue_only: categoria inválida '{state['category']}' "
            f"no ticket {state['ticket_id']}"
        )

    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp":                    datetime.now().isoformat(),
        "ticket_id":                    state["ticket_id"],
        "text":                         state["text"],
        "priority":                     state["priority"],
        "category":                     state["category"],
        "queue":                        state.get("queue", ""),
        "priority_justification":       state.get("priority_justification", ""),
        "classification_justification": state.get("classification_justification", ""),
        "reason":                       "Prioridade alta ou categoria complexa — requer analista humano.",
    }

    try:
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            fila = json.load(f)
    except FileNotFoundError:
        fila = []

    fila.append(entry)

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(fila, f, ensure_ascii=False, indent=2)

    logger.info("%s → fila humana (total na fila: %d)", state["ticket_id"], len(fila))
    return {"route_decision": "queue"}