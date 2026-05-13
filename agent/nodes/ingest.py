from agent.state import TicketState
import re

CAMPOS_OBRIGATORIOS = {"ticket_id", "text", "channel", "requester_profile", "timestamp"}

CANAIS_VALIDOS = {"OTRS", "Telefone", "Balcão", "E-mail"}
PERFIS_VALIDOS = {"aluno", "docente_tec_administrativo"}

def _normalize(text: str) -> str:
    """Remove espaços duplicados, quebras múltiplas e tabulações."""
    text = re.sub(r"[\t\r\n]+", " ", text)        # quebras
    text = re.sub(r" {2,}", " ", text)              # múltiplos espaços
    return text.strip()

def run(state: TicketState) -> dict:

    # campos obrigatórios faltando
    campos_faltando = CAMPOS_OBRIGATORIOS - state.keys()
    if campos_faltando:
        raise RuntimeError(
            f"ingest: campos obrigatórios ausentes no ticket "
            f"{state.get('ticket_id', 'DESCONHECIDO')}: {campos_faltando}"
        )

    # texto vazio
    texto = _normalize(state["text"].strip())
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
