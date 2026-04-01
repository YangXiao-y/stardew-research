"""
工具集成层 - 搜索、网页爬取等
"""

import os
import json
import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SearchTool:
    """Serper 搜索工具"""

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY", "")
        self.base_url = "https://google.serper.dev"

    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """执行搜索查询"""
        if not self.api_key:
            logger.warning("⚠️ SERPER_API_KEY 未设置")
            return []

        try:
            payload = {
                "q": query,
                "num": num_results,
                "gl": "cn" if "中文" in query or any(ord(c) > 127 for c in query) else "us"
            }

            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            logger.info(f"🔍 搜索: {query[:50]}...")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    results = []

                    # 处理有机搜索结果
                    for item in data.get("organic", [])[:num_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "serper"
                        })

                    logger.info(f"✅ 搜索返回 {len(results)} 条结果")
                    return results
                else:
                    logger.error(f"❌ 搜索失败: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"❌ 搜索异常: {str(e)}")
            return []

class WebScraperTool:
    """网页爬取工具 (Browserless)"""

    def __init__(self):
        self.api_key = os.getenv("BROWSERLESS_API_KEY", "")
        self.base_url = os.getenv("BROWSERLESS_URL", "https://api.browserless.io/v2")

    async def scrape_content(self, url: str) -> Optional[str]:
        """爬取网页内容"""
        if not self.api_key:
            logger.warning("⚠️ BROWSERLESS_API_KEY 未设置")
            return None

        try:
            logger.info(f"📄 正在爬取: {url}")

            payload = {
                "url": url,
                "waitForNavigation": ["networkidle2"],
            }

            headers = {
                "Cache-Control": "no-cache",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/content?token={self.api_key}",
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("data", {}).get("content", "")
                    logger.info(f"✅ 爬取成功")
                    return content[:5000]  # 限制内容长度
                else:
                    logger.warning(f"⚠️ 爬取失败: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"❌ 爬取异常: {str(e)}")
            return None

class ToolManager:
    """工具管理器"""

    def __init__(self):
        self.search_tool = SearchTool()
        self.scraper_tool = WebScraperTool()

    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """执行搜索"""
        return await self.search_tool.search(query, num_results)

    async def scrape(self, url: str) -> Optional[str]:
        """爬取内容"""
        return await self.scraper_tool.scrape_content(url)

    async def search_and_scrape(self, query: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """搜索并爬取前N个结果"""
        search_results = await self.search(query, max_pages)

        enriched_results = []
        for result in search_results:
            scraped_content = await self.scrape(result["url"])
            if scraped_content:
                result["full_content"] = scraped_content
            enriched_results.append(result)

        return enriched_results

# 全局工具管理器实例
tool_manager = ToolManager()
