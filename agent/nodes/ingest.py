from agent.state import TicketState, empty_state

REQUIRED_FIELDS = ["ticket_id", "text", "channel", "requester_profile", "timestamp"]
VALID_CHANNELS  = {"OTRS", "Telefone", "Balcão", "E-mail"}
VALID_PROFILES  = {"aluno", "docente_tec_administrativo"}


def run(state: TicketState) -> dict:
    """Nó ingest — código puro, sem LLM.

    Responsabilidades:
    - Valida presença e valores dos campos de entrada
    - Normaliza o texto (strip de espaços)
    - Inicializa todos os campos de saída com valores vazios via empty_state
    - Registra erros sem interromper o fluxo
    """
    errors = []

    # Valida campos obrigatórios
    for field in REQUIRED_FIELDS:
        if not state.get(field, "").strip():
            errors.append(f"Campo obrigatório ausente ou vazio: '{field}'")

    # Valida enumerados
    if state.get("channel") not in VALID_CHANNELS:
        errors.append(f"Canal inválido: '{state.get('channel')}'. Esperado: {VALID_CHANNELS}")

    if state.get("requester_profile") not in VALID_PROFILES:
        errors.append(f"Perfil inválido: '{state.get('requester_profile')}'. Esperado: {VALID_PROFILES}")

    # Se houver erros de entrada, sinaliza revisão humana imediatamente
    if errors:
        return {
            **state,
            "text": state.get("text", "").strip(),
            "errors": errors,
            "needs_human_review": True,
        }

    # Estado inicial limpo com texto normalizado
    base = empty_state(
        ticket_id=state["ticket_id"],
        text=state["text"].strip(),
        channel=state["channel"],
        requester_profile=state["requester_profile"],
        timestamp=state["timestamp"],
    )
    
    return base
