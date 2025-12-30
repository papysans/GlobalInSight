from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.config import settings
import os
from itertools import cycle

class KeyManager:
    def __init__(self, keys, provider_name="Unknown"):
        self.keys = [k for k in keys if k]
        self.key_cycle = cycle(self.keys) if self.keys else None
        self.provider_name = provider_name

    def get_next_key(self):
        if not self.key_cycle:
            raise ValueError(f"No API keys configured for {self.provider_name}.")
        return next(self.key_cycle)

# Initialize key managers
gemini_key_manager = KeyManager(settings.GEMINI_API_KEYS, "Gemini")
moonshot_key_manager = KeyManager(settings.MOONSHOT_API_KEYS, "Moonshot")
deepseek_key_manager = KeyManager(settings.DEEPSEEK_API_KEYS, "DeepSeek")
doubao_key_manager = KeyManager(settings.DOUBAO_API_KEYS, "Doubao")
zhipu_key_manager = KeyManager(settings.ZHIPU_API_KEYS, "Zhipu")

def get_llm(provider: str, model_name: str):
    """
    Factory function to get an LLM instance based on provider and model.
    """
    if provider == "google" or provider == "gemini":
        # Rotate API Key
        current_key = gemini_key_manager.get_next_key()
        
        print(f"妫ｅ啯鏁� Using Gemini Key: ...{current_key[-6:]}")
        
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.7,
            google_api_key=current_key,
            convert_system_message_to_human=True
        )
        
    elif provider == "moonshot":
        current_key = moonshot_key_manager.get_next_key()
        print(f"妫ｅ啯鏁� Using Moonshot Key: ...{current_key[-6:]}")
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=current_key,
            base_url=settings.MOONSHOT_BASE_URL
        )

    elif provider == "openai":
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )

    elif provider == "deepseek":
        current_key = deepseek_key_manager.get_next_key()
        print(f"妫ｅ啯鏁� Using DeepSeek Key: ...{current_key[-6:]}")
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=current_key,
            base_url=settings.DEEPSEEK_BASE_URL
        )

    elif provider == "doubao":
        current_key = doubao_key_manager.get_next_key()
        print(f"妫ｅ啯鏁� Using Doubao Key: ...{current_key[-6:]}")
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=current_key,
            base_url=settings.DOUBAO_BASE_URL
        )

    elif provider == "zhipu":
        current_key = zhipu_key_manager.get_next_key()
        print(f"妫ｅ啯鏁� Using Zhipu Key: ...{current_key[-6:]}")
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=current_key,
            base_url=settings.ZHIPU_BASE_URL
        )
    
    else:
        raise ValueError(f"Unsupported LLM Provider: {provider}")

class ResilientChatModel:
    """
    A wrapper around multiple LLM providers that implements fallback logic.
    If one provider fails, it automatically tries the next one in the list.
    """
    def __init__(self, configs):
        self.configs = configs if isinstance(configs, list) else [configs]

    async def ainvoke(self, messages, **kwargs):
        """
        Invoke LLM with automatic fallback to alternative providers.
        """
        errors = []
        for idx, config in enumerate(self.configs):
            provider = config["provider"]
            model = config["model"]
            try:
                llm = get_llm(provider, model)
                if idx == 0:
                    print(f"🎯 [LLM] Using {provider} ({model})")
                else:
                    print(f"🔄 [LLM Fallback] Trying {provider} ({model})...")
                
                result = await llm.ainvoke(messages, **kwargs)
                
                # Success - log and return
                if idx > 0:
                    print(f"✅ [LLM Fallback] Success with {provider}")
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ [LLM Error] {provider} failed: {error_msg[:100]}")
                errors.append(f"{provider}: {error_msg}")
                
                # If this is the last provider, raise the error
                if idx == len(self.configs) - 1:
                    break
                    
                # Otherwise, continue to next provider
                print(f"🔁 [LLM] Switching to next provider...")
                continue
        
        # All providers failed
        raise Exception(f"❌ All {len(self.configs)} LLM providers failed:\n" + "\n".join(errors))

def get_agent_llm(agent_name: str):
    """
    Get the configured LLM for a specific agent.
    Returns a ResilientChatModel that handles automatic fallback.
    """
    config = settings.AGENT_CONFIG.get(agent_name)
    if not config:
        # Fallback to default if agent not found
        print(f"⚠️ [Config] Agent '{agent_name}' not configured, using default")
        return get_llm("deepseek", settings.DEEPSEEK_MODEL)
    
    return ResilientChatModel(config)
