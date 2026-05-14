import json
from pathlib import Path
from agent.state import TicketState
from agent.llm import call_llm
from agent.logger import get_logger

logger = get_logger(__name__)

PROMPT = Path("prompts/classify_type.md").read_text(encoding="utf-8")

CATEGORIAS_VALIDAS = {"Requisição", "Incidente", "Problema"}

# ── Fail-safe — valores conservadores quando o LLM falha ─────────────────────
FAILSAFE_CATEGORY     = "Incidente"
FAILSAFE_SERVICE_TYPE = "Atendimento Geral"
FAILSAFE_QUEUE        = "N1"

def _failsafe(ticket_id: str, motivo: str, tokens: int) -> dict:
    logger.error("%s | classify_type fail-safe ativado: %s", ticket_id, motivo)
    return {
        "category":                     FAILSAFE_CATEGORY,
        "service_type":                 FAILSAFE_SERVICE_TYPE,
        "queue":                        FAILSAFE_QUEUE,
        "classification_justification": f"Falha no LLM — classificação máxima aplicada por segurança. Requer revisão humana. Motivo: {motivo}",
        "llm_error":                    f"classify_type: {motivo}",
        "tokens_used":                  tokens,
    }

def run(state: TicketState) -> dict:
    ticket_id   = state["ticket_id"]
    tokens_base = state.get("tokens_used", 0)

    system, user = PROMPT.split("---")
    user = user.format(
        text=state["text"],
        requester_profile=state["requester_profile"],
    )

    try:
        resposta, tokens = call_llm(system, user, temperature=0.0)
    except Exception as e:
        return _failsafe(ticket_id, f"falha na chamada ao LLM: {e}", tokens_base)

    try:
        data = json.loads(resposta)
    except json.JSONDecodeError as e:
        return _failsafe(ticket_id, f"JSON inválido: {e.doc[:80]}", tokens_base)

    campos_esperados = {"category", "service_type", "queue", "justification"}
    campos_faltando  = campos_esperados - data.keys()
    if campos_faltando:
        return _failsafe(ticket_id, f"campos ausentes: {campos_faltando}", tokens_base)

    if data["category"] not in CATEGORIAS_VALIDAS:
        return _failsafe(ticket_id, f"categoria inválida: '{data['category']}'", tokens_base)

    tokens_acumulados = tokens_base + tokens

    return {
        "category":                     data["category"],
        "service_type":                 data["service_type"],
        "queue":                        data["queue"],
        "classification_justification": data["justification"],
        "tokens_used":                  tokens_acumulados,
    }