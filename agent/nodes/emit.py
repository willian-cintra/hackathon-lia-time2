from agent.state import TicketState

_batch: list[dict] = []


def run(state: TicketState) -> dict:
    _batch.append({
        "ticket_id":                    state["ticket_id"],
        "priority":                     state["priority"],
        "category":                     state["category"],
        "service_type":                 state["service_type"],
        "queue":                        state["queue"],
        "route_decision":               state["route_decision"],
        "priority_justification":       state["priority_justification"],
        "classification_justification": state["classification_justification"],
        "has_draft":                    bool(state.get("draft_response")),
    })
    return {}


def save_csv(path: str = "outputs/results.csv"):
    import csv, os
    os.makedirs("outputs", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_batch[0].keys())
        writer.writeheader()
        writer.writerows(_batch)
    print(f"{len(_batch)} chamados salvos em {path}")
