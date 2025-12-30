"""
Cookie 管理模块
用于自动保存和加载各平台的登录 Cookie，避免每次都需要扫码登录
"""
import os
import json
from typing import Optional, Dict, List
from pathlib import Path

COOKIE_FILE = Path("cookies.json")


class CookieManager:
    """管理各平台的 Cookie"""
    
    def __init__(self, cookie_file: Path = COOKIE_FILE):
        self.cookie_file = cookie_file
        self.cookies: Dict[str, str] = self._load_cookies()
    
    def _load_cookies(self) -> Dict[str, str]:
        """从文件加载 Cookie"""
        if not self.cookie_file.exists():
            return {}
        
        try:
            with open(self.cookie_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[警告] 加载 Cookie 文件失败: {e}")
            return {}
    
    def _save_cookies(self):
        """保存 Cookie 到文件"""
        try:
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(self.cookies, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[警告] 保存 Cookie 文件失败: {e}")
    
    def get_cookie(self, platform: str) -> Optional[str]:
        """获取指定平台的 Cookie"""
        return self.cookies.get(platform)
    
    def save_cookie(self, platform: str, cookie_str: str):
        """保存指定平台的 Cookie"""
        if cookie_str and cookie_str.strip():
            self.cookies[platform] = cookie_str.strip()
            self._save_cookies()
            print(f"[成功] 已保存 {platform} 的 Cookie")
        else:
            print(f"[警告] Cookie 为空，未保存 {platform} 的 Cookie")
    
    def save_cookies_from_browser(self, platform: str, cookies: List[Dict]):
        """从浏览器 Cookie 列表提取并保存"""
        from MediaCrawler.tools.crawler_util import convert_cookies
        cookie_str, _ = convert_cookies(cookies)
        if cookie_str:
            self.save_cookie(platform, cookie_str)
        else:
            print(f"[警告] 未能从浏览器提取 {platform} 的 Cookie")
    
    def remove_cookie(self, platform: str):
        """删除指定平台的 Cookie"""
        if platform in self.cookies:
            del self.cookies[platform]
            self._save_cookies()
            print(f"[成功] 已删除 {platform} 的 Cookie")
    
    def list_cookies(self) -> Dict[str, bool]:
        """列出所有已保存的 Cookie"""
        return {platform: bool(cookie) for platform, cookie in self.cookies.items()}


# 全局实例
cookie_manager = CookieManager()
