"""
网络搜索插件（AgentCN）：DuckDuckGo/Bing 双源，质量评分（仅供参考）
"""
import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import quote
from datetime import datetime
from typing import List, Dict
from plugins.base import IPlugin

class WebSearchPlugin(IPlugin):
    @property
    def name(self) -> str:
        return "web_search"

    def execute(self, params: dict, context: dict) -> str:
        query = params.get("query", "")
        if not query:
            return "No query"
        results = self._search_duckduckgo(query) or self._search_bing(query)
        if not results:
            return "No results found."
        self._boost_consensus(results)
        out = "Search results (quality estimate):\n"
        for i, r in enumerate(results, 1):
            out += f"{i}. [{r['score']}%] {r['title']}\n{r['content'][:200]}...\n\n"
        return out

    def _search_duckduckgo(self, query: str) -> List[Dict]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            return self._parse_common(soup, ".result")
        except:
            return []

    def _search_bing(self, query: str) -> List[Dict]:
        try:
            url = f"https://www.bing.com/search?q={quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            return self._parse_common(soup, "li.b_algo")
        except:
            return []

    def _parse_common(self, soup: BeautifulSoup, result_selector: str) -> List[Dict]:
        results = []
        for item in soup.select(result_selector):
            title_elem = item.select_one("a") or item.select_one("h2 a")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            link = title_elem.get("href")
            snippet_elem = item.select_one(".snippet") or item.select_one(".b_caption p")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            page_html = self._fetch_page(link)
            if not page_html:
                continue
            page_text = BeautifulSoup(page_html, "html.parser").get_text(" ", strip=True)
            score = self._quality_score(link, page_text)
            results.append({
                "title": title,
                "link": link,
                "snippet": snippet,
                "content": page_text[:500],
                "score": score,
                "keywords": set(title.lower().split() + snippet.lower().split())
            })
            if len(results) >= 5:
                break
        return results

    def _fetch_page(self, url: str) -> str:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            resp.raise_for_status()
            doc = Document(resp.text)
            return doc.summary()
        except:
            return ""

    def _quality_score(self, url: str, text: str) -> int:
        score = 80
        if ".gov" in url or ".edu" in url:
            score += 10
        import re
        years = re.findall(r"\b(20\d{2})\b", text)
        if years:
            oldest = min(int(y) for y in years)
            if datetime.now().year - oldest > 1:
                score -= 5
        return max(0, min(95, score))

    def _boost_consensus(self, results: List[Dict]):
        if len(results) < 2:
            return
        overlaps = []
        for i in range(len(results)):
            for j in range(i+1, len(results)):
                s1 = results[i]["keywords"]
                s2 = results[j]["keywords"]
                if not s1 or not s2:
                    continue
                jacc = len(s1 & s2) / len(s1 | s2) if s1 | s2 else 0
                overlaps.append(jacc)
        if overlaps and (sum(overlaps)/len(overlaps)) > 0.3:
            for r in results:
                r["score"] = 95