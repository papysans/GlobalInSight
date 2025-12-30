import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- 1. Moonshot AI (Kimi) ---
    MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
    MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1"
    MOONSHOT_MODEL = "kimi-k2-turbo-preview"

    # --- 2. Google Gemini (Multi-Key Rotation) ---
    _gemini_keys_str = os.getenv("GEMINI_API_KEYS", "")
    GEMINI_API_KEYS = [k.strip() for k in _gemini_keys_str.split(",") if k.strip()]
    GEMINI_MODEL = "gemini-3-flash-preview"

    # --- 3. OpenAI (Standard) ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-3.5-turbo"

    # --- Agent Configuration (Select Provider Here) ---
    # Options for provider: "moonshot", "gemini", "openai"
    AGENT_CONFIG = {
        "reporter": {"provider": "moonshot", "model": MOONSHOT_MODEL},
        "analyst": {"provider": "moonshot", "model": MOONSHOT_MODEL},
        "debater": {"provider": "moonshot", "model": MOONSHOT_MODEL},
        "writer": {"provider": "moonshot", "model": MOONSHOT_MODEL},
    }

    # --- Workflow Settings ---
    DEBATE_MAX_ROUNDS = 4 # Maximum number of debate rounds between Analyst and Debater

settings = Config()
