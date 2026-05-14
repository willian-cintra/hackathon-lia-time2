import json
from pathlib import Path
from agent.state import TicketState
from agent.llm import call_llm
from agent.logger import get_logger

logger = get_logger(__name__)

PROMPT = Path("prompts/score_priority.md").read_text(encoding="utf-8")

PRIORITY_MATRIX = {
    ("Alta",  "Alto"):  "Crítico",
    ("Alta",  "Médio"): "Alto",
    ("Alta",  "Baixo"): "Alto",
    ("Média", "Alto"):  "Alto",
    ("Média", "Médio"): "Médio",
    ("Média", "Baixo"): "Médio",
    ("Baixa", "Alto"):  "Médio",
    ("Baixa", "Médio"): "Baixo",
    ("Baixa", "Baixo"): "Baixo",
}

URGENCIAS_VALIDAS = {"Alta", "Média", "Baixa"}
IMPACTOS_VALIDOS  = {"Alto", "Médio", "Baixo"}

# ── Fail-safe — valores quando o LLM falha ─────────────────────
FAILSAFE_URGENCY  = "Alta"
FAILSAFE_IMPACT   = "Alto"
FAILSAFE_PRIORITY = "Crítico"

def _failsafe(ticket_id: str, motivo: str, tokens: int) -> dict:
    logger.error("%s | score_priority fail-safe ativado: %s", ticket_id, motivo)
    return {
        "urgency":                FAILSAFE_URGENCY,
        "impact":                 FAILSAFE_IMPACT,
        "priority":               FAILSAFE_PRIORITY,
        "priority_justification": f"Falha no LLM — prioridade máxima aplicada por segurança. Requer revisão humana. Motivo: {motivo}",
        "llm_error":              f"score_priority: {motivo}",
        "tokens_used":            tokens,
    }


def run(state: TicketState) -> dict:
    ticket_id = state["ticket_id"]
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

    campos_esperados = {"urgency", "impact", "justification"}
    campos_faltando  = campos_esperados - data.keys()
    if campos_faltando:
        return _failsafe(ticket_id, f"campos ausentes: {campos_faltando}", tokens_base)

    if data["urgency"] not in URGENCIAS_VALIDAS:
        return _failsafe(ticket_id, f"urgência inválida: '{data['urgency']}'", tokens_base)

    if data["impact"] not in IMPACTOS_VALIDOS:
        return _failsafe(ticket_id, f"impacto inválido: '{data['impact']}'", tokens_base)

    urgency  = data["urgency"]
    impact   = data["impact"]
    priority = PRIORITY_MATRIX[(urgency, impact)]

    tokens_acumulados = tokens_base + tokens

    return {
        "urgency":                urgency,
        "impact":                 impact,
        "priority":               priority,
        "priority_justification": data["justification"],
        "tokens_used":            tokens_acumulados,
    }