import os
from langchain_openai import ChatOpenAI


def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model="meta-llama/llama-3.1-8b-instruct",
        temperature=temperature,
        timeout=30,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]
    return llm.invoke(messages).content
