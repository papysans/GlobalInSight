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

    # --- 5.1 Volcengine Visual API (Image Generation) ---
    VOLC_ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY", "")
    VOLC_SECRET_KEY = os.getenv("VOLC_SECRET_KEY", "")

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
        # --- Hot News Interpretation Agent (for thesis/demo) ---
        # Used by /api/hot-news/interpret. Single-topic, on-demand LLM call with caching.
        "hotnews_interpretation_agent": [
            {"provider": "deepseek", "model": DEEPSEEK_MODEL},
            {"provider": "moonshot", "model": MOONSHOT_MODEL},
            {"provider": "doubao", "model": DOUBAO_MODEL},
        ],
        # --- Translation / Query Builder Agent ---
        # Used in workflow.py to translate CN topic -> EN search query.
        "translator": [
            {"provider": "deepseek", "model": DEEPSEEK_MODEL},
            {"provider": "moonshot", "model": MOONSHOT_MODEL},
        ],
    }

    # --- Workflow Settings ---
    DEBATE_MAX_ROUNDS = 4 # Maximum number of debate rounds between Analyst and Debater

    # --- Workflow Content Safety (backend-only) ---
    # Goal: prevent political-sensitive signals from appearing in workflow outputs (logs/insight/copy).
    # This is intentionally NOT exposed to the frontend.
    #
    # Recommended defaults:
    # - redact_politics: True  -> scrub political entities/terms from generated outputs
    # - block_political_topics: True -> if the user topic is deemed political, short-circuit workflow and return a safe message
    WORKFLOW_CONTENT_SAFETY = {
        "redact_politics": True,
        "block_political_topics": True,
        "redaction_token": "【已脱敏】",
    }

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
        # Foreign / intl
        "hn": {"max_items": 30, "max_comments": 80},
        "reddit": {"max_items": 8, "max_comments": 20},
    }

    # --- Hot News Settings (TopHub) ---
    HOT_NEWS_CONFIG = {
        "enabled": True,
        "platform_sources": [],  # Empty list means collect all platforms
        "fetch_interval_hours": 4,
        "cache_ttl_minutes": 30,
        "max_items_per_platform": 100,
    }

    # --- 小红书 MCP 发布设置 ---
    XHS_MCP_CONFIG = {
        "enabled": True,  # 是否启用小红书发布功能
        "mcp_url": os.getenv("XHS_MCP_URL", "http://localhost:18060/mcp"),
        "auto_publish": False,  # 工作流完成后是否自动发布
    }

settings = Config()
