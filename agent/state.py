from typing import TypedDict, Literal

# ── Tipos enumerados ──────────────────────────────────────────────────────────
Channel          = Literal["OTRS", "Telefone", "Balcão", "E-mail"]
RequesterProfile = Literal["aluno", "docente_tec_administrativo"]
Urgency          = Literal["Alta", "Média", "Baixa"]
Impact           = Literal["Alto", "Médio", "Baixo"]
Priority         = Literal["Crítico", "Alto", "Médio", "Baixo"]
Category         = Literal["Requisição", "Incidente", "Problema"]


class TicketState(TypedDict):
    # ── Entrada ───────────────────────────────────────────────────────────────
    ticket_id:          str
    text:               str
    channel:            Channel
    requester_profile:  RequesterProfile
    timestamp:          str

    # ── Priorização ────────────────────────────────────────────────────────────
    urgency:                 Urgency
    impact:                  Impact
    priority:                Priority
    priority_justification:  str        # obrigatório — auditoria

    # ── Escalonamento ──────────────────────────────────────────────────────────
    category:                      Category
    service_type:                  str
    queue:                         str
    internal_note:                 str
    classification_justification:  str  # obrigatório — auditoria

    # ── Resposta — atendimento 1° nível ─────────────────────────────────────────
    draft_response:  str
    draft_closure:   str

    # ── Controle de fluxo ────────────────────────────────────────────────────────
    route_decision:      str
    needs_human_review:  bool
    errors:              list[str]


def empty_state(ticket_id: str, text: str, channel: Channel,
                requester_profile: RequesterProfile, timestamp: str) -> TicketState:
    """Cria um estado inicial com todos os campos de saída vazios.
    Usado pelo nó ingest para garantir que nenhum campo fique undefined.
    """
    return TicketState(
        ticket_id=ticket_id,
        text=text,
        channel=channel,
        requester_profile=requester_profile,
        timestamp=timestamp,
        urgency="Baixa",
        impact="Baixo",
        priority="Baixo",
        priority_justification="",
        category="Requisição",
        service_type="",
        queue="",
        internal_note="",
        classification_justification="",
        draft_response="",
        draft_closure="",
        route_decision="",
        needs_human_review=False,
        errors=[],
    )
