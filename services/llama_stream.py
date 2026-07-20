"""
LLaMA 流式服务（AgentCN）：异步 SSE 客户端
"""
import httpx, json
from typing import AsyncGenerator
from core.config import load_config

class LlamaStream:
    def __init__(self, base_url: str = None):
        cfg = load_config()
        self.base_url = base_url or cfg.get("llama_base_url", "http://localhost:8080")
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    def _ensure_client(self):
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)

    async def health_check(self) -> bool:
        self._ensure_client()
        try:
            r = await self.client.get(f"{self.base_url}/health")
            return r.status_code == 200
        except:
            return False

    async def stream_chat(self, user_message: str) -> AsyncGenerator[str, None]:
        self._ensure_client()
        payload = {"messages": [{"role": "user", "content": user_message}], "stream": True}
        async with self.client.stream("POST", f"{self.base_url}/v1/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[len("data: "):]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue