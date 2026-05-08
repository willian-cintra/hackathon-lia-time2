import json
from agent.state import TicketState
from agent.llm import get_llm

# Filas disponíveis na AGETIC — baseadas no BPMN §2 "Definir fila"
VALID_QUEUES = {"SECLI-N1", "SECLI-N2", "DINTEC-Redes", "DINTEC-Sistemas", "DINTEC-Seg"}


# STUB — implementação mínima executável.
# Dias 3/4: substituir pelo prompt few-shot completo em prompts/classify_type.md
def run(state: TicketState) -> dict:
    """Nó classify_type — LLM few-shot.

    Ordem fiel ao BPMN §2:
    1. Definir tipo de chamado (Requisição / Incidente / Problema)
    2. Definir serviço (do Catálogo TIC)
    3. Definir fila (setor AGETIC)
    """
    if state.get("needs_human_review"):
        return {}

    try:
        llm = get_llm(temperature=0.0)

        # STUB: prompt simplificado — será expandido com few-shot nos dias 3/4
        prompt = f"""\
Classifique o chamado de suporte TI da AGETIC/UFMS abaixo.

Categorias:
  Requisição = solicitação planejada (instalação, criação de conta, dúvida)
  Incidente  = interrupção não planejada de serviço
  Problema   = causa raiz de incidentes recorrentes

Serviços do Catálogo TIC: Conta Institucional | E-mail Institucional | \
Redes e Conectividade | Software e Licenças | Sistemas Institucionais | \
Segurança da Informação | Equipamentos e Hardware | Outros

Filas disponíveis: SECLI-N1 | SECLI-N2 | DINTEC-Redes | DINTEC-Sistemas | DINTEC-Seg

Chamado: {state['text']}
Perfil: {state['requester_profile']}

Responda APENAS com JSON válido:
{{"category": "...", "service_type": "...", "queue": "...", \
"internal_note": "...", "justification": "..."}}"""

        response = llm.invoke(prompt)
        data = json.loads(response.content)

        # Garante que a fila é válida — fallback conservador
        queue = data.get("queue", "SECLI-N1")
        if queue not in VALID_QUEUES:
            queue = "SECLI-N1"

        return {
            "category":                     data.get("category", "Requisição"),
            "service_type":                 data.get("service_type", "Outros"),
            "queue":                        queue,
            "internal_note":                data.get("internal_note", ""),
            "classification_justification": data.get("justification", ""),
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"classify_type falhou: {e}"],
            "needs_human_review": True,
            "classification_justification": "Falha na classificação — requer revisão humana",
        }
