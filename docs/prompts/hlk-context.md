# 【hlk 专属】AI 工作启动包

> **使用方式**：每次打开新的 AI 对话，把下方「===复制开始===」到「===复制结束===」之间的全部内容粘贴进去，然后再说你想要什么。

---

===复制开始===

## 项目背景

我在开发一款叫 **FindBud（找搭子）** 的手机 App，帮助大学生找比赛队友。前端用 React Native，后端用 Python + FastAPI，数据库用 PostgreSQL。

**完整业务流程：**
1. 用户填写基础信息 + 选择目标比赛类型（带标签）
2. 完成 1-2 个人工设计的固定问题
3. 系统 AI 动态提问 3~5 个个性化问题并评分
4. 匹配算法读取用户画像，固定推荐 **3 位** 最合适的队友

**我负责的部分：**
- **目标标签模块**（前端，与 xzf 合作）：比赛类型的标签展示与筛选
- **调用匹配模块**（前端，与 xzf 合作）：触发匹配、展示等待状态、拿到结果后跳转
- **后端开发**（与 xyh 合作）：匹配算法接口、结果查询接口

---

## 前端部分：我负责的组件/模块

### 目标标签模块
- 在比赛类型选择页中，负责标签的筛选和分组展示逻辑
- 按 `category` 字段将比赛类型分组（如"技术类""学科类"），每组下展示对应标签

### 匹配流程触发模块
- 用户完成所有问题后，触发 POST 接口启动匹配算法
- 显示等待动画（loading 状态），轮询或等待后端返回完成信号
- 匹配完成后跳转到结果页

---

## 后端部分：我需要实现的接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `POST /api/v1/match-sessions/{sessionId}/run-match` | POST | 触发匹配算法，生成 Top 3 推荐结果 |
| `GET /api/v1/match-sessions/{sessionId}/results` | GET | 查询已生成的推荐结果（前端轮询用） |

---

## 数据库表结构

> **说明**：下面是目前参考的字段定义。**如果你这边的功能需要额外的字段，直接告诉 xyh，由 xyh 加到数据库里**。不要自己修改数据库相关文件。

### `user_profiles` — 用户能力画像（匹配算法的输入）
```
id UUID, user_id UUID,
tech_skill_score NUMERIC,       -- 技术能力（0~10）
communication_score NUMERIC,    -- 沟通协作（0~10）
time_commitment_score NUMERIC,  -- 时间投入度（0~10）
innovation_score NUMERIC,       -- 创新思维（0~10）
stress_tolerance_score NUMERIC, -- 抗压能力（0~10）
leadership_score NUMERIC,       -- 领导力（0~10）
preferred_role VARCHAR,
extended_scores JSONB
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

核心函数已定义：
```python
# 核心匹配函数，严格返回 Top 3
def find_top_matches(
    current_user: UserVector,
    all_candidates: list[UserVector],
    dimension_weights: dict | None = None
) -> list[MatchCandidate]   # 长度固定为 MAX_RECOMMEND_COUNT（=3）

# 从数据库数据构建向量对象
def build_user_vector_from_profile(user_id, profile_scores,
                                    preferred_competition_types, preferred_role) -> UserVector
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
