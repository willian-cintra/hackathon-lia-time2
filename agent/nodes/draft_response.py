import json
from pathlib import Path
from agent.state import TicketState
from agent.llm import call_llm
from agent.utils.few_shot import build_few_shot
from agent.logger import get_logger
from agent.config import DRAFT_RESPONSE_PROMPT

logger = get_logger(__name__)

PROMPT = DRAFT_RESPONSE_PROMPT.read_text(encoding="utf-8")

# ── Fail-safe ─────────────────────────────────────────────────────────────────
# Quando o LLM falha ao gerar o rascunho, o ticket muda de rota para "queue"
def _failsafe(ticket_id: str, motivo: str, tokens: int) -> dict:
    """Redireciona para fila humana quando o rascunho não pode ser gerado."""
    logger.error("%s | draft_response fail-safe ativado: %s", ticket_id, motivo)
    return {
        "draft_response": "",
        "draft_closure":  "",
        "route_decision": "queue",   # ← muda a rota para fila humana
        "llm_error":      f"draft_response: {motivo}",
        "tokens_used":    tokens,
    }


def run(state: TicketState) -> dict:
    ticket_id   = state["ticket_id"]
    tokens_base = state.get("tokens_used", 0)

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
    except Exception as e:
        return _failsafe(ticket_id, f"falha na chamada ao LLM: {e}", tokens_base)

    try:
        data = json.loads(resposta)
    except json.JSONDecodeError as e:
        return _failsafe(ticket_id, f"JSON inválido: {e.doc[:80]}", tokens_base)

    campos_esperados = {"draft_response", "draft_closure"}
    campos_faltando  = campos_esperados - data.keys()
    if campos_faltando:
        return _failsafe(ticket_id, f"campos ausentes: {campos_faltando}", tokens_base)

    for campo in campos_esperados:
        if not data[campo] or not data[campo].strip():
            return _failsafe(ticket_id, f"campo '{campo}' veio vazio", tokens_base)

    tokens_acumulados = tokens_base + tokens

    logger.info("%s | rascunho gerado com sucesso | tokens=%d", ticket_id, tokens_acumulados)

    return {
        "draft_response": data["draft_response"],
        "draft_closure":  data["draft_closure"],
        "route_decision": "draft",
        "tokens_used":    tokens_acumulados,
    }