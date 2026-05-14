# agent/nodes/classify_type.py
import json
from pathlib import Path
from agent.state import TicketState
from agent.llm import call_llm

PROMPT = Path("prompts/classify_type.md").read_text(encoding="utf-8")


def run(state: TicketState) -> dict:
    system, user = PROMPT.split("---")
    user = user.format(
        text=state["text"],
        requester_profile=state["requester_profile"],
    )

    try:
        resposta, tokens = call_llm(system, user, temperature=0.0)
    except TimeoutError:
        raise RuntimeError(
            f"classify_type: timeout ao chamar o LLM "
            f"no ticket {state['ticket_id']}"
        )

    try:
        data = json.loads(resposta)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"classify_type: LLM não retornou JSON válido "
            f"no ticket {state['ticket_id']}. "
            f"Resposta: {e.doc[:100]}"
        )

    campos_esperados = {"category", "service_type", "queue", "justification"}
    campos_faltando  = campos_esperados - data.keys()
    if campos_faltando:
        raise RuntimeError(
            f"classify_type: campos ausentes no ticket "
            f"{state['ticket_id']}: {campos_faltando}"
        )

    categorias_validas = {"Requisição", "Incidente", "Problema"}
    if data["category"] not in categorias_validas:
        raise RuntimeError(
            f"classify_type: categoria inválida '{data['category']}' "
            f"no ticket {state['ticket_id']}. Esperado: {categorias_validas}"
        )

    tokens_acumulados = state.get("tokens_used", 0) + tokens

    return {
        "category":                     data["category"],
        "service_type":                 data["service_type"],
        "queue":                        data["queue"],
        "classification_justification": data["justification"],
        "tokens_used":                  tokens_acumulados,
    }
