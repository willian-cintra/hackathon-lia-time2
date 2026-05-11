import os
from langchain_openai import ChatOpenAI
from langchain_core.exceptions import OutputParserException
from openai import (
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    APIConnectionError,
    APIStatusError,
)

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:

    # chave ausente
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "llm: OPENROUTER_API_KEY não encontrada. "
            "Verifique seu arquivo .env"
        )

    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model="google/gemma-4-31b-it",
        temperature=temperature,
        timeout=30,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    try:
        resposta = llm.invoke(messages)

    except AuthenticationError:
        raise RuntimeError(
            "llm: chave de API inválida ou expirada. "
            "Verifique sua OPENROUTER_API_KEY"
        )
    except RateLimitError:
        raise RuntimeError(
            "llm: limite de uso da API atingido. "
            "Aguarde ou verifique seus créditos no OpenRouter"
        )
    except NotFoundError:
        raise RuntimeError(
            "llm: modelo não encontrado. "
            "Verifique se 'google/gemma-4-31b-it' ainda está disponível"
        )
    except APIConnectionError:
        raise RuntimeError(
            "llm: sem conexão com o OpenRouter. "
            "Verifique sua internet ou se o serviço está no ar"
        )
    except TimeoutError:
        raise RuntimeError(
            "llm: timeout — o modelo não respondeu em 30 segundos"
        )
    except APIStatusError as e:
        raise RuntimeError(
            f"llm: erro do servidor OpenRouter (status {e.status_code}): {e.message}"
        )

    # resposta vazia
    if not resposta.content or not resposta.content.strip():
        raise RuntimeError(
            "llm: o modelo retornou uma resposta vazia"
        )

    return resposta.content