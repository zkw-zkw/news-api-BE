import json
from crud import news
from models.news import News, Category
from sqlalchemy import select
from datetime import datetime, timedelta
from langchain_core.tools import Tool

TOOL_DEFS = [
    {"type": "function", "function": {"name": "get_categories", "description": "get all news categories", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "search_news", "description": "search news by keyword in title and description", "parameters": {"type": "object", "properties": {"keyword": {"type": "string", "description": "search keyword"}}, "required": ["keyword"]}}},
    {"type": "function", "function": {"name": "get_news_by_category", "description": "get news list by category name", "parameters": {"type": "object", "properties": {"category_name": {"type": "string", "description": "category name"}, "page": {"type": "integer", "description": "page number, default 1"}}, "required": ["category_name"]}}},
    {"type": "function", "function": {"name": "get_hot_news", "description": "get top N most viewed news", "parameters": {"type": "object", "properties": {"top_n": {"type": "integer", "description": "number of news, default 5"}}}}},
    {"type": "function", "function": {"name": "get_hot_news_by_category", "description": "get top N most viewed news in a category", "parameters": {"type": "object", "properties": {"category_name": {"type": "string", "description": "category name"}, "top_n": {"type": "integer", "description": "number of news, default 5"}}, "required": ["category_name"]}}},
    {"type": "function", "function": {"name": "get_news_detail", "description": "get news detail by id", "parameters": {"type": "object", "properties": {"news_id": {"type": "integer", "description": "news id"}}, "required": ["news_id"]}}},
    {"type": "function", "function": {"name": "get_news_count_by_category", "description": "count news in a category", "parameters": {"type": "object", "properties": {"category_id": {"type": "integer", "description": "category id"}}, "required": ["category_id"]}}},
    {"type": "function", "function": {"name": "get_recent_news", "description": "get news from last N days", "parameters": {"type": "object", "properties": {"days": {"type": "integer", "description": "number of days"}}, "required": ["days"]}}},
    {"type": "function", "function": {"name": "get_news_by_author", "description": "get news by author name", "parameters": {"type": "object", "properties": {"author": {"type": "string", "description": "author name"}}, "required": ["author"]}}},
]

async def get_categories(db):
    cats = await news.get_categories(db)
    return json.dumps([{"id": c.id, "name": c.name} for c in cats], ensure_ascii=False)

async def search_news(db, keyword: str):
    stmt = select(News).where(News.title.like(f"%{keyword}%") | News.description.like(f"%{keyword}%")).limit(20)
    r = await db.execute(stmt)
    items = [{"id": n.id, "title": n.title, "views": n.views} for n in r.scalars().all()]
    return json.dumps(items, ensure_ascii=False)

async def get_news_by_category(db, category_name: str, page: int = 1):
    cats = await news.get_categories(db)
    for c in cats:
        if c.name == category_name:
            skip = (page - 1) * 10
            items = await news.get_news_list(db, c.id, skip, 10)
            return json.dumps([{"id": n.id, "title": n.title, "views": n.views} for n in items], ensure_ascii=False)
    return json.dumps({"error": f"category {category_name} not found"}, ensure_ascii=False)

async def get_hot_news(db, top_n: int = 5):
    stmt = select(News).order_by(News.views.desc()).limit(top_n)
    r = await db.execute(stmt)
    items = [{"id": n.id, "title": n.title, "views": n.views} for n in r.scalars().all()]
    return json.dumps(items, ensure_ascii=False)

async def get_hot_news_by_category(db, category_name: str, top_n: int = 5):
    cats = await news.get_categories(db)
    cat_id = None
    for c in cats:
        if c.name == category_name:
            cat_id = c.id
            break
    if not cat_id:
        return json.dumps({"error": f"category {category_name} not found"}, ensure_ascii=False)
    stmt = select(News).where(News.category_id == cat_id).order_by(News.views.desc()).limit(top_n)
    r = await db.execute(stmt)
    items = [{"id": n.id, "title": n.title, "views": n.views} for n in r.scalars().all()]
    return json.dumps(items, ensure_ascii=False)

async def get_news_detail(db, news_id: int):
    n = await news.get_news_detail(db, news_id)
    if not n:
        return json.dumps({"error": "news not found"}, ensure_ascii=False)
    return json.dumps({"id": n.id, "title": n.title, "content": n.content, "views": n.views}, ensure_ascii=False)

async def get_news_count_by_category(db, category_id: int):
    count = await news.get_news_count(db, category_id)
    return json.dumps({"category_id": category_id, "count": count}, ensure_ascii=False)

async def get_recent_news(db, days: int):
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = select(News).where(News.publish_time >= cutoff).order_by(News.publish_time.desc()).limit(20)
    r = await db.execute(stmt)
    items = [{"id": n.id, "title": n.title, "publish_time": str(n.publish_time), "views": n.views} for n in r.scalars().all()]
    return json.dumps(items, ensure_ascii=False)

async def get_news_by_author(db, author: str):
    stmt = select(News).where(News.author == author).order_by(News.publish_time.desc()).limit(20)
    r = await db.execute(stmt)
    items = [{"id": n.id, "title": n.title, "publish_time": str(n.publish_time), "views": n.views} for n in r.scalars().all()]
    return json.dumps(items, ensure_ascii=False)

def create_langchain_tools(db):
    """创建绑定数据库会话的 LangChain 工具列表"""
    return [
        Tool(name="get_categories", description="获取所有新闻分类列表", func=lambda: None, coroutine=lambda: get_categories(db)),
        Tool(name="search_news", description="按关键词搜索新闻标题和简介（传keyword）", func=lambda: None, coroutine=lambda kw: search_news(db, keyword=kw)),
        Tool(name="get_news_by_category", description="按分类名称获取新闻列表（传category_name, page可选）", func=lambda: None, coroutine=lambda cn, p=1: get_news_by_category(db, category_name=cn, page=p)),
        Tool(name="get_hot_news", description="获取浏览量最高的N条新闻（传top_n, 默认5）", func=lambda: None, coroutine=lambda n=5: get_hot_news(db, top_n=n)),
        Tool(name="get_hot_news_by_category", description="获取指定分类下浏览量最高的新闻（传category_name, top_n可选）", func=lambda: None, coroutine=lambda cn, n=5: get_hot_news_by_category(db, category_name=cn, top_n=n)),
        Tool(name="get_news_detail", description="获取新闻详情（传news_id）", func=lambda: None, coroutine=lambda nid: get_news_detail(db, news_id=nid)),
        Tool(name="get_news_count_by_category", description="统计分类下新闻数量（传category_id）", func=lambda: None, coroutine=lambda cid: get_news_count_by_category(db, category_id=cid)),
        Tool(name="get_recent_news", description="获取最近N天内的新闻（传days）", func=lambda: None, coroutine=lambda d: get_recent_news(db, days=d)),
        Tool(name="get_news_by_author", description="按作者查新闻（传author）", func=lambda: None, coroutine=lambda a: get_news_by_author(db, author=a)),
    ]

TOOL_MAP = {
    "get_categories": get_categories,
    "search_news": search_news,
    "get_news_by_category": get_news_by_category,
    "get_hot_news": get_hot_news,
    "get_hot_news_by_category": get_hot_news_by_category,
    "get_news_detail": get_news_detail,
    "get_news_count_by_category": get_news_count_by_category,
    "get_recent_news": get_recent_news,
    "get_news_by_author": get_news_by_author,
}
