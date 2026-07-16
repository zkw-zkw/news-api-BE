import asyncio
import logging
from sqlalchemy import select, update
from config.cache_conf import redis_client
from config.db_conf import AsyncSessionLocal
from models.news import News
from cache.news_cache import set_cache_news_list
from schemas.base import NewsItemBase

logger = logging.getLogger(__name__)
_shutdown_event = asyncio.Event()


async def sync_news_views():
    #每30秒同步一次 Redis 浏览量到 MySQL
    while not _shutdown_event.is_set():
        await asyncio.sleep(30)
        try:
            async with AsyncSessionLocal() as session:
                async for key in redis_client.scan_iter("news:views:*"):
                    news_id = int(key.split(":")[-1])
                    delta = int(await redis_client.get(key))
                    if delta:
                        await session.execute(
                            update(News).where(News.id == news_id)
                            .values(views=News.views + delta)
                        )
                        await redis_client.incrby(key, -delta)
                await session.commit()
        except Exception as e:
            logger.error(f"同步浏览量失败: {e}", exc_info=True)


async def warmup_news_cache():
    #预热缓存：预加载 category_id=1 的前3页
    try:
        async with AsyncSessionLocal() as session:
            for page in range(1, 4):
                offset = (page - 1) * 10
                stmt = (
                    select(News)
                    .where(News.category_id == 1)
                    .order_by(News.publish_time.desc())
                    .offset(offset)
                    .limit(10)
                )
                result = await session.execute(stmt)
                news_list = result.scalars().all()
                if news_list:
                    data = [
                        NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False)
                        for item in news_list
                    ]
                    await set_cache_news_list(1, page, 10, data, expire=1800)
                    logger.info(f"[warmup] category_id=1 page {page} cached ({len(news_list)} items)")
    except Exception as e:
        logger.error(f"[warmup] failed: {e}")


async def startup_tasks():
    #启动时执行的任务
    await warmup_news_cache()
    task = asyncio.create_task(sync_news_views())
    logger.info("后台任务已启动 (sync_news_views)")
    return task


async def shutdown_tasks(task):
    #关闭时执行的任务
    logger.info("正在关闭应用，等待后台任务完成...")
    _shutdown_event.set()
    await task
    logger.info("后台任务已停止")