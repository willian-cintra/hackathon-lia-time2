# agent/llm.py — versão com singleton e retry
import os
import re
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from openai import (
    AuthenticationError, RateLimitError, NotFoundError,
    APIConnectionError, APIStatusError,
)

load_dotenv()

def build_llm(temperature: float = 0.0) -> ChatOpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "llm: OPENROUTER_API_KEY não encontrada. Verifique seu arquivo .env"
        )
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model=os.environ.get("LLM_MODEL", "google/gemma-4-31b-it"),
        temperature=temperature,
        timeout=30,
    ).with_retry(stop_after_attempt=3, wait_exponential_jitter=True)

# Instâncias únicas — criadas no import do módulo
llm_deterministic = build_llm(temperature=0.0)
llm_creative      = build_llm(temperature=0.3)

def clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
    llm = llm_creative if temperature > 0 else llm_deterministic

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    try:
        resposta = llm.invoke(messages)
    except AuthenticationError:
        raise RuntimeError("llm: chave de API inválida ou expirada.")
    except RateLimitError:
        raise RuntimeError("llm: limite de uso da API atingido. Aguarde ou verifique créditos.")
    except NotFoundError:
        raise RuntimeError(f"llm: modelo não encontrado.")
    except APIConnectionError:
        raise RuntimeError("llm: sem conexão com o OpenRouter.")
    except APIStatusError as e:
        raise RuntimeError(f"llm: erro do servidor (status {e.status_code}): {e.message}")

    if not resposta.content or not resposta.content.strip():
        raise RuntimeError("llm: o modelo retornou uma resposta vazia.")

    return clean(resposta.content)