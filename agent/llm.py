from langchain_openai import ChatOpenAI
import os

def get_llm(model: str = "openai/gpt-4o-mini", temperature: float = 0.0) -> ChatOpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY não definida. Verifique o .env")

    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model=model,
        temperature=temperature,
        timeout=30,
        max_retries=2,
    )
