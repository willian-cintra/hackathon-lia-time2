import json
import time
import uuid
from agent.state import TicketState

# Lista acumulada em memória durante o batch
# Em produção, substituir por escrita incremental em arquivo
_batch_results: list[dict] = []


def run(state: TicketState) -> dict:
    """Nó emit — serializa e registra o resultado final do chamado.

    Registra no estado final:
    - execution_id: UUID único para rastreabilidade
    - Acumula resultado no batch para geração do CSV ao final
    """
    execution_id = str(uuid.uuid4())[:8]

    result = {
        "execution_id":   execution_id,
        "ticket_id":      state.get("ticket_id"),
        "priority":       state.get("priority"),
        "category":       state.get("category"),
        "service_type":   state.get("service_type"),
        "queue":          state.get("queue"),
        "route_decision": state.get("route_decision"),
        "needs_human_review": state.get("needs_human_review", False),
        "priority_justification":        state.get("priority_justification", ""),
        "classification_justification":  state.get("classification_justification", ""),
        "has_draft_response": bool(state.get("draft_response")),
        "errors": state.get("errors", []),
    }

    _batch_results.append(result)
    return {}


def get_batch_results() -> list[dict]:
    """Retorna todos os resultados acumulados no batch atual."""
    return _batch_results.copy()


def reset_batch():
    """Limpa o batch — chamar entre execuções de datasets distintos."""
    global _batch_results
    _batch_results = []


def save_batch_csv(path: str = "outputs/results.csv"):
    """Salva os resultados do batch em CSV para análise de acurácia."""
    import csv, os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not _batch_results:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_batch_results[0].keys())
        writer.writeheader()
        writer.writerows(_batch_results)
    print(f"Resultados salvos em {path} ({len(_batch_results)} chamados)")
