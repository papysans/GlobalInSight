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

    # --- 7. MiniMax ---
    _minimax_keys_str = os.getenv("MINIMAX_API_KEYS", "")
    MINIMAX_API_KEYS = [k.strip() for k in _minimax_keys_str.split(",") if k.strip()]
    MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
    MINIMAX_MODEL = "MiniMax-M2.1"

    # --- Provider Models Metadata ---
    # Complete list of available models for each provider
    PROVIDER_MODELS = {
        "deepseek": [
            {
                "id": "deepseek-chat",
                "name": "DeepSeek Chat",
                "description": "平衡的对话模型，适合大多数任务",
                "type": "chat",
                "is_default": True
            },
            {
                "id": "deepseek-reasoner",
                "name": "DeepSeek Reasoner",
                "description": "推理增强模型，适合复杂分析",
                "type": "reasoning",
                "is_default": False
            }
        ],
        "gemini": [
            {
                "id": "gemini-3-pro-preview",
                "name": "Gemini 3 Pro Preview",
                "description": "最强大的模型，适合复杂任务",
                "type": "pro",
                "is_default": False
            },
            {
                "id": "gemini-3-flash-preview",
                "name": "Gemini 3 Flash Preview",
                "description": "快速响应模型",
                "type": "flash",
                "is_default": True
            },
            {
                "id": "gemini-2.5-flash",
                "name": "Gemini 2.5 Flash",
                "description": "稳定的快速模型",
                "type": "flash",
                "is_default": False
            },
            {
                "id": "gemini-2.5-pro",
                "name": "Gemini 2.5 Pro",
                "description": "稳定的专业模型",
                "type": "pro",
                "is_default": False
            }
        ],
        "kimi": [
            {
                "id": "kimi-k2-0905-preview",
                "name": "Kimi K2 0905 Preview",
                "description": "最新预览版本",
                "type": "preview",
                "is_default": False
            },
            {
                "id": "kimi-k2-turbo-preview",
                "name": "Kimi K2 Turbo Preview",
                "description": "快速响应版本",
                "type": "turbo",
                "is_default": True
            },
            {
                "id": "kimi-k2-thinking",
                "name": "Kimi K2 Thinking",
                "description": "深度思考模型",
                "type": "thinking",
                "is_default": False
            }
        ],
        "zhipu": [
            {
                "id": "GLM-4.7",
                "name": "GLM-4.7",
                "description": "最新一代模型",
                "type": "chat",
                "is_default": True
            },
            {
                "id": "GLM-4.7-FlashX",
                "name": "GLM-4.7 FlashX",
                "description": "极速响应版本",
                "type": "flash",
                "is_default": False
            },
            {
                "id": "GLM-4.6",
                "name": "GLM-4.6",
                "description": "稳定版本",
                "type": "chat",
                "is_default": False
            }
        ],
        "minimax": [
            {
                "id": "MiniMax-M2.1",
                "name": "MiniMax M2.1",
                "description": "最新版本",
                "type": "chat",
                "is_default": True
            },
            {
                "id": "M2-her",
                "name": "M2 HER",
                "description": "高效推理版本",
                "type": "reasoning",
                "is_default": False
            }
        ],
        "doubao": [
            {
                "id": "doubao-seed-1-8-251228",
                "name": "豆包 Seed 1.8",
                "description": "最新种子模型",
                "type": "chat",
                "is_default": True
            },
            {
                "id": "doubao-seed-1-6-flash-250828",
                "name": "豆包 Seed 1.6 Flash",
                "description": "快速响应版本",
                "type": "flash",
                "is_default": False
            }
        ],
        "openai": [
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "description": "最强大的模型",
                "type": "chat",
                "is_default": False
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "快速且经济的模型",
                "type": "chat",
                "is_default": True
            }
        ]
    }

    # --- Agent Configuration (Select Provider Here) ---
    # Options for provider: "moonshot", "gemini", "openai", "deepseek", "doubao", "zhipu", "minimax"
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
        "cache_ttl_minutes": 240,  # 4 hours = 240 minutes
        "max_items_per_platform": 100,
    }

    # --- 小红书 MCP 发布设置 ---
    XHS_MCP_CONFIG = {
        "enabled": True,  # 是否启用小红书发布功能
        "mcp_url": os.getenv("XHS_MCP_URL", "http://localhost:18060/mcp"),
        "auto_publish": False,  # 工作流完成后是否自动发布
    }

    # --- 图片发布配置 (MCP Image Publishing Pipeline) ---
    # image_publish_mode: 
    #   - "ai_only": 阶段 F，仅使用 AI 生成的配图
    #   - "ai_and_cards": 阶段 B，同时使用数据卡片和 AI 配图
    IMAGE_PUBLISH_CONFIG = {
        "image_publish_mode": os.getenv("IMAGE_PUBLISH_MODE", "ai_only"),
        "render_service_url": os.getenv("RENDER_SERVICE_URL", "http://localhost:8000/render"),
        "render_timeout": int(os.getenv("RENDER_TIMEOUT", "30")),
        "browser_pool_min": int(os.getenv("BROWSER_POOL_MIN", "2")),
        "browser_pool_max": int(os.getenv("BROWSER_POOL_MAX", "4")),
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "render_route": "/render-cards",
    }

    # --- Model Management Methods ---
    @classmethod
    def get_all_models(cls):
        """获取所有提供商的模型列表"""
        return cls.PROVIDER_MODELS

    @classmethod
    def get_models_for_provider(cls, provider_key):
        """获取指定提供商的模型列表"""
        return cls.PROVIDER_MODELS.get(provider_key, [])

    @classmethod
    def get_default_model(cls, provider_key):
        """获取指定提供商的默认模型"""
        models = cls.get_models_for_provider(provider_key)
        default = next((m for m in models if m.get("is_default")), None)
        return default["id"] if default else (models[0]["id"] if models else None)

    @classmethod
    def validate_model(cls, provider_key, model_id):
        """验证提供商-模型组合是否有效"""
        if not provider_key or not model_id:
            return False
        models = cls.get_models_for_provider(provider_key)
        return any(m["id"] == model_id for m in models)

    # --- Image Publish Config Methods ---
    @classmethod
    def get_image_publish_mode(cls):
        """获取当前图片发布模式（支持热加载）"""
        # 每次调用时重新读取环境变量，支持运行时配置变更
        return os.getenv("IMAGE_PUBLISH_MODE", cls.IMAGE_PUBLISH_CONFIG["image_publish_mode"])
    
    @classmethod
    def set_image_publish_mode(cls, mode: str):
        """设置图片发布模式（运行时）"""
        if mode not in ("ai_only", "ai_and_cards"):
            raise ValueError(f"Invalid image_publish_mode: {mode}. Must be 'ai_only' or 'ai_and_cards'")
        cls.IMAGE_PUBLISH_CONFIG["image_publish_mode"] = mode
        # 同时更新环境变量以支持跨进程
        os.environ["IMAGE_PUBLISH_MODE"] = mode
        from loguru import logger
        logger.info(f"Image publish mode changed to: {mode}")
    
    @classmethod
    def get_image_publish_config(cls):
        """获取完整的图片发布配置"""
        config = cls.IMAGE_PUBLISH_CONFIG.copy()
        # 确保使用最新的模式设置
        config["image_publish_mode"] = cls.get_image_publish_mode()
        return config

settings = Config()
