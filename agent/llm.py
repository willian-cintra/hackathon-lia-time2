# agent/llm.py
import os
import re
import threading
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai import (
    AuthenticationError, RateLimitError, NotFoundError,
    APIConnectionError, APIStatusError,
)

load_dotenv()

# ── Acumulador thread-safe de tokens ──────────────────────────────────────────
_token_lock   = threading.Lock()
_token_totals = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}

def get_token_totals() -> dict:
    """Retorna cópia dos totais acumulados de tokens."""
    with _token_lock:
        return dict(_token_totals)

def reset_token_totals():
    """Zera os contadores — chamar no início de cada execução batch."""
    with _token_lock:
        _token_totals["prompt"]     = 0
        _token_totals["completion"] = 0
        _token_totals["total"]      = 0
        _token_totals["calls"]      = 0

def _register_tokens(usage):
    """Registra tokens de uma resposta no acumulador global."""
    if not usage:
        return
    with _token_lock:
        _token_totals["prompt"]     += getattr(usage, "prompt_tokens",     0)
        _token_totals["completion"] += getattr(usage, "completion_tokens", 0)
        _token_totals["total"]      += getattr(usage, "total_tokens",      0)
        _token_totals["calls"]      += 1

# ── Instâncias singleton do LLM ───────────────────────────────────────────────
def _build_llm(temperature: float = 0.0) -> ChatOpenAI:
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

_llm_deterministic = _build_llm(temperature=0.0)
_llm_creative      = _build_llm(temperature=0.3)

# ── Sanitização de output ─────────────────────────────────────────────────────
def _clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

# ── Chamada principal ─────────────────────────────────────────────────────────
def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
    llm = _llm_creative if temperature > 0 else _llm_deterministic

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
        raise RuntimeError("llm: modelo não encontrado.")
    except APIConnectionError:
        raise RuntimeError("llm: sem conexão com o OpenRouter.")
    except APIStatusError as e:
        raise RuntimeError(f"llm: erro do servidor (status {e.status_code}): {e.message}")

    if not resposta.content or not resposta.content.strip():
        raise RuntimeError("llm: o modelo retornou uma resposta vazia.")

    # Registrar tokens se disponíveis
    if hasattr(resposta, "response_metadata"):
        usage = resposta.response_metadata.get("token_usage")
        if usage:
            with _token_lock:
                _token_totals["prompt"]     += usage.get("prompt_tokens", 0)
                _token_totals["completion"] += usage.get("completion_tokens", 0)
                _token_totals["total"]      += usage.get("total_tokens", 0)
                _token_totals["calls"]      += 1

    return _clean(resposta.content)
