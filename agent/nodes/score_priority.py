import json
from pathlib import Path
from agent.state import TicketState
from agent.llm import call_llm

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

URGENCIAS_VALIDAS  = {"Alta", "Média", "Baixa"}
IMPACTOS_VALIDOS   = {"Alto", "Médio", "Baixo"}

def run(state: TicketState) -> dict:
    system, user = PROMPT.split("---")
    user = user.format(
        text=state["text"],
        requester_profile=state["requester_profile"],
    )

    # erro de API ou timeout
    try:
        resposta = call_llm(system, user, temperature=0.0)
    except TimeoutError:
        raise RuntimeError(
            f"score_priority: timeout ao chamar o LLM "
            f"no ticket {state['ticket_id']}"
        )

    # erro de JSON inválido
    try:
        data = json.loads(resposta)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"score_priority: LLM não retornou JSON válido "
            f"no ticket {state['ticket_id']}. "
            f"Resposta: {e.doc[:100]}"
        )

    # campos faltando
    campos_esperados = {"urgency", "impact", "justification"}
    campos_faltando = campos_esperados - data.keys()
    if campos_faltando:
        raise RuntimeError(
            f"score_priority: campos ausentes no ticket "
            f"{state['ticket_id']}: {campos_faltando}"
        )

    # urgência inválida
    if data["urgency"] not in URGENCIAS_VALIDAS:
        raise RuntimeError(
            f"score_priority: urgência inválida '{data['urgency']}' "
            f"no ticket {state['ticket_id']}. "
            f"Esperado: {URGENCIAS_VALIDAS}"
        )

    # impacto inválido
    if data["impact"] not in IMPACTOS_VALIDOS:
        raise RuntimeError(
            f"score_priority: impacto inválido '{data['impact']}' "
            f"no ticket {state['ticket_id']}. "
            f"Esperado: {IMPACTOS_VALIDOS}"
        )

    urgency  = data["urgency"]
    impact   = data["impact"]
    priority = PRIORITY_MATRIX[(urgency, impact)]

    return {
        "urgency":                urgency,
        "impact":                 impact,
        "priority":               priority,
        "priority_justification": data["justification"],
    }
