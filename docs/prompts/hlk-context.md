# 【hlk 专属】AI 工作启动包

> **使用方式**：每次打开新的 AI 对话，把下方「===复制开始===」到「===复制结束===」之间的全部内容粘贴进去，然后再说你想要什么。

---

===复制开始===

## 项目背景

我在开发一款叫 **FindBud（找搭子）** 的网页应用，面向**宁波诺丁汉大学**学生，当前 MVP 聚焦**数学建模比赛搭子**。前端用 React + Vite，后端用 Python + FastAPI，数据库用 PostgreSQL。

**完整业务流程（三个 Phase）：**

**Phase I：用户信息采集**
1. 收集 6 项基础信息：姓名、性别、年级、专业、组队目标、是否长期组队
2. 机动前置问题（1-2 题选择题）：根据组队目标分流
3. AI 生成选择题量化三大向量维度：
   - **技能向量**（相对实力）：数学建模实力 / 编程实现 / 论文排版
   - **性格动能因子**：领导者 / 支持者 / 执行者
   - **绝对实力**：比赛经验 / 是否获奖 / 夺冠欲望

**Phase II：匹配算法（我的核心职责）**
4. 在本地 Mock 数据库（含其他候选人）中，通过**平行与正交的效用函数**计算帕累托最优组合，找出前 3 位最佳候选人

**Phase III：展示结果**
5. 固定推荐 **3 位** 最合适的队友

**我负责的部分：**
- **匹配等待页面**（前端，与 xzf 合作）：触发匹配、显示等待状态、完成后跳转结果页
- **后端匹配算法开发**（与 xyh 合作）：实现效用函数、匹配接口、结果查询接口

---

## 前端部分：我负责的组件/模块

### 匹配等待页面（MatchWaitingPage.tsx）
- 用户完成所有 AI 选择题后，触发 POST 接口启动匹配算法
- 显示加载动画和提示文字"正在为你寻找最佳队友…"
- 每隔 2 秒轮询一次结果接口，匹配完成后跳转到结果页
- 最多等待 30 秒，超时后显示"匹配超时，请重试"

---

## 后端部分：我需要实现的接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `POST /api/v1/match-sessions/{sessionId}/run-match` | POST | 触发匹配算法，生成 Top 3 推荐结果 |
| `GET /api/v1/match-sessions/{sessionId}/results` | GET | 查询已生成的推荐结果（前端轮询用） |

---

## 数据库表结构

> **说明**：下面是目前参考的字段定义。**如果你这边的功能需要额外的字段，直接告诉 xyh，由 xyh 加到数据库里**。不要自己修改数据库相关文件。

### `user_profiles` — 用户向量画像（匹配算法的输入）
```
id UUID, user_id UUID,
-- 技能向量（相对实力）
skill_modeling NUMERIC,         -- 数学建模实力（0~10）
skill_coding NUMERIC,           -- 编程实现（0~10）
skill_writing NUMERIC,          -- 论文排版（0~10）
-- 性格动能因子
personality_leader NUMERIC,     -- 领导者倾向（0~10）
personality_supporter NUMERIC,  -- 支持者倾向（0~10）
personality_executor NUMERIC,   -- 执行者倾向（0~10）
-- 绝对实力
strength_experience NUMERIC,    -- 比赛经验（0~10）
strength_has_award BOOLEAN,     -- 是否获奖
strength_ambition NUMERIC,      -- 夺冠欲望（0~10）
-- 前置问题结果
preferred_role VARCHAR,         -- 如 "建模手"/"论文手"/"编程手"
raw_answers JSONB               -- 原始选择题答案
```

### `match_results` — 推荐结果（写入这里，固定 3 条）
```
id UUID, session_id UUID, recommended_user_id UUID,
rank SMALLINT,             -- 只能是 1、2、3
match_score NUMERIC(5,4),  -- 综合匹配度（0~1）
match_reasons JSONB,       -- 格式见下方
is_viewed BOOLEAN
```

`match_reasons` 的 JSON 格式：
```json
{
  "summary": "技术互补，时间投入度一致",
  "dimension_breakdown": [
    { "dimension": "技术能力", "score": 0.85, "comment": "两人技术栈互补" },
    { "dimension": "沟通协作", "score": 0.90, "comment": "沟通风格高度匹配" }
  ]
}
```

### `match_sessions` — 匹配会话（需要更新 status）
```
id UUID, user_id UUID, status VARCHAR,
-- status 流转：questioning → matching → completed
completed_at TIMESTAMPTZ
```

---

## 已有的匹配算法骨架（在此基础上写，不要推倒重来）

文件路径：`backend/app/services/match_service.py`

### 核心算法思路：平行与正交的效用函数
- **技能向量**：用"正交互补"逻辑——团队成员的技能应互补（建模手+论文手+编程手），而非重叠
- **性格动能因子**：用"平行一致"逻辑——性格倾向相似的人合作摩擦更少
- **绝对实力**：直接加权求和，实力越强越好
- 最终在 Mock 数据库中穷举/优化，找到效用函数值最大的 3 人组合

核心函数已定义：
```python
# 核心匹配函数，通过效用函数最大化，严格返回 Top 3
def find_top_matches(
    current_user: UserVector,
    all_candidates: list[UserVector],
    dimension_weights: dict | None = None
) -> list[MatchCandidate]   # 长度固定为 MAX_RECOMMEND_COUNT（=3）

# 从数据库 user_profiles 记录构建向量对象
def build_user_vector_from_profile(user_id, profile_scores, preferred_role) -> UserVector
```

重要常量：
```python
MAX_RECOMMEND_COUNT: int = 3   # 推荐数量，任何地方都用这个常量，不要写数字 3
```

---

## 编码规范（必须遵守）

**前端部分（React Native）：**
- 组件名 `PascalCase`，变量/函数 `camelCase`
- 注释全部写中文
- 不要修改 `backend/` 目录下任何文件

**后端部分（Python/FastAPI）：**
- 变量/函数 `snake_case`，类 `PascalCase`
- 注释全部写中文
- 推荐数量用常量 `MAX_RECOMMEND_COUNT`，不写数字 `3`

---

## 需求描述模板

```
我需要实现：[前端组件 / 后端接口]
这个功能要做的事：[具体描述]
用到的数据：[字段名]
调用/操作的接口或表：[从上面列表中选]
特殊要求：[没有则不填]
```

===复制结束===

---

## 示例提示词

**示例 1：比赛类型标签分组组件**
```
请帮我实现一个 React Native 组件 CompetitionTagGroup.tsx。
功能：接收一个 CompetitionType[] 数组作为 props，按 category 字段分组展示。
每个分组显示分组标题（如"技术类"），下面横向排列该分组下的比赛名称标签。
用户点击标签可以选中/取消，选中状态高亮。
将当前选中的 id 列表通过 onSelectionChange 回调传出。
所有注释用中文。
```

**示例 2：实现"触发匹配"接口**
```
请帮我实现 POST /api/v1/match-sessions/{session_id}/run-match 接口。
逻辑：
1. 更新 match_sessions.status 为 "matching"
2. 读取当前用户的 user_profiles 记录，用 build_user_vector_from_profile() 构建向量
3. 读取数据库中所有其他用户的 user_profiles（排除当前用户）
4. 调用 find_top_matches() 得到 Top 3
5. 将 3 条结果写入 match_results 表（rank 分别为 1、2、3）
6. 更新 match_sessions.status 为 "completed"，completed_at 填当前时间
推荐数量使用常量 MAX_RECOMMEND_COUNT，不要硬编码 3。所有注释用中文。
```

**示例 3：匹配等待页面**
```
请帮我实现 MatchWaitingScreen.tsx。
进入页面后显示加载动画和提示文字"正在为你寻找最佳队友…"。
每隔 2 秒调用一次 GET /api/v1/match-sessions/{sessionId}/results，
如果返回的 data 不为空（说明匹配完成），立即跳转到 MatchResultScreen。
最多等待 30 秒，超时后显示"匹配超时，请重试"提示。
所有注释用中文。
```

---

## 前置软件安装（仅首次，装过跳过）

hlk 需要安装以下两个软件（Mac）：

- **Python**：Mac 自带 Python 3，终端运行 `python3 --version` 验证，若版本 < 3.11 则去 https://www.python.org/downloads/ 下载
- **Node.js**：https://nodejs.org → 选 LTS 版本，下载 macOS 安装包，双击安装

安装完后在终端验证：
```bash
python3 --version
node --version
```
两个都能输出版本号即为成功。

---

## 本地环境启动（Mac 终端，只需做一次的步骤标注了"仅首次"）

```bash
# 【仅首次】安装后端依赖
pip3 install -r backend/requirements.txt

# 【仅首次】复制环境变量模板，然后用文本编辑器打开 backend/.env 填入数据库地址和 API Key
cp backend/.env.example backend/.env

# 【仅首次】安装前端依赖（如果你也负责前端等待页）
npm install --prefix frontend

# 每次开始写代码前，启动后端服务（在项目根目录执行）
uvicorn app.main:app --reload --app-dir backend
```

> 启动成功后终端会显示 `Uvicorn running on http://127.0.0.1:8000`，保持这个窗口开着再去写代码。
> 写完收工按 `Ctrl+C` 关闭。
