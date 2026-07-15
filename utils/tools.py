import json
from crud import news
from models.news import News
from sqlalchemy import select
from datetime import datetime, timedelta
from langchain_core.tools import tool


def create_langchain_tools(db):
    @tool
    async def get_categories():
        """获取所有新闻分类列表"""
        cats = await news.get_categories(db)
        return json.dumps([{"id": c.id, "name": c.name} for c in cats], ensure_ascii=False)

    @tool
    async def search_news(keyword: str):
        """按关键词搜索新闻标题和简介（传keyword）"""
        stmt = select(News).where(News.title.like(f"%{keyword}%") | News.description.like(f"%{keyword}%")).limit(20)
        r = await db.execute(stmt)
        items = [{"id": n.id, "title": n.title, "views": n.views} for n in r.scalars().all()]
        return json.dumps(items, ensure_ascii=False)

    @tool
    async def get_news_by_category(category_name: str, page: int = 1):
        """按分类名称获取新闻列表（传category_name, page可选）"""
        cats = await news.get_categories(db)
        for c in cats:
            if c.name == category_name:
                skip = (page - 1) * 10
                items = await news.get_news_list(db, c.id, skip, 10)
                return json.dumps([{"id": n.id, "title": n.title, "views": n.views} for n in items], ensure_ascii=False)
        return json.dumps({"error": f"category {category_name} not found"}, ensure_ascii=False)

    @tool
    async def get_hot_news(top_n: int = 5):
        """获取浏览量最高的N条新闻（传top_n, 默认5）"""
        stmt = select(News).order_by(News.views.desc()).limit(top_n)
        r = await db.execute(stmt)
        items = [{"id": n.id, "title": n.title, "views": n.views} for n in r.scalars().all()]
        return json.dumps(items, ensure_ascii=False)

    @tool
    async def get_hot_news_by_category(category_name: str, top_n: int = 5):
        """获取指定分类下浏览量最高的新闻（传category_name, top_n可选）"""
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

    @tool
    async def get_news_detail(news_id: int):
        """获取新闻详情（传news_id）"""
        n = await news.get_news_detail(db, news_id)
        if not n:
            return json.dumps({"error": "news not found"}, ensure_ascii=False)
        return json.dumps({"id": n.id, "title": n.title, "content": n.content, "views": n.views}, ensure_ascii=False)

    @tool
    async def get_news_count_by_category(category_id: int):
        """统计分类下新闻数量（传category_id）"""
        count = await news.get_news_count(db, category_id)
        return json.dumps({"category_id": category_id, "count": count}, ensure_ascii=False)

    @tool
    async def get_recent_news(days: int):
        """获取最近N天内的新闻（传days）"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = select(News).where(News.publish_time >= cutoff).order_by(News.publish_time.desc()).limit(20)
        r = await db.execute(stmt)
        items = [{"id": n.id, "title": n.title, "publish_time": str(n.publish_time), "views": n.views} for n in r.scalars().all()]
        return json.dumps(items, ensure_ascii=False)

    @tool
    async def get_news_by_author(author: str):
        """按作者查新闻（传author）"""
        stmt = select(News).where(News.author == author).order_by(News.publish_time.desc()).limit(20)
        r = await db.execute(stmt)
        items = [{"id": n.id, "title": n.title, "publish_time": str(n.publish_time), "views": n.views} for n in r.scalars().all()]
        return json.dumps(items, ensure_ascii=False)

    return [
        get_categories, search_news, get_news_by_category, get_hot_news,
        get_hot_news_by_category, get_news_detail, get_news_count_by_category,
        get_recent_news, get_news_by_author,
    ]
