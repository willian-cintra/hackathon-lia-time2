import json
from agent.config import KNOWLEDGE_BASE_PATH

_KB_PATH = KNOWLEDGE_BASE_PATH

def build_few_shot(service_type: str, n: int = 2) -> str:
    try:
        kb = json.loads(_KB_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ""  # sem base de conhecimento, retorna vazio

    # busca exemplos do mesmo tipo de serviço
    exemplos = [e for e in kb if e.get("service_type") == service_type]

    # se não encontrar, usa qualquer exemplo disponível
    if not exemplos:
        exemplos = kb

    resultado = ""
    for e in exemplos[:n]:
        resultado += f'Chamado: "{e["text"]}"\n'
        resultado += f'Resposta: "{e["draft_response"]}"\n\n'

    return resultado.strip()