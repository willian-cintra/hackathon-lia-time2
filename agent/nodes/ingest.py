from agent.state import TicketState


def run(state: TicketState) -> dict:
    return {"text": state["text"].strip()}
