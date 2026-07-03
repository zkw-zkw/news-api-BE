import os
import json
from typing import Any
import logging

logger = logging.getLogger(__name__)

import redis.asyncio as redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))


#创建 Redis 的连接对象
redis_client = redis.Redis(
    host=REDIS_HOST,  # Redis 服务器的主机地址
    port=REDIS_PORT,  # Redis 端口号
    db=REDIS_DB,  # Redis 数据库编号，0~15
    decode_responses=True  # 是否将字节数据解码为字符串
)


#设置和读取（字符串 和 列表或字典）"[{}]"
#读取字符串
async def get_cache(key: str):
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.error(f"获取缓存失败：{e}")
        return None


#读取列表或字典
async def get_json_cache(key: str):
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)  #序列化
        return None
    except Exception as e:
        logger.error(f"获取 JSON 缓存失败：{e}")
        return None


#设置缓存setex(key, expire, value)
async def set_cache(key: str, value: Any, expire: int = 3600):
    try:
        if isinstance(value, (dict, list)):
            #转字符串再存
            value = json.dumps(value, ensure_ascii=False)  #中文正常保存
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        logger.error(f"设置缓存失败：{e}")
        return False
