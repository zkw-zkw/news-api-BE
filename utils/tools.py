from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from crud import news
from models.news import Category, News
from datetime import datetime, timedelta

TOOL_DEFS = [
    {"type": "function", "function": {
        "name": "get_categories",
        "description": "获取所有新闻分类列表",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "search_news",
        "description": "按关键词搜索新闻标题和简介",
        "parameters": {"type": "object", "properties": {
            "keyword": {"type": "string", "description": "搜索关键词"}
        }, "required": ["keyword"]}
    }},
    {"type": "function", "function": {
        "name": "get_news_by_category",
        "description": "按分类名称获取新闻列表",
        "parameters": {"type": "object", "properties": {
            "category_name": {"type": "string", "description": "分类名称，如 头条、科技、体育、财经"},
            "page": {"type": "integer", "description": "页码，从1开始"}
        }, "required": ["category_name"]}
    }},
    {"type": "function", "function": {
        "name": "get_hot_news",
        "description": "获取浏览量最高的新闻",
        "parameters": {"type": "object", "properties": {
            "top_n": {"type": "integer", "description": "返回条数"}
        }, "required": ["top_n"]}
    }},
    {"type": "function", "function": {
        "name": "get_hot_news_by_category",
        "description": "获取指定分类下浏览量最高的新闻",
        "parameters": {"type": "object", "properties": {
            "category_name": {"type": "string", "description": "分类名称，如 头条、社会、科技、体育、财经、国际、娱乐、国内"},
            "top_n": {"type": "integer", "description": "返回条数"}
        }, "required": ["category_name"]}
    }},
    {"type": "function", "function": {
        "name": "get_news_detail",
        "description": "获取新闻详情",
        "parameters": {"type": "object", "properties": {
            "news_id": {"type": "integer", "description": "新闻ID"}
        }, "required": ["news_id"]}
    }},
    {"type": "function", "function": {
        "name": "get_news_count_by_category",
        "description": "统计指定分类下的新闻数量",
        "parameters": {"type": "object", "properties": {
            "category_id": {"type": "integer", "description": "分类ID"}
        }, "required": ["category_id"]}
    }},
    {"type": "function", "function": {
        "name": "get_recent_news",
        "description": "获取最近N天内的新闻",
        "parameters": {"type": "object", "properties": {
            "days": {"type": "integer", "description": "天数"}
        }, "required": ["days"]}
    }},
    {"type": "function", "function": {
        "name": "get_news_by_author",
        "description": "按作者名称查询新闻",
        "parameters": {"type": "object", "properties": {
            "author": {"type": "string", "description": "作者名称"}
        }, "required": ["author"]}
    }},
]

# ── 使用 crud/news.py 已有函数的工具 ──

async def get_categories(db: AsyncSession):
    cats = await news.get_categories(db)
    return [{"id": c.id, "name": c.name, "sort_order": c.sort_order} for c in cats]

async def get_news_by_category(db: AsyncSession, category_name: str, page: int = 1):
    cats = await news.get_categories(db)
    for c in cats:
        if c.name == category_name:
            skip = (page - 1) * 10
            items = await news.get_news_list(db, c.id, skip, 10)
            return [{"id": n.id, "title": n.title, "description": n.description, "views": n.views} for n in items]
    return []

async def get_news_detail(db: AsyncSession, news_id: int):
    n = await news.get_news_detail(db, news_id)
    if not n:
        return {"error": "新闻不存在"}
    return {"id": n.id, "title": n.title, "content": n.content, "author": n.author, "views": n.views, "publish_time": str(n.publish_time)}

async def get_news_count_by_category(db: AsyncSession, category_id: int):
    count = await news.get_news_count(db, category_id)
    return {"category_id": category_id, "count": count}

# ── 需要直接写查询的工具 ──

async def search_news(db: AsyncSession, keyword: str):
    stmt = select(News).where(
        News.title.like(f"%{keyword}%") |
        News.description.like(f"%{keyword}%")
    ).limit(20)
    r = await db.execute(stmt)
    return [{"id": n.id, "title": n.title, "description": n.description, "views": n.views} for n in r.scalars().all()]

async def get_hot_news(db: AsyncSession, top_n: int):
    stmt = select(News).order_by(News.views.desc()).limit(top_n)
    r = await db.execute(stmt)
    return [{"id": n.id, "title": n.title, "views": n.views} for n in r.scalars().all()]

async def get_hot_news_by_category(db: AsyncSession, category_name: str, top_n: int = 5):
    cats = await news.get_categories(db)
    cat_id = None
    for c in cats:
        if c.name == category_name:
            cat_id = c.id
            break
    if not cat_id:
        return {"error": f"分类「{category_name}」不存在"}
    stmt = select(News).where(News.category_id == cat_id).order_by(News.views.desc()).limit(top_n)
    r = await db.execute(stmt)
    return [{"id": n.id, "title": n.title, "views": n.views, "author": n.author, "publish_time": str(n.publish_time)} for n in r.scalars().all()]

async def get_recent_news(db: AsyncSession, days: int):
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = select(News).where(News.publish_time >= cutoff).order_by(News.publish_time.desc()).limit(20)
    r = await db.execute(stmt)
    return [{"id": n.id, "title": n.title, "publish_time": str(n.publish_time), "views": n.views} for n in r.scalars().all()]

async def get_news_by_author(db: AsyncSession, author: str):
    stmt = select(News).where(News.author == author).order_by(News.publish_time.desc()).limit(20)
    r = await db.execute(stmt)
    return [{"id": n.id, "title": n.title, "publish_time": str(n.publish_time), "views": n.views} for n in r.scalars().all()]

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
