import json
from agent.state import TicketState
from agent.llm import get_llm

# Matriz ANS — aplicada por código Python, NUNCA pelo LLM
# Fonte: BPMN §1 "Priorizar chamado" — Acordo Geral no Nível de Serviço (ANS)
PRIORITY_MATRIX: dict[tuple[str, str], str] = {
    ("Alta",  "Alto"):  "Crítico",
    ("Alta",  "Médio"): "Alto",
    ("Alta",  "Baixo"): "Alto",
    ("Média", "Alto"):  "Alto",
    ("Média", "Médio"): "Médio",
    ("Média", "Baixo"): "Médio",
    ("Baixa", "Alto"):  "Médio",
    ("Baixa", "Médio"): "Baixo",
    ("Baixa", "Baixo"): "Baixo",
}


def apply_ans_matrix(urgency: str, impact: str) -> str:
    """Aplica a matriz ANS. Função pura — testável isoladamente."""
    return PRIORITY_MATRIX.get((urgency, impact), "Médio")


# STUB — implementação mínima executável.
# Dias 3/4: substituir pelo prompt completo em prompts/score_priority.md
def run(state: TicketState) -> dict:
    """Nó score_priority — LLM + regras determinísticas.

    Ordem fiel ao BPMN §1:
    1. LLM estima urgência e impacto a partir do texto livre
    2. Código Python aplica a matriz ANS para calcular a prioridade final
    """
    if state.get("needs_human_review"):
        return {}  # Já sinalizado pelo ingest, não processa

    try:
        llm = get_llm(temperature=0.0)

        # STUB: prompt simplificado — será substituído pelo arquivo .md nos dias 3/4
        prompt = f"""\
Analise o chamado de suporte abaixo e estime urgência e impacto.

Urgência: quão rapidamente a falta de resolução afeta o solicitante
  Alta  = impede trabalho imediato
  Média = causa transtorno mas há contorno
  Baixa = pode aguardar

Impacto: quantas pessoas são afetadas
  Alto  = múltiplos usuários ou sistema crítico
  Médio = um setor ou pequeno grupo
  Baixo = um único usuário

Chamado: {state['text']}
Perfil: {state['requester_profile']}

Responda APENAS com JSON válido:
{{"urgency": "Alta|Média|Baixa", "impact": "Alto|Médio|Baixo", "justification": "..."}}"""

        response = llm.invoke(prompt)
        data = json.loads(response.content)

        urgency = data["urgency"]
        impact  = data["impact"]
        priority = apply_ans_matrix(urgency, impact)

        return {
            "urgency": urgency,
            "impact":  impact,
            "priority": priority,
            "priority_justification": data.get("justification", ""),
        }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"score_priority falhou: {e}"],
            "needs_human_review": True,
            "priority": "Médio",  # valor conservador de fallback
            "priority_justification": "Falha na análise — requer revisão humana",
        }
