from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from loguru import logger
from app.schemas import (
    ConfigResponse, ConfigUpdateRequest,
    OutputFileListResponse, OutputFileInfo, OutputFileContentResponse,
    LLMProviderConfig, CrawlerLimit,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
    XhsPublishRequest,
)
from app.config import settings
from app.services.user_settings import load_user_settings, update_user_settings
from pathlib import Path
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "globalinsight-backend"}


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """获取当前配置"""
    llm_providers = {
        "reporter": [LLMProviderConfig(**item) for item in settings.AGENT_CONFIG["reporter"]],
        "analyst": [LLMProviderConfig(**item) for item in settings.AGENT_CONFIG["analyst"]],
        "debater": [LLMProviderConfig(**item) for item in settings.AGENT_CONFIG["debater"]],
        "writer": [LLMProviderConfig(**item) for item in settings.AGENT_CONFIG["writer"]],
    }

    crawler_limits = {
        platform: CrawlerLimit(**limits)
        for platform, limits in settings.CRAWLER_LIMITS.items()
    }

    from app.schemas import HotNewsConfig
    hot_news_config = HotNewsConfig(**settings.HOT_NEWS_CONFIG)

    return ConfigResponse(
        llm_providers=llm_providers,
        crawler_limits=crawler_limits,
        debate_max_rounds=settings.DEBATE_MAX_ROUNDS,
        default_platforms=settings.DEFAULT_PLATFORMS,
        hot_news_config=hot_news_config
    )


@router.put("/config")
async def update_config(request: ConfigUpdateRequest):
    """更新配置（部分更新）"""
    updated_fields = []

    if request.debate_max_rounds is not None:
        if request.debate_max_rounds < 1:
            raise HTTPException(status_code=400, detail="debate_max_rounds 必须大于0")
        settings.DEBATE_MAX_ROUNDS = request.debate_max_rounds
        updated_fields.append("debate_max_rounds")

    if request.crawler_limits is not None:
        for platform, limits in request.crawler_limits.items():
            if platform in settings.CRAWLER_LIMITS:
                settings.CRAWLER_LIMITS[platform].update(limits.dict())
                updated_fields.append(f"crawler_limits.{platform}")

    if request.default_platforms is not None:
        valid_platforms = ["wb", "dy", "ks", "bili", "tieba", "zhihu", "xhs", "hn", "reddit"]
        invalid = [p for p in request.default_platforms if p not in valid_platforms]
        if invalid:
            raise HTTPException(status_code=400, detail=f"无效的平台: {invalid}")
        settings.DEFAULT_PLATFORMS = request.default_platforms
        updated_fields.append("default_platforms")

    if request.hot_news_config is not None:
        settings.HOT_NEWS_CONFIG = request.hot_news_config.dict()
        updated_fields.append("hot_news_config")

    if not updated_fields:
        raise HTTPException(status_code=400, detail="没有提供要更新的字段")

    return {
        "success": True,
        "message": f"配置已更新: {', '.join(updated_fields)}",
        "updated_fields": updated_fields
    }


@router.get("/user-settings", response_model=UserSettingsResponse)
async def get_user_settings():
    """获取前端可写入的用户设置（存储在 cache/user_settings.json）"""
    data = load_user_settings()
    return UserSettingsResponse(
        llm_apis=data.get("llm_apis") or [],
        volcengine=data.get("volcengine"),
        agent_llm_overrides=data.get("agent_llm_overrides") or {},
    )


@router.put("/user-settings", response_model=UserSettingsResponse)
async def put_user_settings(request: UserSettingsUpdateRequest):
    """更新前端可写入的用户设置（部分更新）"""
    # 验证 llm_apis 中的模型配置
    if request.llm_apis is not None:
        for api_item in request.llm_apis:
            provider_key = api_item.providerKey if hasattr(api_item, 'providerKey') else api_item.get('providerKey')
            model = api_item.model if hasattr(api_item, 'model') else api_item.get('model')

            if model and provider_key:
                if not settings.validate_model(provider_key, model):
                    available_models = settings.get_models_for_provider(provider_key)
                    model_names = [m["id"] for m in available_models] if available_models else []
                    raise HTTPException(
                        status_code=400,
                        detail=f"模型 {model} 在提供商 {provider_key} 中无效。可用模型: {', '.join(model_names)}"
                    )

    # 验证 agent_llm_overrides 中的模型配置
    if request.agent_llm_overrides is not None:
        for agent_key, override in request.agent_llm_overrides.items():
            if isinstance(override, dict):
                provider = override.get('provider')
                model = override.get('model')

                if not model:
                    continue

                if provider and provider not in settings.PROVIDER_MODELS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent {agent_key} 的提供商配置无效: {provider} 不是有效的提供商。可用提供商: {', '.join(settings.PROVIDER_MODELS.keys())}"
                    )

                if model and provider:
                    if not settings.validate_model(provider, model):
                        available_models = settings.get_models_for_provider(provider)
                        model_names = [m["id"] for m in available_models] if available_models else []
                        raise HTTPException(
                            status_code=400,
                            detail=f"Agent {agent_key} 的模型配置无效: {model} 在提供商 {provider} 中不存在。可用模型: {', '.join(model_names)}"
                        )

                fallbacks = override.get('fallbacks', [])
                if fallbacks:
                    for idx, fallback in enumerate(fallbacks):
                        fb_provider = fallback.get('provider')
                        fb_model = fallback.get('model')

                        if fb_model and fb_provider:
                            if not settings.validate_model(fb_provider, fb_model):
                                available_models = settings.get_models_for_provider(fb_provider)
                                model_names = [m["id"] for m in available_models] if available_models else []
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Agent {agent_key} 的降级选项 #{idx+1} 无效: {fb_model} 在提供商 {fb_provider} 中不存在。可用模型: {', '.join(model_names)}"
                                )

    merged = update_user_settings(
        llm_apis=[x.model_dump() for x in request.llm_apis] if request.llm_apis is not None else None,
        volcengine=request.volcengine.model_dump() if request.volcengine is not None else None,
        agent_llm_overrides=request.agent_llm_overrides if request.agent_llm_overrides is not None else None,
    )
    return UserSettingsResponse(
        llm_apis=merged.get("llm_apis") or [],
        volcengine=merged.get("volcengine"),
        agent_llm_overrides=merged.get("agent_llm_overrides") or {},
    )


@router.get("/outputs", response_model=OutputFileListResponse)
async def get_output_files(limit: int = 20, offset: int = 0):
    """获取历史输出文件列表"""
    output_dir = Path("outputs")
    if not output_dir.exists():
        return OutputFileListResponse(files=[], total=0)

    md_files = list(output_dir.glob("*.md"))
    md_files = [f for f in md_files if f.name != "TECH_DOC.md"]
    md_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    total = len(md_files)
    paginated_files = md_files[offset:offset + limit]

    file_infos = []
    for file_path in paginated_files:
        stat = file_path.stat()
        parts = file_path.stem.split("_", 2)
        if len(parts) >= 3:
            topic = parts[2]
        else:
            topic = file_path.stem

        file_infos.append(OutputFileInfo(
            filename=file_path.name,
            topic=topic,
            created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            size=stat.st_size
        ))

    return OutputFileListResponse(files=file_infos, total=total)


@router.get("/outputs/{filename}", response_model=OutputFileContentResponse)
async def get_output_file(filename: str):
    """获取指定输出文件的内容"""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    file_path = Path("outputs") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="不是有效的文件")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return OutputFileContentResponse(
            filename=filename,
            content=content,
            created_at=created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


# --- 模型管理接口 ---

@router.get("/models")
async def get_models():
    """获取所有提供商的模型列表"""
    models = settings.get_all_models()
    return models


@router.post("/validate-model")
async def validate_model(payload: dict):
    """验证提供商-模型组合是否有效"""
    provider = payload.get("provider", "").strip()
    model = payload.get("model", "").strip()

    if not provider or not model:
        return {"valid": False, "message": "提供商和模型参数不能为空"}

    is_valid = settings.validate_model(provider, model)

    if is_valid:
        return {"valid": True, "message": f"模型 {model} 在提供商 {provider} 中有效"}
    else:
        available_models = settings.get_models_for_provider(provider)
        if available_models:
            model_names = [m["id"] for m in available_models]
            return {"valid": False, "message": f"模型 {model} 在提供商 {provider} 中无效。可用模型: {', '.join(model_names)}"}
        else:
            return {"valid": False, "message": f"提供商 {provider} 不存在或没有可用模型"}


# --- 小红书 MCP 发布接口 ---

@router.get("/xhs/status")
async def get_xhs_status():
    """检查小红书 MCP 服务状态和登录状态"""
    from app.services.xiaohongshu_publisher import xiaohongshu_publisher
    from app.schemas import XhsStatusResponse

    status = await xiaohongshu_publisher.get_status()
    return XhsStatusResponse(
        mcp_available=status.get("mcp_available", False),
        login_status=status.get("login_status", False),
        message=status.get("message", "")
    )


@router.post("/xhs/publish")
async def publish_to_xhs(request: XhsPublishRequest):
    """手动发布内容到小红书"""
    from app.services.xiaohongshu_publisher import xiaohongshu_publisher
    from app.schemas import XhsPublishResponse

    if not request.title or not request.content:
        return XhsPublishResponse(success=False, message="标题和内容不能为空")

    if not request.images:
        return XhsPublishResponse(success=False, message="至少需要一张图片")

    result = await xiaohongshu_publisher.publish_content(
        title=request.title,
        content=request.content,
        images=request.images,
        tags=request.tags
    )

    return XhsPublishResponse(
        success=result.get("success", False),
        message=result.get("message") or result.get("error", "发布失败"),
        data=result.get("data")
    )
