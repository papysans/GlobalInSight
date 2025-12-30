import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- 1. Moonshot AI (Kimi) ---
    _moonshot_keys_str = os.getenv("MOONSHOT_API_KEYS", "")
    MOONSHOT_API_KEYS = [k.strip() for k in _moonshot_keys_str.split(",") if k.strip()]
    MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1"
    MOONSHOT_MODEL = "kimi-k2-turbo-preview"

    # --- 2. Google Gemini (Multi-Key Rotation) ---
    _gemini_keys_str = os.getenv("GEMINI_API_KEYS", "")
    GEMINI_API_KEYS = [k.strip() for k in _gemini_keys_str.split(",") if k.strip()]
    GEMINI_MODEL = "gemini-3-flash-preview"

    # --- 3. OpenAI (Standard) ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-3.5-turbo"

    # --- 4. DeepSeek ---
    _deepseek_keys_str = os.getenv("DEEPSEEK_API_KEYS", "")
    DEEPSEEK_API_KEYS = [k.strip() for k in _deepseek_keys_str.split(",") if k.strip()]
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"

    # --- 5. Doubao ---
    _doubao_keys_str = os.getenv("DOUBAO_API_KEYS", "")
    DOUBAO_API_KEYS = [k.strip() for k in _doubao_keys_str.split(",") if k.strip()]
    DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DOUBAO_MODEL = "doubao-seed-1-6-251015"

    # --- 6. Zhipu AI ---
    _zhipu_keys_str = os.getenv("ZHIPU_API_KEYS", "")
    ZHIPU_API_KEYS = [k.strip() for k in _zhipu_keys_str.split(",") if k.strip()]
    ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPU_MODEL = "glm-4.7"

    # --- Agent Configuration (Select Provider Here) ---
    # Options for provider: "moonshot", "gemini", "openai", "deepseek", "doubao", "zhipu"
    # Supports fallback: if the first provider fails, it will try the next one
    AGENT_CONFIG = {
        "reporter": [
            {"provider": "deepseek", "model": DEEPSEEK_MODEL},
            {"provider": "moonshot", "model": MOONSHOT_MODEL},
            {"provider": "doubao", "model": DOUBAO_MODEL},
        ],
        "analyst": [
            {"provider": "deepseek", "model": DEEPSEEK_MODEL},
            {"provider": "moonshot", "model": MOONSHOT_MODEL},
        ],
        "debater": [
            {"provider": "deepseek", "model": DEEPSEEK_MODEL},
            {"provider": "moonshot", "model": MOONSHOT_MODEL},
            {"provider": "doubao", "model": DOUBAO_MODEL},
        ],
        "writer": [
            {"provider": "deepseek", "model": DEEPSEEK_MODEL},
            {"provider": "moonshot", "model": MOONSHOT_MODEL},
        ],
    }

    # --- Workflow Settings ---
    DEBATE_MAX_ROUNDS = 4 # Maximum number of debate rounds between Analyst and Debater

    # --- Crawler Settings ---
    # Default platforms to search if none provided
    # Options: "wb", "dy", "ks", "bili", "tieba", "zhihu", "xhs"
    DEFAULT_PLATFORMS = ["wb", "bili"]

    # Crawler Limits (per platform)
    # max_items: Number of posts/articles to retrieve
    # max_comments: Number of comments to retrieve per post (if supported)
    CRAWLER_LIMITS = {
        "wb": {"max_items": 5, "max_comments": 10},
        "bili": {"max_items": 5, "max_comments": 10},
        "dy": {"max_items": 5, "max_comments": 10},
        "xhs": {"max_items": 5, "max_comments": 10},
        "zhihu": {"max_items": 5, "max_comments": 10},
        "tieba": {"max_items": 5, "max_comments": 10},
        "ks": {"max_items": 5, "max_comments": 10},
    }

settings = Config()
