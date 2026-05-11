from agent.state import TicketState

CAMPOS_OBRIGATORIOS = {"ticket_id", "text", "channel", "requester_profile", "timestamp"}

CANAIS_VALIDOS = {"OTRS", "Telefone", "Balcão", "E-mail"}
PERFIS_VALIDOS = {"aluno", "docente_tec_administrativo"}

def run(state: TicketState) -> dict:

    # campos obrigatórios faltando
    campos_faltando = CAMPOS_OBRIGATORIOS - state.keys()
    if campos_faltando:
        raise RuntimeError(
            f"ingest: campos obrigatórios ausentes no ticket "
            f"{state.get('ticket_id', 'DESCONHECIDO')}: {campos_faltando}"
        )

    # texto vazio
    texto = state["text"].strip()
    if not texto:
        raise RuntimeError(
            f"ingest: texto do chamado está vazio "
            f"no ticket {state['ticket_id']}"
        )

    # canal inválido
    if state["channel"] not in CANAIS_VALIDOS:
        raise RuntimeError(
            f"ingest: canal inválido '{state['channel']}' "
            f"no ticket {state['ticket_id']}. "
            f"Esperado: {CANAIS_VALIDOS}"
        )

    # perfil inválido
    if state["requester_profile"] not in PERFIS_VALIDOS:
        raise RuntimeError(
            f"ingest: perfil inválido '{state['requester_profile']}' "
            f"no ticket {state['ticket_id']}. "
            f"Esperado: {PERFIS_VALIDOS}"
        )

    return {"text": texto}
