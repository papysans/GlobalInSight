import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from pathlib import Path

# TopHub source ids to probe
SOURCES = {
    "hot": "全平台热榜",
    "KqndgxeLl9": "微博热搜榜",
    "74KvxwokxM": "B站全站日榜",
    "Jb0vmloB1G": "百度实时热点",
    "Om4ejxvxEN": "百度贴吧热榜",
    "DpQvNABoNE": "抖音热榜",
    "MZd7PrPerO": "快手热榜",
    "mproPpoq6O": "知乎热榜",
}

BASE_URL = "https://tophub.today/n/"
HOT_URL = "https://tophub.today/hot"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://tophub.today/",
}

OUTPUT_DIR = Path("outputs/probe_html")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def fetch_html(client: httpx.AsyncClient, source_id: str) -> str:
    # 全平台热榜用 /hot URL，其他用 /n/{source_id}
    url = HOT_URL if source_id == "hot" else f"{BASE_URL}{source_id}"
    resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    return resp.text

async def probe_source(client: httpx.AsyncClient, source_id: str, name: str):
    html = await fetch_html(client, source_id)
    (OUTPUT_DIR / f"{source_id}_{name}.html").write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    
    # 全榜特殊处理
    if source_id == "hot":
        items = soup.find_all("li", class_="child-item")
        title_text = ""
        hot_text = ""
        platform_text = ""
        
        if items:
            item = items[0]
            # 标题
            title_a = item.select_one("p.medium-txt a")
            if title_a:
                title_text = title_a.get_text(strip=True)
            
            # 平台和热度
            small_txt = item.select_one("p.small-txt")
            if small_txt:
                text = small_txt.get_text(strip=True)
                # 用分隔符 ‧ 或 · 分割
                parts = re.split(r'[‧·]', text)
                if len(parts) >= 1:
                    platform_text = parts[0].strip()
                if len(parts) >= 2:
                    hot_text = parts[1].strip()
    else:
        # 普通榜单处理
        table = soup.find("table", class_="table")
        first_item = None
        if table:
            rows = table.find_all("tr")[1:]
            if rows:
                first_item = rows[0]
        else:
            anchors = soup.select("a[itemid]") or soup.select("a[href*='/link?']")
            if anchors:
                first_item = anchors[0].parent if anchors[0].parent else anchors[0]

        hot_text = ""
        title_text = ""
        platform_text = ""
        if first_item:
            # title
            link = first_item.find("a", href=True)
            if link:
                title_text = link.get_text(strip=True)
            # possible heat nodes
            candidates = first_item.select(".item-desc, .item-extra")
            if not candidates:
                candidates = first_item.find_all(
                    lambda tag: (
                        tag.get("class") and any(
                            key in " ".join(tag.get("class"))
                            for key in ["hot", "heat", "count", "hotness", "热度"]
                        )
                    )
                )
            # data-e2e 或特定 td.ws
            if not candidates:
                data_e2e = first_item.find_all(attrs={"data-e2e": True})
                candidates = data_e2e if data_e2e else candidates
            # gather text
            if candidates:
                hot_text = " | ".join(c.get_text(strip=True) for c in candidates if c.get_text(strip=True))
            if not hot_text:
                # Weibo: td.ws contains heat
                ws_td = first_item.find("td", class_="ws")
                if ws_td:
                    hot_text = ws_td.get_text(strip=True)
            if not hot_text:
                # fallback to last cell text if table row
                tds = first_item.find_all("td")
                if tds:
                    hot_text = tds[-1].get_text(strip=True)

            # 清洗抖音热度：提取 "12345次播放"
            if hot_text:
                play_match = re.search(r'([\d,\.]+\s*次播放)', hot_text)
                if play_match:
                    hot_text = play_match.group(1).strip()

    print(f"[{name}] title: {title_text or 'N/A'}")
    if source_id == "hot" and platform_text:
        print(f"[{name}] platform: {platform_text}")
    print(f"[{name}] heat:  {hot_text or 'N/A'}")
    print(f"HTML saved: {OUTPUT_DIR / f'{source_id}_{name}.html'}")
    print("-" * 60)

async def main():
    async with httpx.AsyncClient() as client:
        for sid, name in SOURCES.items():
            try:
                await probe_source(client, sid, name)
            except Exception as e:
                print(f"[{name}] error: {e}")
                print(f"(Check saved HTML if available.)")
                print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
