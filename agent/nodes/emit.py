import csv
import json
import os
import time
from datetime import datetime
from agent.state import TicketState
from agent.config import OUTPUTS_DIR, LOG_JSONL_PATH, RESULTS_CSV_PATH
from agent.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = OUTPUTS_DIR
LOG_PATH   = LOG_JSONL_PATH

CAMPOS_OBRIGATORIOS = {
    "ticket_id", "priority", "category",
    "service_type", "queue", "route_decision",
    "priority_justification", "classification_justification",
}

# ID único da execução — gerado uma vez no import, compartilhado por todos os tickets
_EXECUTION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")


def run(state: TicketState) -> dict:
    inicio = time.time()

    # ── Validações ────────────────────────────────────────────────────────────
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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tokens = state.get("tokens_used", 0)

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
        "tokens_used":                  tokens,
    }

    # ── JSON individual por ticket ────────────────────────────────────────────
    json_path = OUTPUT_DIR / f"{state['ticket_id']}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)

    # ── CSV acumulativo ───────────────────────────────────────────────────────
    csv_path    = RESULTS_CSV_PATH
    file_exists = csv_path.is_file()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

    # ── Log estruturado JSONL ─────────────────────────────────────────────────
    processing_ms = round((time.time() - inicio) * 1000)

    log_entry = {
        "execution_id":                 _EXECUTION_ID,
        "timestamp":                    datetime.now().isoformat(),
        "ticket_id":                    state["ticket_id"],
        "processing_ms":                processing_ms,
        "tokens_used":                  tokens,
        "route_decision":               state["route_decision"],
        "category":                     state["category"],
        "priority":                     state["priority"],
        "urgency":                      state.get("urgency", ""),
        "impact":                       state.get("impact", ""),
        "service_type":                 state["service_type"],
        "queue":                        state["queue"],
        "priority_justification":       state["priority_justification"],
        "classification_justification": state["classification_justification"],
        "has_draft":                    bool(state.get("draft_response")),
    }

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    logger.info(
        "%s | categoria=%-10s prioridade=%-8s rota=%-5s tokens=%s latencia=%dms",
        state["ticket_id"],
        state["category"],
        state["priority"],
        state["route_decision"],
        f"{tokens:,}",
        processing_ms,
    )
    return {}
