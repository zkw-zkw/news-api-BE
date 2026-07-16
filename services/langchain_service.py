import os

from langchain.chat_models import init_chat_model

from langchain.agents import create_agent

from utils.tools import create_langchain_tools

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

SYSTEM_PROMPT = "你是新闻资讯AI助手，连接着一个新闻数据库。\n\n规则：\n1. 任何与新闻相关的问题，必须先调用工具查数据库，不要凭知识回答\n2. 「热度」「浏览」「最多」「前N」「排行」→ 如果带了分类名用 get_hot_news_by_category，否则用 get_hot_news\n3. 「搜索」「找」「关于」「关键词」「查找」「查询」→ 调用 search_news\n4. 「分类」「社会」「国际」「科技」「体育」「娱乐」「财经」「国内」「头条」等分类名 → 调用 get_news_by_category 获取该分类新闻列表\n5. 例如「社会新闻热度前五」→ get_hot_news_by_category(category_name=\"社会\", top_n=5)\n6. 例如「搜索关于芯片的新闻」→ search_news(keyword=\"芯片\")\n7. 例如「查看科技分类的新闻」→ get_news_by_category(category_name=\"科技\", page=1)\n8. 用户问什么就用对应的工具，不要自己编造数据\n9. 提到新闻标题时，用Markdown链接格式 [标题](/news/detail/数字)，例如 [我国GDP增长5.2%](/news/detail/4)"

def _build_agent(db):
    llm = init_chat_model(
        model="qwen-plus",
        model_provider = "qwen",
        api_key=DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0,
    )
    tools = create_langchain_tools(db)
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

async def stream_agent(db, user_msg: str):
    agent = _build_agent(db)
    async for event in agent.astream_events(
        {"messages": [("human", user_msg)]},
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield content
