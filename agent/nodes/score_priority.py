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


def run(state: TicketState) -> dict:
    system, user = PROMPT.split("---")
    user = user.format(
        text=state["text"],
        requester_profile=state["requester_profile"],
    )

    try:
        data = json.loads(call_llm(system, user, temperature=0.0))
    except Exception as e:
        raise RuntimeError(f"score_priority falhou em {state['ticket_id']}: {e}")

    urgency  = data["urgency"]
    impact   = data["impact"]
    priority = PRIORITY_MATRIX[(urgency, impact)]

    return {
        "urgency":                urgency,
        "impact":                 impact,
        "priority":               priority,
        "priority_justification": data["justification"],
    }
