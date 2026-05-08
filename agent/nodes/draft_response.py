import json
from agent.state import TicketState
from agent.llm import get_llm


# STUB — implementação mínima executável.
# Dias 3/4: integrar prompts/draft_response.md e prompts/knowledge_base.md
def run(state: TicketState) -> dict:
    """Nó draft_response — gera rascunho de e-mail para chamados simples.

    Só é chamado quando route_fn retorna 'draft':
    - categoria = Requisição
    - prioridade <= Médio
    - needs_human_review = False
    """
    try:
        llm = get_llm(temperature=0.3)  # leve variação para naturalidade no texto

        # STUB: sem base de conhecimento ainda — adicionada nos dias 3/4
        prompt = f"""\
Você é um analista de suporte da AGETIC/UFMS.
Redija uma resposta cordial e objetiva para o chamado abaixo.

Chamado: {state['text']}
Tipo de serviço: {state['service_type']}
Perfil do solicitante: {state['requester_profile']}
Prioridade: {state['priority']}

INSTRUÇÕES:
- Cumprimente pelo perfil (ex: "Prezado(a) discente," ou "Prezado(a) servidor(a),")
- Confirme o recebimento do chamado
- Apresente próximo passo ou solução
- Informe prazo: Médio → até 4h úteis | Baixo → até 1 dia útil
- Assine como "Equipe de Suporte AGETIC/UFMS"
- NÃO invente informações técnicas

Responda APENAS com JSON:
{{"draft_response": "<e-mail completo>", "draft_closure": "<mensagem curta de encerramento>"}}"""

        response = llm.invoke(prompt)
        data = json.loads(response.content)

        return {
            "draft_response": data.get("draft_response", ""),
            "draft_closure":  data.get("draft_closure", ""),
            "route_decision": "draft",
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"draft_response falhou: {e}"],
            "route_decision": "draft",  # mantém a rota registrada mesmo com falha
        }
