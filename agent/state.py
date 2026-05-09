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

    # ── Priorização — BPMN §1 ─────────────────────────────────────────────────
    urgency:                 Urgency
    impact:                  Impact
    priority:                Priority
    priority_justification:  str

    # ── Escalonamento — BPMN §2 ───────────────────────────────────────────────
    category:                      Category
    service_type:                  str
    queue:                         str
    classification_justification:  str

    # ── Resposta — atendimento 1° nível ───────────────────────────────────────
    draft_response:  str
    draft_closure:   str

    # ── Controle de fluxo ─────────────────────────────────────────────────────
    route_decision:  str
