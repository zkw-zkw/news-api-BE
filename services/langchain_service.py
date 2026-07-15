import json, os, logging

from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from utils.tools import create_langchain_tools

logger = logging.getLogger(__name__)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

SYSTEM_PROMPT = "你是新闻资讯AI助手，连接着一个新闻数据库。\n\n规则：\n1. 任何与新闻相关的问题，必须先调用工具查数据库，不要凭知识回答\n2. 「热度」「浏览」「最多」「前N」「排行」→ 如果带了分类名用 get_hot_news_by_category，否则用 get_hot_news\n3. 「搜索」「找」「关于」「关键词」「查找」「查询」→ 调用 search_news\n4. 「分类」「社会」「国际」「科技」「体育」「娱乐」「财经」「国内」「头条」等分类名 → 调用 get_news_by_category 获取该分类新闻列表\n5. 例如「社会新闻热度前五」→ get_hot_news_by_category(category_name=\"社会\", top_n=5)\n6. 例如「搜索关于芯片的新闻」→ search_news(keyword=\"芯片\")\n7. 例如「查看科技分类的新闻」→ get_news_by_category(category_name=\"科技\", page=1)\n8. 用户问什么就用对应的工具，不要自己编造数据\n9. 提到新闻标题时，用Markdown链接格式 [标题](/news/detail/数字)，例如 [我国GDP增长5.2%](/news/detail/4)"

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

def _build_executor(db):
    llm = ChatOpenAI(
        model="qwen-plus",
        openai_api_key=DASHSCOPE_API_KEY,
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0,
    )
    tools = create_langchain_tools(db)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

async def run_agent(db, user_msg: str) -> str:
    if not DASHSCOPE_API_KEY:
        return "AI 服务未配置（DASHSCOPE_API_KEY 为空）"
    executor = _build_executor(db)
    result = await executor.ainvoke({"input": user_msg})
    return result.get("output", "")

async def stream_agent(db, user_msg: str):
    if not DASHSCOPE_API_KEY:
        yield "AI 服务未配置"
        return
    executor = _build_executor(db)
    async for step in executor.astream({"input": user_msg}):
        if "output" in step:
            yield step["output"]
