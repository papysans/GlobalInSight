from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


_SETTINGS_FILE = Path("cache") / "user_settings.json"


def _ensure_parent_dir() -> None:
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _safe_load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8") or "{}")
    except Exception:
        # Corrupted file or invalid json: don't break the server.
        return {}


def load_user_settings() -> Dict[str, Any]:
    """Load persisted user settings from cache (safe)."""
    return _safe_load_json(_SETTINGS_FILE)


def save_user_settings(data: Dict[str, Any]) -> None:
    """Persist user settings to cache."""
    _ensure_parent_dir()
    _SETTINGS_FILE.write_text(
        json.dumps(data or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_user_llm_apis() -> List[Dict[str, Any]]:
    data = load_user_settings()
    apis = data.get("llm_apis")
    return apis if isinstance(apis, list) else []


def get_volcengine_settings() -> Dict[str, Any]:
    data = load_user_settings()
    volc = data.get("volcengine")
    return volc if isinstance(volc, dict) else {}


def get_image_generation_count() -> int:
    """
    Get the number of images to generate.
    Returns the user-configured count or default (2).
    Supports 0 (disabled) to 9 images.
    """
    volc = get_volcengine_settings()
    count = volc.get("image_count")
    # 支持 0（禁用生图）到 9 张
    if isinstance(count, int) and 0 <= count <= 9:
        return count
    return 2  # 默认生成2张图片


def get_agent_llm_overrides() -> Dict[str, Dict[str, Any]]:
    """
    Get agent LLM overrides in new format: {agent_name: {provider, model, apiId}}
    Also handles backward compatibility with old format (agent_name: provider_string)
    """
    data = load_user_settings()
    overrides = data.get("agent_llm_overrides")
    if not isinstance(overrides, dict):
        return {}
    
    out: Dict[str, Dict[str, Any]] = {}
    for k, v in overrides.items():
        kk = str(k).strip()
        if not kk:
            continue
            
        # Handle both old format (string) and new format (dict)
        if isinstance(v, str):
            # Old format: just provider key
            vv = v.strip()
            if vv:
                out[kk] = {"provider": vv, "model": "", "apiId": None}
        elif isinstance(v, dict):
            # New format: {provider, model, apiId}
            provider = (v.get("provider") or "").strip()
            model = (v.get("model") or "").strip()
            apiId = v.get("apiId")
            if provider:
                out[kk] = {"provider": provider, "model": model, "apiId": apiId}
    
    return out


def update_user_settings(
    *,
    llm_apis: Optional[List[Dict[str, Any]]] = None,
    volcengine: Optional[Dict[str, Any]] = None,
    agent_llm_overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Partial update; returns the merged settings."""
    data = load_user_settings()
    if llm_apis is not None:
        data["llm_apis"] = llm_apis
    if volcengine is not None:
        data["volcengine"] = volcengine
    if agent_llm_overrides is not None:
        data["agent_llm_overrides"] = agent_llm_overrides
    save_user_settings(data)
    return data


def _extract_llm_keys(apis: List[Dict[str, Any]], provider_key: str) -> List[str]:
    """Extract keys for a provider from stored llm_apis."""
    out: List[str] = []
    for it in apis or []:
        if not isinstance(it, dict):
            continue
        pk = (it.get("providerKey") or it.get("provider_key") or "").strip().lower()
        if pk != (provider_key or "").strip().lower():
            continue
        key_raw = (it.get("key") or "").strip()
        if not key_raw:
            continue
        # Allow users to paste multiple keys in one field: split by comma/newline/semicolon.
        normalized = (
            key_raw.replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace(";", ",")
            .replace("\n", ",")
        )
        parts = [p.strip() for p in normalized.split(",") if p.strip()]
        if not parts:
            continue
        out.extend(parts)
    return out


def get_effective_llm_keys(*, provider_key: str, env_keys: List[str]) -> List[str]:
    """
    Merge user-provided keys (from frontend) with env keys.
    Order: user keys first, then env keys. Dedupe while preserving order.
    """
    user_keys = _extract_llm_keys(get_user_llm_apis(), provider_key)
    merged: List[str] = []
    for k in (user_keys or []) + (env_keys or []):
        k = (k or "").strip()
        if not k:
            continue
        if k in merged:
            continue
        merged.append(k)
    return merged


def get_effective_volcengine_credentials(
    *, env_access_key: str, env_secret_key: str
) -> Dict[str, str]:
    """
    Return AK/SK for volcengine visual API.
    Prefer cached settings; fallback to .env.
    """
    volc = get_volcengine_settings()
    ak = (volc.get("access_key") or volc.get("ak") or "").strip() or (env_access_key or "").strip()
    sk = (volc.get("secret_key") or volc.get("sk") or "").strip() or (env_secret_key or "").strip()
    return {"access_key": ak, "secret_key": sk}


def get_agent_api_config(agent_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the specific API configuration for an agent based on agent_llm_overrides.
    Returns: {provider, model, key} or None if no override configured.
    """
    overrides = get_agent_llm_overrides()
    override = overrides.get(agent_name)
    if not override:
        return None
    
    provider = override.get("provider")
    model = override.get("model", "")
    
    if not provider:
        return None
    
    # Find the matching API configuration from llm_apis
    apis = get_user_llm_apis()
    for api in apis:
        api_provider = (api.get("providerKey") or api.get("provider_key") or "").strip().lower()
        api_model = (api.get("model") or "").strip()
        
        # Match by provider and model
        if api_provider == provider.lower():
            # If model is specified in override, must match
            if model and api_model != model:
                continue
            # If no model specified in override, use first matching provider
            
            key = (api.get("key") or "").strip()
            if key:
                return {
                    "provider": provider,
                    "model": api_model or model,
                    "key": key
                }
    
    return None

