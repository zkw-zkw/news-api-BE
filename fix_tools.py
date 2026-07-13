import sys

c = open(sys.argv[1], "r", encoding="utf-8").read()

# 1. Add LangChain import after the existing imports
c = c.replace(
    "from datetime import datetime, timedelta",
    "from datetime import datetime, timedelta\nfrom langchain_core.tools import Tool"
)

# 2. Add create_langchain_tools function before TOOL_MAP
old_end = "TOOL_MAP = {\n    \"get_categories\": get_categories,\n    \"search_news\": search_news,\n    \"get_news_by_category\": get_news_by_category,\n    \"get_hot_news\": get_hot_news,\n    \"get_hot_news_by_category\": get_hot_news_by_category,\n    \"get_news_detail\": get_news_detail,\n    \"get_news_count_by_category\": get_news_count_by_category,\n    \"get_recent_news\": get_recent_news,\n    \"get_news_by_author\": get_news_by_author,\n}"

new_end = """def create_langchain_tools(db):
    \"\"\"创建绑定数据库会话的 LangChain 工具列表\"\"\"
    return [
        Tool(name="get_categories", description="获取所有新闻分类列表", coroutine=lambda: get_categories(db)),
        Tool(name="search_news", description="按关键词搜索新闻标题和简介（传keyword）", coroutine=lambda kw: search_news(db, keyword=kw)),
        Tool(name="get_news_by_category", description="按分类名称获取新闻列表（传category_name, page可选）", coroutine=lambda cn, p=1: get_news_by_category(db, category_name=cn, page=p)),
        Tool(name="get_hot_news", description="获取浏览量最高的N条新闻（传top_n, 默认5）", coroutine=lambda n=5: get_hot_news(db, top_n=n)),
        Tool(name="get_hot_news_by_category", description="获取指定分类下浏览量最高的新闻（传category_name, top_n可选）", coroutine=lambda cn, n=5: get_hot_news_by_category(db, category_name=cn, top_n=n)),
        Tool(name="get_news_detail", description="获取新闻详情（传news_id）", coroutine=lambda nid: get_news_detail(db, news_id=nid)),
        Tool(name="get_news_count_by_category", description="统计分类下新闻数量（传category_id）", coroutine=lambda cid: get_news_count_by_category(db, category_id=cid)),
        Tool(name="get_recent_news", description="获取最近N天内的新闻（传days）", coroutine=lambda d: get_recent_news(db, days=d)),
        Tool(name="get_news_by_author", description="按作者查新闻（传author）", coroutine=lambda a: get_news_by_author(db, author=a)),
    ]

""" + old_end

c = c.replace(old_end, new_end)

open(sys.argv[1], "w", encoding="utf-8").write(c)
print("Done")
