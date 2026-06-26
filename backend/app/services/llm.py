from langchain_ollama import ChatOllama

from config import settings


llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    temperature=settings.TEMPERATURE
)