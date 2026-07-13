# 新闻资讯后端系统

> 基于 FastAPI 的新闻资讯 API 服务，支持 AI Agent 智能搜索，多层缓存防护体系。

🎯 在线演示：[http://118.195.129.25/](http://118.195.129.25/)  
📖 API 文档：[http://118.195.129.25:8000/docs](http://118.195.129.25:8000/docs)

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Python 3.12 + FastAPI |
| ORM | SQLAlchemy 2.0（异步） |
| 数据库 | MySQL 8.0 + aiomysql |
| 缓存 | Redis 7.0 |
| AI Agent | LangChain 0.3 + DashScope（通义千问） |
| 部署 | Docker + Docker Compose |

---

## 核心功能

- 🤖 **AI Agent 智能问答** — 自然语言搜索新闻、查询热度排行、按分类浏览
- 用户注册 / 登录（JWT 认证）
- 新闻分类浏览（多级分类）
- 新闻列表分页查询（按分类 / 热度 / 时间）
- 新闻详情 + 浏览实时统计
- 相关新闻推荐
- 新闻收藏 / 取消收藏
- 浏览历史记录

---

## 性能压测

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| QPS | 120 | 380+ |
| 平均响应时间 | 210ms | 75ms |
| 缓存命中率 | 无缓存 | 95%+ |
| 数据库负载 | 100% | ~35% |

> 压测工具：JMeter，10-200 并发阶梯压测

---

## 项目结构

```
news-api-BE/
├── main.py                 # 入口文件
├── requirements.txt        # 依赖
├── Dockerfile              # Docker 构建
├── docker-compose.yml      # Docker 编排
├── .env                    # 环境变量
│
├── routers/                # 路由层
│   ├── ai.py               # AI Agent 接口（POST /api/ai/chat）
│   ├── news.py             # 新闻接口
│   ├── users.py            # 用户接口
│   ├── favorite.py         # 收藏接口
│   └── history.py          # 浏览历史接口
│
├── services/               # 业务逻辑层
│   └── langchain_service.py # LangChain Agent（工具调用 + 流式输出）
│
├── utils/                  # 工具
│   ├── tools.py            # Agent 工具函数（搜索、热度、分类等）
│   ├── auth.py             # JWT 认证
│   ├── exception.py        # 异常定义
│   ├── exception_handlers.py # 异常处理
│   ├── response.py         # 响应封装
│   └── security.py         # 安全工具
│
├── schemas/                # Pydantic 数据模型
│   ├── ai.py               # AI 请求/响应模型
│   ├── base.py             # 基础模型
│   ├── favorite.py         # 收藏模型
│   ├── history.py          # 历史模型
│   ├── news.py             # 新闻模型
│   └── users.py            # 用户模型
│
├── crud/                   # 数据库操作
│   ├── news_cache.py       # 缓存 + 数据库组合操作
│   └── ...
│
├── cache/                  # Redis 缓存
│   └── news_cache.py
│
├── config/                 # 配置
│
├── core/                   # 启动、日志
└── ...
```

---

## 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/zkw-zkw/news-api-BE.git
cd news-api-BE
```

### 2. 配置环境变量

创建 `.env` 文件：

```ini
DATABASE_URL=mysql+aiomysql://root:密码@localhost:3306/news_app?charset=utf8mb4
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
DASHSCOPE_API_KEY=你的通义千问API密钥
```

### 3. 初始化数据库

```bash
mysql -u root -p -e "CREATE DATABASE news_app CHARACTER SET utf8mb4;"
```

### 4. Docker 部署

```bash
docker-compose up -d
```

或本地运行：

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看 Swagger 文档。

---

## AI Agent 使用

发送 POST 请求到 `/api/ai/chat`：

```json
{
  "message": "搜索社会新闻热度前五",
  "stream": false
}
```

响应：

```json
{
  "code": 200,
  "data": {
    "reply": "查询结果：[标题](/news/detail/4) …"
  }
}
```

支持 `stream: true` 启用 SSE 流式输出。

---

## License

MIT
