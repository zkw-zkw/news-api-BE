# 基于 FastAPI 的高并发新闻资讯后端系统

> 一个高性能、生产级的新闻资讯 API 服务，涵盖完整的用户认证、新闻浏览、收藏互动和阅读记录功能。

## 📌 项目简介

本项目是一个高并发新闻聚合平台后端 API 服务，采用 **Python FastAPI** 异步框架开发。核心亮点是**多级缓存防御体系** + **高并发浏览量写入方案**，经 JMeter 压测验证，单机 QPS 达 **380+**，TP99 控制在 **200ms** 以内。

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Python 3.12 + FastAPI |
| ORM | SQLAlchemy 2.0（异步） |
| 数据库 | MySQL 8.0 + aiomysql |
| 缓存 | Redis 7.0 |
| 部署 | Docker + Docker Compose |
| 工具 | Git + Linux + JMeter |

## 🚀 核心功能

- 用户注册 / 登录（JWT 认证）
- 新闻分类浏览（多级分类）
- 新闻列表分页查询（按分类 / 热度 / 时间）
- 新闻详情 + 浏览量实时统计
- 相关新闻推荐
- 新闻收藏 / 取消收藏
- 浏览历史记录

## ⚡ 技术亮点

| 优化项 | 实现方案 | 效果 |
|--------|----------|------|
| 缓存穿透防护 | 空值缓存（Sentinel） | 缓存命中率 95%+ |
| 缓存击穿防护 | SETNX 互斥锁（分布式锁） | 防止热点 key 失效时打垮数据库 |
| 缓存雪崩防护 | 随机过期时间（Jitter） | 避免大量缓存同时失效 |
| 高并发浏览量 | Redis INCR 原子计数器 + 30s 异步批量同步 | 数据库写入压力降低 80%+ |
| 数据库查询优化 | 字段裁剪 + 复合索引 | 响应时间降低 60%+ |
| 优雅退出 | asyncio.Event 信号控制 | 应用关闭前数据不丢失 |
| 请求监控 | 耗时中间件 + 结构化日志 | 便于性能排查 |

## 📁 项目结构
```
头条项目/
├── cache/
│ └── news_cache.py
├── config/
│ ├── cache_conf.py
│ └── db_conf.py
├── core/
│ ├── logger.py
│ └── startup.py
├── crud/
│ ├── favorite.py
│ ├── history.py
│ ├── news.py
│ ├── news_cache.py
│ └── users.py
├── models/
│ ├── favorite.py
│ ├── history.py
│ ├── news.py
│ └── users.py
├── routers/
│ ├── favorite.py
│ ├── history.py
│ ├── news.py
│ └── users.py
├── schemas/
│ ├── base.py
│ ├── favorite.py
│ ├── history.py
│ ├── news.py
│ └── users.py
├── utils/
│ ├── auth.py
│ ├── exception.py
│ ├── exception_handlers.py
│ ├── response.py
│ └── security.py
├── .env
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```


## 🔧 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/zkw-zkw/new-sapi.git
cd new-sapi
```
### 2. 创建虚拟环境并安装依赖
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
```
### 3. 配置环境变量
创建 .env 文件：

```ini
DATABASE_URL=mysql+aiomysql://root:你的密码@localhost:3306/news_app?charset=utf8mb4
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```
### 4. 初始化数据库
```bash
mysql -u root -p -e "CREATE DATABASE news_app CHARACTER SET utf8mb4;"
```
### 5. 启动服务
```bash
uvicorn main:app --reload
访问 http://localhost:8000/docs 查看 Swagger API 文档。
```
## 📊 压测数据

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| QPS | 120 | 380+ |
| 平均响应时间 | 210ms | 75ms |
| 缓存命中率 | 无缓存 | 95%+ |
| 数据库负载 | 100% | ~35% |

> 压测工具：JMeter，50-200 并发阶梯压测

---

## 📄 License

MIT License


#### 3. `.env.example`（新建）

```ini
# 数据库配置
DATABASE_URL=mysql+aiomysql://root:你的密码@localhost:3306/news_app?charset=utf8mb4

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```
### 4. requirements.txt
在项目根目录打开终端，执行：

```bash
pip freeze > requirements.txt
```