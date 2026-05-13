# agent/nodes/draft_response.py
import json
from pathlib import Path
from agent.state import TicketState
from agent.llm import call_llm
from agent.utils.few_shot import build_few_shot

PROMPT = Path("prompts/draft_response.md").read_text(encoding="utf-8")


def run(state: TicketState) -> dict:
    system, user = PROMPT.split("---")

    few_shot = build_few_shot(state["service_type"])

    user = user.format(
        text=state["text"],
        service_type=state["service_type"],
        requester_profile=state["requester_profile"],
        priority=state["priority"],
        few_shot=few_shot,
    )

    try:
        resposta, tokens = call_llm(system, user, temperature=0.3)
    except TimeoutError:
        raise RuntimeError(
            f"draft_response: timeout ao chamar o LLM "
            f"no ticket {state['ticket_id']}"
        )

    try:
        data = json.loads(resposta)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"draft_response: LLM não retornou JSON válido "
            f"no ticket {state['ticket_id']}. "
            f"Resposta: {e.doc[:100]}"
        )

    campos_esperados = {"draft_response", "draft_closure"}
    campos_faltando  = campos_esperados - data.keys()
    if campos_faltando:
        raise RuntimeError(
            f"draft_response: campos ausentes no ticket "
            f"{state['ticket_id']}: {campos_faltando}"
        )

    for campo in campos_esperados:
        if not data[campo] or not data[campo].strip():
            raise RuntimeError(
                f"draft_response: campo '{campo}' veio vazio "
                f"no ticket {state['ticket_id']}"
            )

    tokens_acumulados = state.get("tokens_used", 0) + tokens

    return {
        "draft_response": data["draft_response"],
        "draft_closure":  data["draft_closure"],
        "route_decision": "draft",
        "tokens_used":    tokens_acumulados,
    }
