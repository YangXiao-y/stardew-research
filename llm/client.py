from langchain_openai import ChatOpenAI
from config import settings


def get_llm(temperature: float = 0.2):
    return ChatOpenAI(
        model=settings.QWEN_MODEL,
        api_key=settings.QWEN_API_KEY,
        base_url=settings.QWEN_BASE_URL,
        temperature=temperature,
    )