import json
from pathlib import Path
from agent.state import TicketState
from agent.llm import call_llm

PROMPT = Path("prompts/draft_response.md").read_text(encoding="utf-8")


def run(state: TicketState) -> dict:
    system, user = PROMPT.split("---")
    user = user.format(
        text=state["text"],
        service_type=state["service_type"],
        requester_profile=state["requester_profile"],
        priority=state["priority"],
    )

    try:
        data = json.loads(call_llm(system, user, temperature=0.3))
    except Exception as e:
        raise RuntimeError(f"draft_response falhou em {state['ticket_id']}: {e}")

    return {
        "draft_response": data["draft_response"],
        "draft_closure":  data["draft_closure"],
        "route_decision": "draft",
    }
