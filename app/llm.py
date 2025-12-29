from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.config import settings
import os
from itertools import cycle

class GeminiKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.key_cycle = cycle(keys)

    def get_next_key(self):
        if not self.keys:
            raise ValueError("No Gemini API keys configured.")
        return next(self.key_cycle)

# Initialize key manager
gemini_key_manager = GeminiKeyManager(settings.GEMINI_API_KEYS)

def get_llm(provider: str, model_name: str):
    """
    Factory function to get an LLM instance based on provider and model.
    """
    if provider == "google" or provider == "gemini":
        # Rotate API Key
        current_key = gemini_key_manager.get_next_key()
        
        print(f"🔄 Using Gemini Key: ...{current_key[-6:]}")
        
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.7,
            google_api_key=current_key,
            convert_system_message_to_human=True
        )
        
    elif provider == "moonshot":
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=settings.MOONSHOT_API_KEY,
            base_url=settings.MOONSHOT_BASE_URL
        )

    elif provider == "openai":
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
    
    else:
        raise ValueError(f"Unsupported LLM Provider: {provider}")

def get_agent_llm(agent_name: str):
    """
    Get a specific LLM instance for a named agent based on AGENT_CONFIG.
    """
    config = settings.AGENT_CONFIG.get(agent_name)
    if not config:
        # Fallback to default if agent not found
        return get_llm("gemini", settings.GEMINI_MODEL)
    
    return get_llm(config["provider"], config["model"])
