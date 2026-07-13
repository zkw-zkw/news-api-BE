import json, os, logging, httpx
from sqlalchemy.ext.asyncio import AsyncSession
from utils.tools import TOOL_DEFS, TOOL_MAP

logger = logging.getLogger(__name__)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
SYSTEM_PROMPT = "你是新闻资讯AI助手，连接着一个新闻数据库。\n\n规则：\n1. 任何与新闻相关的问题，必须先调用工具查数据库\n2. 热度排行用 get_hot_news 或 get_hot_news_by_category\n3. 搜索用 search_news\n4. 按分类查用 get_news_by_category\n5. 不要自己编造数据"

async def call_nonstream(messages, tools=None):
    body = {"model": "qwen-plus", "messages": messages}
    if tools:
        body["tools"] = tools
    headers = {"Authorization": "Bearer " + DASHSCOPE_API_KEY, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(API_URL, headers=headers, json=body)
        r.raise_for_status()
        return r.json()

async def call_stream(messages, tools=None):
    body = {"model": "qwen-plus", "messages": messages, "stream": True}
    if tools:
        body["tools"] = tools
    headers = {"Authorization": "Bearer " + DASHSCOPE_API_KEY, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", API_URL, headers=headers, json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    yield line[6:]

async def run_agent(db: AsyncSession, user_msg: str) -> str:
    if not DASHSCOPE_API_KEY:
        return "AI 服务未配置"
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}]
    resp = await call_nonstream(msgs, tools=TOOL_DEFS)
    msg = resp.get("choices", [{}])[0].get("message", {})
    content = msg.get("content", "")
    tool_calls = msg.get("tool_calls", [])
    if tool_calls:
        msgs.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            args = json.loads(fn.get("arguments", "{}")) if fn.get("arguments") else {}
            func = TOOL_MAP.get(name)
            result = await func(db, **args) if func else {"error": "unknown tool"}
            msgs.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False), "tool_call_id": tc.get("id", "")})
        final = await call_nonstream(msgs)
        return final.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
    return content or ""

async def stream_agent(db: AsyncSession, user_msg: str):
    if not DASHSCOPE_API_KEY:
        yield "AI 服务未配置"
        return
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}]
    resp = await call_nonstream(msgs, tools=TOOL_DEFS)
    msg = resp.get("choices", [{}])[0].get("message", {})
    content = msg.get("content", "")
    tool_calls = msg.get("tool_calls", [])
    if tool_calls:
        msgs.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            args = json.loads(fn.get("arguments", "{}")) if fn.get("arguments") else {}
            func = TOOL_MAP.get(name)
            result = await func(db, **args) if func else {"error": "unknown tool"}
            msgs.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False), "tool_call_id": tc.get("id", "")})
        async for chunk in call_stream(msgs):
            yield chunk
    else:
        yield content or ""
