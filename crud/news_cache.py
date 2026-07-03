from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from cache.news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list, get_cached_news_detail, cache_news_detail, get_cached_related_news, cache_related_news, acquire_lock, release_lock, _is_empty_cache, cache_empty_news_detail, incr_news_views

from models.news import Category, News
from schemas.base import NewsItemBase
from schemas.news import NewsDetailResponse, RelatedNewsResponse


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    #先尝试从缓存中获取数据
    cached_categories = await get_cached_categories()
    if cached_categories:
        return cached_categories

    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()  # ORM

    #写入缓存
    if categories:
        categories = jsonable_encoder(categories)
        await set_cache_categories(categories)

    #返回数据
    return categories


async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    page = skip // limit + 1
    cached_list = await get_cache_news_list(category_id, page, limit)
    if cached_list:
        return [News(**item) for item in cached_list]

    #SETNX 互斥锁：缓存未命中时只允许一个请求查数据库，防止击穿
    lock_name = f"news_list:{category_id}:{page}:{limit}"
    if await acquire_lock(lock_name, ttl=5):
        try:
            #双重检查：获取锁期间其他请求可能已填充缓存
            cached_list = await get_cache_news_list(category_id, page, limit)
            if cached_list:
                return [News(**item) for item in cached_list]

            stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
            result = await db.execute(stmt)
            news_list = result.scalars().all()

            if news_list:
                news_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in news_list]
                await set_cache_news_list(category_id, page, limit, news_data)

            return news_list
        finally:
            await release_lock(lock_name)
    else:
        #未获取到锁，短暂等待后重试缓存
        await asyncio.sleep(0.05)
        cached_list = await get_cache_news_list(category_id, page, limit)
        if cached_list:
            return [News(**item) for item in cached_list]
        #兜底：等待后缓存仍为空，直接查数据库
        stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()


async def get_news_count(db: AsyncSession, category_id: int):
    #查询的是指定分类下的新闻数量
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()  #只能有一个结果，否则报错


async def get_news_detail(db: AsyncSession, news_id: int):
    #先尝试从缓存获取
    cached_news = await get_cached_news_detail(news_id)
    if cached_news is not None:
        #检查空值占位符，避免构造 ORM 对象时报错
        if not await _is_empty_cache(cached_news):
            return News(**cached_news)

    # SETNX 互斥锁：缓存未命中时只允许一个请求查数据库，防止击穿
    if await acquire_lock('detail:' + str(news_id)):
        try:
            #双重检查：获取锁期间其他请求可能已填充缓存
            cached_news = await get_cached_news_detail(news_id)
            if cached_news is not None:
                if not await _is_empty_cache(cached_news):
                    return News(**cached_news)

            stmt = select(News).where(News.id == news_id)
            result = await db.execute(stmt)
            news = result.scalar_one_or_none()

            if news:
                news_dict = NewsDetailResponse.model_validate(news).model_dump(
                    by_alias=False, mode='json', exclude={'related_news'}
                )
                await cache_news_detail(news_id, news_dict)
            else:
                #空值缓存，防止缓存穿透
                await cache_empty_news_detail(news_id)

            return news
        finally:
            await release_lock('detail:' + str(news_id))
    else:
        #未获取到锁，短暂等待后重试缓存
        await asyncio.sleep(0.05)
        cached_news = await get_cached_news_detail(news_id)
        if cached_news is not None:
            if not await _is_empty_cache(cached_news):
                return News(**cached_news)
        #兜底：等待后缓存仍为空，直接查数据库
        stmt = select(News).where(News.id == news_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    cached_related = await get_cached_related_news(news_id, category_id)
    if cached_related:
        #缓存数据是字典列表，直接返回
        return cached_related
    #order_by 排序 → 浏览量和发布时间
    stmt = select(News).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by(
        News.views.desc(),  #默认是升序，desc 表示降序
        News.publish_time.desc()
    ).limit(limit)
    result = await db.execute(stmt)
    related_news = result.scalars().all()

    #转换为字典格式用于缓存和返回（不使用别名，保持数据库字段名）
    if related_news:
        related_data = [
            RelatedNewsResponse.model_validate(news).model_dump(by_alias=False, mode="json")
            for news in related_news
        ]
        await cache_related_news(news_id, category_id, related_data)
        return related_data

    #没有相关新闻，返回空列表
    return []
    # 列表推导式 推导出新闻的核心数据，然后再 return
    # return [{
    #     "id": news_detail.id,
    #     "title": news_detail.title,
    #     "content": news_detail.content,
    #     "image": news_detail.image,
    #     "author": news_detail.author,
    #     "publishTime": news_detail.publish_time,
    #     "categoryId": news_detail.category_id,
    #     "views": news_detail.views
    # } for news_detail in related_news]
