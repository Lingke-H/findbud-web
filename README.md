# FindBud — 找搭子 · 比赛组队 App

> 面向宁波诺丁汉大学学生，通过 AI 选择题量化用户向量 + 效用函数最大化匹配，帮你快速找到最合适的比赛队友。

---

## 项目简介

**FindBud** 是面向**宁波诺丁汉大学**学生的校园搭子平台（学习搭子、竞赛组队、旅游搭子等）。当前 MVP 聚焦**寻找数学建模比赛搭子**这一核心场景，同时保持代码的最大可复用性。

**核心痛点**：校园内跨专业找队友信息不对称，传统组队方式无法验证能力匹配度和真实性，容易导致团队技能重叠或目标不一致。

### 核心特性

- **向量化用户画像**：通过 AI 选择题量化三大维度（技能向量、性格动能因子、绝对实力）
- **效用函数最大化匹配**：用"平行与正交的效用函数"在 Mock 数据库中计算最优组合
- **固定推荐 3 位**：输出前 3 位最佳候选人，不多不少

---

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 前端 | React + Vite（网页版） |
| 后端 | Python + FastAPI |
| 数据库 | PostgreSQL |
| AI 接口 | AI API（通过环境变量配置，支持 OpenAI / DeepSeek 等） |
| ORM | SQLAlchemy |
| 数据校验 | Pydantic v2 |

---

## 业务流程

```
Phase I：用户信息采集
     │
     ▼
┌──────────────────────────────────────┐
│  Step 1：基础信息收集（6 项）          │
│  姓名 / 性别 / 年级 / 专业            │
│  组队目标（找什么场景的搭子）          │
│  是否想要长期组队                     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Step 2：机动前置问题（1-2 题）        │
│  根据组队目标分流，收集影响核心向量    │
│  的主观因素                          │
│  例（数学建模）：                     │
│  "你倾向在团队担任什么角色？"          │
│  A.建模手 B.论文手 C.编程手 D.无倾向  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│  Step 3：AI 核心计算向量收集（选择题）             │
│  通过 AI 生成选择题量化以下三大维度：              │
│                                                  │
│  技能向量（相对实力）：                           │
│    数学建模实力 / 编程实现 / 论文排版              │
│                                                  │
│  性格动能因子：                                   │
│    领导者 / 支持者 / 执行者                       │
│                                                  │
│  绝对实力：                                       │
│    比赛经验 / 是否获奖 / 夺冠欲望                 │
└──────────────┬───────────────────────────────────┘
               │
               ▼
Phase II：匹配算法
               │
               ▼
┌──────────────────────────────────────┐
│  Step 4：效用函数最大化匹配           │
│  在 Mock 数据库（含其他候选人）中     │
│  通过"平行与正交的效用函数"           │
│  计算最优团队组合                     │
└──────────────┬───────────────────────┘
               │
               ▼
Phase III：输出结果
               │
               ▼
┌──────────────────────────────────────┐
│  Step 5：展示前 3 位最佳候选人        │
│  固定推荐 3 位，展示匹配维度 + 联系方式│
└──────────────────────────────────────┘
```

---

## 项目目录结构

```
FindBud_APP/
├── frontend/                        # React + Vite 网页前端
│   ├── src/
│   │   ├── pages/                   # 页面组件
│   │   │   ├── OnboardingPage.tsx       # 基础信息填写页（6项）
│   │   │   ├── PreQuestionPage.tsx      # 机动前置问题页
│   │   │   ├── AIQuestionPage.tsx       # AI 选择题向量收集页
│   │   │   └── MatchResultPage.tsx      # 推荐结果展示页
│   │   ├── api/                     # 后端接口封装
│   │   └── App.tsx                  # 路由配置
│   ├── package.json
│   └── .env.example
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

### 前置依赖（按人员）

> 所有人均使用 **Windows**，命令统一用 PowerShell 执行。

| 成员 | 需要安装的软件 |
|------|--------------|
| **xyh**（后端 + 数据库） | Python ≥ 3.11、PostgreSQL ≥ 15 |
| **xzf**（前端） | Node.js ≥ 18 |
| **hlk**（前端等待页 + 后端匹配算法） | Python ≥ 3.11、Node.js ≥ 18 |

**下载地址：**
- **Python**：https://www.python.org/downloads/ （安装时勾选 ☑ Add Python to PATH）
- **PostgreSQL**：https://www.postgresql.org/download/windows/ （安装时记住设置的 postgres 用户密码）
- **Node.js**：https://nodejs.org （选 LTS 版本，一路下一步即可）

> ⚠️ 安装完任何软件后，必须**关闭并重新打开 PowerShell**，命令才会生效。

### 1. 克隆仓库

```bash
git clone https://github.com/<your-org>/FindBud_APP.git
cd FindBud_APP
```

### 2. 后端环境配置

**Windows（PowerShell）：**
```powershell
# 创建并激活虚拟环境
python -m venv backend\venv
backend\venv\Scripts\activate

# 安装依赖
pip install -r backend\requirements.txt

# 配置环境变量（重要！）
Copy-Item backend\.env.example backend\.env
```

**macOS / Linux：**
```bash
python -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

> ⚠️ **注意**：所有命令均在项目根目录 `FindBud_APP/` 下执行，不需要先 `cd backend`。

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

**Windows（PowerShell）：**
```powershell
npm install --prefix frontend
Copy-Item frontend\.env.example frontend\.env
```

**macOS / Linux：**
```bash
npm install --prefix frontend
cp frontend/.env.example frontend/.env
```

`.env` 内容示例：

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

### 6. 启动前端

```powershell
npm run dev --prefix frontend
```

访问 [http://localhost:5173](http://localhost:5173) 查看页面。

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
