import json
from pathlib import Path
from agent.state import TicketState
from agent.llm import invoke

PROMPT = Path("prompts/classify_type.md").read_text(encoding="utf-8")


def run(state: TicketState) -> dict:
    system, user = PROMPT.split("---")
    user = user.format(
        text=state["text"],
        requester_profile=state["requester_profile"],
    )

    try:
        data = json.loads(invoke(system, user, temperature=0.0))
    except Exception as e:
        raise RuntimeError(f"classify_type falhou em {state['ticket_id']}: {e}")

    return {
        "category":                     data["category"],
        "service_type":                 data["service_type"],
        "queue":                        data["queue"],
        "classification_justification": data["justification"],
    }
