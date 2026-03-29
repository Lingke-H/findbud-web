# FindBud — 数据库 Schema 设计文档

> **用途**：将此文件直接喂给 AI（Cursor/Copilot），确保前后端三人操作同一数据模型。
> **数据库**：PostgreSQL 15+
> **字段类型约定**：`UUID` 主键、`TIMESTAMPTZ` 时间戳、`JSONB` 存储结构化动态数据。
> **MVP 场景**：数学建模比赛搭子 / 雅思学习搭子（宁波诺丁汉大学）

---

## 实体关系概览

```
users
  │
  ├──< match_sessions
  │         │
  │         ├──< question_answers   (前置选择题 + AI 向量收集题)
  │         │
  │         └──< match_results >── users (被推荐的候选人)
  │
  ├──── user_profiles       (1:1，数学建模搭子向量画像)
  │
  └──── ielts_user_profiles  (1:1，雅思学习搭子向量画像)
```

> `team_goal` 字段决定用哪张 profile 表：`'数学建模大赛'` → `user_profiles`；`'雅思学习搭子'` → `ielts_user_profiles`。

---

## 表结构详细定义

---

### 1. `users` — 用户基础信息表

> 存储用户填写的 6 项基础信息，是所有关联数据的根节点。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | 用户唯一标识 |
| `name` | `VARCHAR(50)` | NOT NULL | 姓名 |
| `gender` | `VARCHAR(10)` | NOT NULL | 性别，如 "男" / "女" / "其他" |
| `grade` | `VARCHAR(20)` | NOT NULL | 年级，如 "大二"、"研一" |
| `major` | `VARCHAR(100)` | NOT NULL | 专业 |
| `team_goal` | `VARCHAR(100)` | NOT NULL | 组队目标，如 "数学建模比赛" |
| `want_long_term` | `BOOLEAN` | NOT NULL | 是否想要长期组队（固定标签） |
| `gender_preference` | `VARCHAR(10)` | NULL | **固定标签**：对搭子的性别要求，如 "男"/"女"/"任意" |
| `grade_preference` | `VARCHAR(20)` | NULL | **固定标签**：对搭子的年级要求，如 "大二"/"任意" |
| `contact_info` | `VARCHAR(100)` | NULL | 联系方式（微信/QQ），匹配后展示 |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | 账号是否激活 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 注册时间 |

> **固定标签说明**：`gender_preference` / `grade_preference` / `want_long_term` 用于条件筛选（排除不符合要求的候选人），不参与效用函数计算。

```sql
CREATE TABLE users (
    id                 UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name               VARCHAR(50)  NOT NULL,
    gender             VARCHAR(10)  NOT NULL,
    grade              VARCHAR(20)  NOT NULL,
    major              VARCHAR(100) NOT NULL,
    team_goal          VARCHAR(100) NOT NULL,
    want_long_term     BOOLEAN      NOT NULL,
    gender_preference  VARCHAR(10),
    grade_preference   VARCHAR(20),
    contact_info       VARCHAR(100),
    is_active          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

---

### 2. `match_sessions` — 匹配会话表

> 用户每次发起匹配流程就创建一条记录，贯穿选择题填写到推荐结果的完整生命周期。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 会话唯一标识 |
| `user_id` | `UUID` | FK → users.id, NOT NULL | 发起匹配的用户 |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT 'questioning' | 状态：`questioning`（选择题填写中）/ `matching`（算法运行中）/ `completed`（已完成） |
| `question_count` | `SMALLINT` | NOT NULL, DEFAULT 0 | 已完成的题目数 |
| `user_vector` | `JSONB` | NULL | 最终三大向量（AI题完成后写入，供匹配算法使用） |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 会话创建时间 |
| `completed_at` | `TIMESTAMPTZ` | NULL | 匹配完成时间 |

```sql
CREATE TABLE match_sessions (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status         VARCHAR(20) NOT NULL DEFAULT 'questioning'
                       CHECK (status IN ('questioning', 'matching', 'completed')),
    question_count SMALLINT    NOT NULL DEFAULT 0,
    user_vector    JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at   TIMESTAMPTZ
);

CREATE INDEX idx_match_sessions_user_id ON match_sessions(user_id);
```

---

### 3. `question_answers` — 选择题记录表

> 存储每次会话中的所有选择题（前置问题 + AI 向量收集题）及用户的选择。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 记录唯一标识 |
| `session_id` | `UUID` | FK → match_sessions.id, NOT NULL | 所属匹配会话 |
| `phase` | `VARCHAR(10)` | NOT NULL | 阶段：`pre`（机动前置问题）/ `ai`（AI向量收集题） |
| `round_number` | `SMALLINT` | NOT NULL | 题目序号（从 1 开始） |
| `question_text` | `TEXT` | NOT NULL | 题目正文 |
| `options` | `JSONB` | NOT NULL | 选项列表，如 `[{"label":"A","text":"建模手"},...]` |
| `selected_option` | `VARCHAR(5)` | NULL | 用户选择的选项标签，如 `"A"` |
| `dimension` | `VARCHAR(50)` | NULL | AI阶段对应的向量维度，如 `"skill_modeling"` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 题目生成时间 |
| `answered_at` | `TIMESTAMPTZ` | NULL | 用户作答时间 |

```sql
CREATE TABLE question_answers (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID        NOT NULL REFERENCES match_sessions(id) ON DELETE CASCADE,
    phase           VARCHAR(10) NOT NULL CHECK (phase IN ('pre', 'ai')),
    round_number    SMALLINT    NOT NULL,
    question_text   TEXT        NOT NULL,
    options         JSONB       NOT NULL,
    selected_option VARCHAR(5),
    dimension       VARCHAR(50),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    answered_at     TIMESTAMPTZ,
    UNIQUE (session_id, phase, round_number)
);

CREATE INDEX idx_question_answers_session_id ON question_answers(session_id);
```

---

### 4. `user_profiles` — 用户三大向量画像表（1:1 与 users）

> 存储 AI 选择题量化后的三大向量维度，由匹配算法直接读取。AI 题全部完成后写入。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 记录唯一标识 |
| `user_id` | `UUID` | FK → users.id, UNIQUE, NOT NULL | 关联用户（1:1） |
| `skill_modeling` | `NUMERIC(4,2)` | NULL | 技能向量 — 数学建模实力（0~10） |
| `skill_coding` | `NUMERIC(4,2)` | NULL | 技能向量 — 编程实现（0~10） |
| `skill_writing` | `NUMERIC(4,2)` | NULL | 技能向量 — 论文排版（0~10） |
| `personality_leader` | `NUMERIC(4,2)` | NULL | 性格动能 — 领导者倾向（0~10） |
| `personality_supporter` | `NUMERIC(4,2)` | NULL | 性格动能 — 支持者倾向（0~10） |
| `personality_executor` | `NUMERIC(4,2)` | NULL | 性格动能 — 执行者倾向（0~10） |
| `strength_competition_count` | `INTEGER` | NULL, CHECK ≥ 0 | 绝对实力 — 参赛次数 |
| `strength_award_count` | `INTEGER` | NULL, CHECK ≥ 0 | 绝对实力 — 获奖次数 |
| `strength_ambition` | `NUMERIC(4,2)` | NULL | 绝对实力 — 获奖欲望（0~10） |
| `strength_major_relevant` | `NUMERIC(4,2)` | NULL | 绝对实力 — 专业对口程度（0~10） |
| `preferred_role` | `VARCHAR(20)` | NULL | 前置问题结果：建模手 / 论文手 / 编程手 / 无倾向 |
| `raw_answers` | `JSONB` | NULL | 原始选择题答案备份 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 最后更新时间 |

```sql
CREATE TABLE user_profiles (
    id                     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                UUID         NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    skill_modeling         NUMERIC(4,2) CHECK (skill_modeling        BETWEEN 0 AND 10),
    skill_coding           NUMERIC(4,2) CHECK (skill_coding          BETWEEN 0 AND 10),
    skill_writing          NUMERIC(4,2) CHECK (skill_writing         BETWEEN 0 AND 10),
    personality_leader     NUMERIC(4,2) CHECK (personality_leader    BETWEEN 0 AND 10),
    personality_supporter  NUMERIC(4,2) CHECK (personality_supporter BETWEEN 0 AND 10),
    personality_executor   NUMERIC(4,2) CHECK (personality_executor  BETWEEN 0 AND 10),
    strength_competition_count INTEGER CHECK (strength_competition_count >= 0),
    strength_award_count       INTEGER CHECK (strength_award_count >= 0),
    strength_ambition       NUMERIC(4,2) CHECK (strength_ambition BETWEEN 0 AND 10),
    strength_major_relevant NUMERIC(4,2) CHECK (strength_major_relevant  BETWEEN 0 AND 10),
    preferred_role         VARCHAR(20),
    raw_answers            JSONB,
    updated_at             TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

---

### 5. `match_results` — 匹配推荐结果表

> 效用函数算法运行后写入，固定 3 条（rank 1/2/3），是最终呈现给用户的数据。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 记录唯一标识 |
| `session_id` | `UUID` | FK → match_sessions.id, NOT NULL | 所属匹配会话 |
| `recommended_user_id` | `UUID` | FK → users.id, NOT NULL | 被推荐的候选人用户 ID |
| `rank` | `SMALLINT` | NOT NULL, CHECK (rank IN (1,2,3)) | 推荐排名，固定为 1、2、3 |
| `match_score` | `NUMERIC(5,4)` | NOT NULL | 效用函数计算的综合匹配度（0.0000~1.0000） |
| `match_reasons` | `JSONB` | NOT NULL | 三大维度匹配分析，格式见下方说明 |
| `is_viewed` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | 用户是否已查看该推荐 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 推荐生成时间 |

**`match_reasons` JSONB 格式示例：**
```json
{
  "summary": "技能互补（建模手+编程手），性格一致，实力均衡",
  "dimension_breakdown": [
    { "dimension": "技能向量", "score": 0.90, "comment": "技能正交互补，覆盖建模/编程/排版" },
    { "dimension": "性格动能", "score": 0.85, "comment": "领导者倾向相近，协作摩擦小" },
    { "dimension": "绝对实力", "score": 0.80, "comment": "均有比赛经验，夺冠欲望一致" }
  ]
}
```

```sql
CREATE TABLE match_results (
    id                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id           UUID          NOT NULL REFERENCES match_sessions(id) ON DELETE CASCADE,
    recommended_user_id  UUID          NOT NULL REFERENCES users(id),
    rank                 SMALLINT      NOT NULL CHECK (rank IN (1, 2, 3)),
    match_score          NUMERIC(5,4)  NOT NULL CHECK (match_score BETWEEN 0 AND 1),
    match_reasons        JSONB         NOT NULL,
    is_viewed            BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),
    UNIQUE (session_id, rank),
    UNIQUE (session_id, recommended_user_id)
);

CREATE INDEX idx_match_results_session_id ON match_results(session_id);
```

---

## 完整业务流程与表关联时序

```
Phase I：用户信息采集

1. 提交基础信息（OnboardingPage）
   → 写入 users（6 项基础信息）
   → 写入 user_profiles（三大向量字段全为 NULL）
   → 创建 match_sessions（status = 'questioning'）
   → 返回 user_id + session_id 给前端

2. 机动前置选择题（PreQuestionPage，1-2 题）
   → 写入 question_answers（phase = 'pre'）
   → 更新 user_profiles.preferred_role（如 "建模手"）

3. AI 向量收集选择题（AIQuestionPage）
   → AI 生成选择题，写入 question_answers（phase = 'ai'）
   → 用户作答后更新 question_answers.selected_option + answered_at
   → 全部完成后，将选项映射为数值，更新 user_profiles 三大向量字段
   → 生成 match_sessions.user_vector（JSONB 格式）

Phase II：匹配算法

4. 触发匹配（MatchWaitingPage）
   → 更新 match_sessions.status = 'matching'
   → 读取所有 user_profiles（Mock 数据库中的候选人）
   → 通过平行与正交的效用函数计算最优组合
   → 写入 match_results（rank 1/2/3，固定 3 条）
   → 更新 match_sessions.status = 'completed' + completed_at

Phase III：展示结果

5. 展示推荐结果（MatchResultPage）
   → 读取 match_results + users（name, major, grade, contact_info）
   → 展示匹配度、三大维度分析、联系方式
   → 更新 match_results.is_viewed = TRUE
```

---

## 注意事项

1. **`user_profiles` 三大向量**在 AI 题全部完成后一次性写入，不做增量更新。
2. **`match_sessions.user_vector`** 存储三大向量的归一化结果（JSONB），示例：
   ```json
   {
     "skill": {"modeling": 0.8, "coding": 0.5, "writing": 0.3},
     "personality": {"leader": 0.7, "supporter": 0.5, "executor": 0.6},
     "strength": {"experience": 0.9, "has_award": true, "ambition": 0.8}
   }
   ```
3. **推荐结果固定 3 条**，由后端常量 `MAX_RECOMMEND_COUNT = 3` 控制，禁止在代码中硬编码数字 `3`。
4. 所有主键均为 **UUID**，禁止使用自增 ID 作为对外接口标识符。
5. **Mock 数据库**：开发阶段在 `user_profiles` 表中预先插入若干测试用户数据，匹配算法从中取候选人。

---

### 6. `ielts_user_profiles` — 雅思学习搭子向量画像表（1:1 与 users）

> 存储雅思搭子目标用户的分类标签画像，结构平行于 `user_profiles`，互不干扰。
> 仅当 `users.team_goal = '雅思学习搭子'` 的用户填写时创建。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 记录唯一标识 |
| `user_id` | `UUID` | FK → users.id, UNIQUE, NOT NULL | 关联用户（1:1） |
| `skill_listening` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 互斥技能 — 听力（擅长题型组） |
| `skill_reading` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 互斥技能 — 阅读（擅长题型组） |
| `skill_writing` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 互斥技能 — 写作（擅长题型组） |
| `skill_speaking` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 互斥技能 — 口语（擅长题型组） |
| `personality_planner` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 互斥性格 — 计划制定及推动者 |
| `personality_resourcer` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 互斥性格 — 资源获取者 |
| `personality_coordinator` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 互斥性格 — 协调者 |
| `strength_fluency` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 独立标签 — 日常英语口语顺畅程度 |
| `strength_has_ielts_exp` | `BOOLEAN` | NULL | 独立标签 — 是否有雅思考试经历 |
| `strength_willing_training` | `BOOLEAN` | NULL | 独立标签 — 是否愿意一起参加培训班 |
| `strength_weekly_hours` | `INTEGER` | NULL, CHECK ≥ 0 | 独立标签 — 每周可投入共同学习时长（小时） |
| `strength_target_score` | `NUMERIC(4,2)` | NULL, CHECK 0~10 | 独立标签 — 目标成绩期望（0=随意，10=最高分） |
| `preferred_role` | `VARCHAR(20)` | NULL | 前置问题结果：听力/阅读/写作/口语/无倾向 |
| `raw_answers` | `JSONB` | NULL | 原始选择题答案备份 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 最后更新时间 |

```sql
CREATE TABLE ielts_user_profiles (
    id                      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID         NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    skill_listening         NUMERIC(4,2) CHECK (skill_listening         BETWEEN 0 AND 10),
    skill_reading           NUMERIC(4,2) CHECK (skill_reading           BETWEEN 0 AND 10),
    skill_writing           NUMERIC(4,2) CHECK (skill_writing           BETWEEN 0 AND 10),
    skill_speaking          NUMERIC(4,2) CHECK (skill_speaking          BETWEEN 0 AND 10),
    personality_planner     NUMERIC(4,2) CHECK (personality_planner     BETWEEN 0 AND 10),
    personality_resourcer   NUMERIC(4,2) CHECK (personality_resourcer   BETWEEN 0 AND 10),
    personality_coordinator NUMERIC(4,2) CHECK (personality_coordinator BETWEEN 0 AND 10),
    strength_fluency        NUMERIC(4,2) CHECK (strength_fluency        BETWEEN 0 AND 10),
    strength_has_ielts_exp     BOOLEAN,
    strength_willing_training  BOOLEAN,
    strength_weekly_hours      INTEGER CHECK (strength_weekly_hours >= 0),
    strength_target_score   NUMERIC(4,2) CHECK (strength_target_score   BETWEEN 0 AND 10),
    preferred_role          VARCHAR(20),
    raw_answers             JSONB,
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```
