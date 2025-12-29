import os

class Config:
    # --- 1. Moonshot AI (Kimi) ---
    MOONSHOT_API_KEY = "sk-liynHIDVC9Z5ISEjl752dV2oB0OsqZLLOdpj5IggtAHeOd5l"
    MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1"
    MOONSHOT_MODEL = "kimi-k2-turbo-preview"

    # --- 2. Google Gemini (Multi-Key Rotation) ---
    GEMINI_API_KEYS = [
        "AIzaSyDy-OXo9Y6ZnGJygJvPF2tKtfEYVFDFxv8",
        "AIzaSyCh_8AhxUiJjkS2jbkCBm_0fuMfSPf5s9k",
        "AIzaSyA_5dhUSIfnNDD3KvsRJg3hWkCLI2OoPQw",
        "AIzaSyAS-8QLk_7Z2dzz1TJNPNr7-Gm0admEw2g",
        "AIzaSyA9O_ZsTobKvNPHDC024E0EoFeDzUp44do",
        "AIzaSyAU07hh0YptT1rBNG2TjniikpoyVasYUUE",
        "AIzaSyAYVVmzEnHCK0Bk0WXk1fIxRLFRPcPhLgM",
        "AIzaSyBI8pq4n7XM57So_YFuaophWODyb8mnLH8"
    ]
    GEMINI_MODEL = "gemini-3-flash-preview"

    # --- 3. OpenAI (Standard) ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-3.5-turbo"

    # --- Agent Configuration (Select Provider Here) ---
    # Options for provider: "moonshot", "gemini", "openai"
    AGENT_CONFIG = {
        "reporter": {"provider": "gemini", "model": GEMINI_MODEL},
        "analyst": {"provider": "gemini", "model": GEMINI_MODEL},
        "debater": {"provider": "gemini", "model": GEMINI_MODEL},
        "writer": {"provider": "gemini", "model": GEMINI_MODEL},
    }

    # --- Workflow Settings ---
    DEBATE_MAX_ROUNDS = 4 # Maximum number of debate rounds between Analyst and Debater

settings = Config()
