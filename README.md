# FindBud — 找搭子 · 比赛组队 App

> 通过 AI 动态提问 + 智能匹配算法，帮你快速找到最合适的比赛队友。

---

## 项目简介

**FindBud** 是一款面向大学生竞赛场景的智能组队应用。用户填写基础信息和目标比赛类型后，系统后台调用 AI API 为每位用户生成**个性化问题**，深度挖掘用户画像，最终通过匹配算法向每位用户精准推荐 **3 位** 最合适的潜在队友。

### 核心特性

- **AI 个性化提问**：不同用户收到不同问题，AI 根据比赛类型和预设维度动态生成
- **智能匹配推荐**：基于用户画像向量计算，固定推荐 3 个最合适的队友
- **隐私维度保护**：评判维度由系统后台维护，不直接暴露给用户

---

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 前端 | React Native（跨平台移动端） |
| 后端 | Python + FastAPI |
| 数据库 | PostgreSQL |
| AI 接口 | AI API（通过环境变量配置，支持 OpenAI / DeepSeek 等） |
| ORM | SQLAlchemy |
| 数据校验 | Pydantic v2 |

---

## 业务流程

```
用户启动 App
     │
     ▼
┌─────────────────────────────┐
│  Step 1：采集基础信息         │
│  - 姓名、年级、专业、技能标签  │
│  - 目标比赛类型               │
│    （如：数学建模/黑客马拉松）  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Step 2：系统加载评判维度     │
│  （后台预设，用户不可见）      │
│  - 技术能力 / 沟通风格        │
│  - 时间投入度 / 创新思维 等   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Step 3：AI 动态提问（核心模块）               │
│  - 将 [比赛类型 + 评判维度] 注入 AI 上下文    │
│  - AI 为该用户生成 3~5 个个性化问题           │
│  - 每位用户的问题序列各不相同                 │
│  - 用户逐条回答，结果以 JSON 格式存储          │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Step 4：构建用户画像向量     │
│  基础信息 + AI 问答结果       │
│  → 量化为多维度特征向量       │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Step 5：匹配算法运行         │
│  计算用户间相似度 / 互补度    │
│  → 排序候选队友              │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Step 6：推荐结果展示         │
│  固定推荐 3 位潜在队友        │
│  展示：匹配维度说明 + 联系方式 │
└─────────────────────────────┘
```

---

## 项目目录结构

```
FindBud_APP/
├── frontend/                        # React Native 前端
│   ├── src/
│   │   ├── screens/                 # 页面组件
│   │   │   ├── OnboardingScreen.tsx     # 基础信息填写页
│   │   │   ├── QuestionScreen.tsx       # AI 动态提问页
│   │   │   └── MatchResultScreen.tsx    # 推荐结果展示页
│   │   ├── components/              # 可复用组件
│   │   ├── hooks/                   # 自定义 Hooks
│   │   ├── services/                # API 请求封装
│   │   └── constants/               # 全局常量
│   ├── package.json
│   └── app.json
│
├── backend/                         # FastAPI 后端
│   ├── app/
│   │   ├── routers/
│   │   │   ├── user_router.py           # 用户信息接口
│   │   │   ├── ai_question_router.py    # AI 提问接口
│   │   │   └── match_router.py          # 匹配推荐接口
│   │   ├── models/                  # 数据库 ORM 模型
│   │   ├── schemas/                 # Pydantic Schema
│   │   ├── services/
│   │   │   ├── ai_service.py            # AI 动态提问核心逻辑
│   │   │   └── match_service.py         # 匹配算法核心逻辑
│   │   ├── core/
│   │   │   ├── config.py                # 环境变量加载
│   │   │   └── database.py              # 数据库连接
│   │   └── main.py
│   ├── tests/
│   ├── .env.example                 # 环境变量模板（安全，可提交）
│   ├── .env                         # 真实环境变量（已加入 .gitignore）
│   └── requirements.txt
│
├── .cursorrules                     # AI 编程规范
├── .gitignore
└── README.md
```

---

## 本地环境配置

### 前置依赖

- Node.js >= 18
- Python >= 3.11
- PostgreSQL >= 15
- React Native 开发环境（参考 [官方文档](https://reactnative.dev/docs/environment-setup)）

### 1. 克隆仓库

```bash
git clone https://github.com/<your-org>/FindBud_APP.git
cd FindBud_APP
```

### 2. 后端环境配置

```bash
cd backend

# 创建并激活虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（重要！）
cp .env.example .env
```

打开 `backend/.env`，填入你的真实配置：

```dotenv
# ==============================
# FindBud 后端环境变量配置
# ⚠️  此文件已加入 .gitignore，禁止提交到 Git
# ==============================

# 数据库连接
DATABASE_URL=postgresql://用户名:密码@localhost:5432/findbud_db

# AI API 配置（从 AI 平台官网获取，绝对不能硬编码到代码中）
AI_API_KEY=your_ai_api_key_here
AI_API_BASE_URL=https://api.openai.com/v1   # 或 DeepSeek 等其他平台地址
AI_MODEL_NAME=gpt-4o                         # 使用的模型名称

# 应用安全
SECRET_KEY=your_random_secret_key_here       # 用于 JWT 签名，请使用随机字符串
DEBUG=True                                   # 生产环境改为 False
```

> **安全须知**：
> - `.env` 文件已在 `.gitignore` 中，**永远不要**将其提交到 Git。
> - 仓库中只保留 `.env.example`（Key 值为占位符），供团队成员参考格式。
> - AI_API_KEY 如果泄露，请立即在平台控制台撤销并重新生成。

### 3. 初始化数据库

```bash
# 在 PostgreSQL 中创建数据库
createdb findbud_db

# 运行数据库迁移
cd backend
alembic upgrade head
```

### 4. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

访问 API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

### 5. 前端环境配置

```bash
cd frontend
npm install

# 配置前端环境变量（API 地址）
cp .env.example .env
```

`.env` 内容示例：

```dotenv
API_BASE_URL=http://localhost:8000/api/v1
```

### 6. 启动前端

```bash
# iOS
npm run ios

# Android
npm run android
```

---

## 开发规范

请在开始编码前，仔细阅读 [`.cursorrules`](./.cursorrules) 文件，其中定义了：

- 变量命名规范（Python snake_case / TS camelCase）
- 强制中文注释要求
- AI 动态提问模块的编码约束
- API Key 安全规范
- Git 提交信息格式

---

## License

MIT License — 详见 [LICENSE](./LICENSE)
