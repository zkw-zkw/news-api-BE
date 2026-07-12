import json, os, logging
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from utils.tools import TOOL_DEFS, TOOL_MAP

logger = logging.getLogger(__name__)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
SYSTEM_PROMPT = "你是新闻资讯AI助手，连接着一个新闻数据库。\n\n规则：\n1. 任何与新闻相关的问题，必须先调用工具查数据库，不要凭知识回答\n2. 「热度」「浏览」「最多」「前N」「排行」→ 如果带了分类名用 get_hot_news_by_category，否则用 get_hot_news\n3. 「搜索」「找」「关于」「关键词」「查找」「查询」→ 调用 search_news\n4. 「分类」「社会」「国际」「科技」「体育」「娱乐」「财经」「国内」「头条」等分类名 → 调用 get_news_by_category 获取该分类新闻列表\n5. 例如「社会新闻热度前五」→ get_hot_news_by_category(category_name=\"社会\", top_n=5)\n6. 例如「搜索关于芯片的新闻」→ search_news(keyword=\"芯片\")\n7. 例如「查看科技分类的新闻」→ get_news_by_category(category_name=\"科技\", page=1)\n8. 用户问什么就用对应的工具，不要自己编造数据"

async def call_nonstream(messages, tools=None):
    body = {"model": "qwen-plus", "messages": messages}
    if tools: body["tools"] = tools
    headers = {"Authorization": "Bearer " + DASHSCOPE_API_KEY, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(API_URL, headers=headers, json=body)
        r.raise_for_status()
        return r.json()

async def call_stream(messages, tools=None):
    body = {"model": "qwen-plus", "messages": messages, "stream": True}
    if tools: body["tools"] = tools
    headers = {"Authorization": "Bearer " + DASHSCOPE_API_KEY, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", API_URL, headers=headers, json=body) as resp:
            resp.raise_for_status()
            buf = ""
            async for chunk in resp.aiter_bytes():
                buf += chunk.decode()
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line.startswith("data:"):
                        d = line[6:].strip()
                        if d and d != "[DONE]":
                            yield d

async def run_agent(db: AsyncSession, user_msg: str) -> str:
    if not DASHSCOPE_API_KEY:
        return "AI 服务未配置（DASHSCOPE_API_KEY 为空）"
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

    # First pass: non-streaming to detect tool calls
    resp = await call_nonstream(msgs, tools=TOOL_DEFS)
    msg = resp.get("choices", [{}])[0].get("message", {})
    content = msg.get("content", "")
    tool_calls = msg.get("tool_calls", [])

    if content:
        yield content

    if tool_calls:
        msgs.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            args = json.loads(fn.get("arguments", "{}")) if fn.get("arguments") else {}
            func = TOOL_MAP.get(name)
            result = await func(db, **args) if func else {"error": "unknown"}
            msgs.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False), "tool_call_id": tc.get("id", "")})
        async for data in call_stream(msgs):
            try:
                parsed = json.loads(data)
                c = parsed.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if c: yield c
            except json.JSONDecodeError:
                pass

