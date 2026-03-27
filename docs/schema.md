# FindBud — 数据库 Schema 设计文档

> **用途**：将此文件直接喂给 AI（Cursor/Copilot），确保前后端三人操作同一数据模型。
> **数据库**：PostgreSQL 15+
> **字段类型约定**：`UUID` 主键、`TIMESTAMPTZ` 时间戳、`JSONB` 存储结构化动态数据。

---

## 实体关系概览

```
users
  │
  ├──< user_competition_preferences >── competition_types
  │
  ├──< match_sessions
  │         │
  │         ├──< question_answers
  │         │
  │         └──< match_results >── users (被推荐的队友)
  │
  └──── user_profiles (1:1)

evaluation_dimensions (系统后台维护，独立表)
```

---

## 表结构详细定义

---

### 1. `users` — 用户基础信息表

> 存储用户注册后的基础资料，是所有关联数据的根节点。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK, DEFAULT gen_random_uuid() | 用户唯一标识，对外暴露 |
| `nickname` | `VARCHAR(50)` | NOT NULL | 用户昵称，App 内展示名称 |
| `real_name` | `VARCHAR(50)` | NULL | 真实姓名，仅队友匹配后可见 |
| `school` | `VARCHAR(100)` | NOT NULL | 所在学校 |
| `major` | `VARCHAR(100)` | NOT NULL | 所学专业 |
| `grade` | `VARCHAR(20)` | NOT NULL | 年级，如 "大二"、"研一" |
| `contact_info` | `VARCHAR(100)` | NULL | 联系方式（微信/QQ），匹配后展示 |
| `avatar_url` | `TEXT` | NULL | 头像图片 URL |
| `bio` | `TEXT` | NULL | 个人简介，100 字以内 |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | 账号是否处于激活状态 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 注册时间 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 最后更新时间 |

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nickname        VARCHAR(50)  NOT NULL,
    real_name       VARCHAR(50),
    school          VARCHAR(100) NOT NULL,
    major           VARCHAR(100) NOT NULL,
    grade           VARCHAR(20)  NOT NULL,
    contact_info    VARCHAR(100),
    avatar_url      TEXT,
    bio             TEXT,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

---

### 2. `competition_types` — 比赛类型字典表

> 系统预设的比赛类型，由管理员维护。用户选择目标比赛类型时从此表取值。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 比赛类型唯一标识 |
| `name` | `VARCHAR(100)` | NOT NULL, UNIQUE | 比赛名称，如 "数学建模"、"黑客马拉松" |
| `category` | `VARCHAR(50)` | NOT NULL | 大类，如 "技术类"、"创新创业类"、"学科类" |
| `description` | `TEXT` | NULL | 比赛简介 |
| `typical_team_size` | `SMALLINT` | NOT NULL, DEFAULT 3 | 该比赛典型队伍人数 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 创建时间 |

```sql
CREATE TABLE competition_types (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(100) NOT NULL UNIQUE,
    category            VARCHAR(50)  NOT NULL,
    description         TEXT,
    typical_team_size   SMALLINT     NOT NULL DEFAULT 3,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 预置数据示例
INSERT INTO competition_types (name, category, typical_team_size) VALUES
('数学建模', '学科类', 3),
('黑客马拉松', '技术类', 3),
('大学生创新创业大赛', '创新创业类', 5),
('ACM程序设计', '技术类', 3),
('互联网+', '创新创业类', 5);
```

---

### 3. `user_competition_preferences` — 用户偏好比赛类型（多对多）

> 一个用户可以偏好多种比赛类型，此为关联表。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `user_id` | `UUID` | FK → users.id | 用户 ID |
| `competition_type_id` | `UUID` | FK → competition_types.id | 比赛类型 ID |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 添加时间 |

```sql
CREATE TABLE user_competition_preferences (
    user_id              UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    competition_type_id  UUID        NOT NULL REFERENCES competition_types(id) ON DELETE CASCADE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, competition_type_id)
);
```

---

### 4. `evaluation_dimensions` — 评判维度字典表（系统后台，用户不可见）

> 系统预设的多个评判维度，AI 提问时以此为上下文。用户无法直接查看此表。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 维度唯一标识 |
| `name` | `VARCHAR(100)` | NOT NULL, UNIQUE | 维度名称，如 "技术能力" |
| `description` | `TEXT` | NOT NULL | 维度描述，用于构建 AI 提示词 |
| `applicable_categories` | `TEXT[]` | NULL | 适用的比赛大类，NULL 表示通用 |
| `weight` | `NUMERIC(3,2)` | NOT NULL, DEFAULT 1.00 | 在匹配算法中的权重（0.00~2.00） |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT TRUE | 是否启用 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 创建时间 |

```sql
CREATE TABLE evaluation_dimensions (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    VARCHAR(100)  NOT NULL UNIQUE,
    description             TEXT          NOT NULL,
    applicable_categories   TEXT[],
    weight                  NUMERIC(3,2)  NOT NULL DEFAULT 1.00,
    is_active               BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- 预置数据示例
INSERT INTO evaluation_dimensions (name, description, weight) VALUES
('技术能力', '用户的编程、算法等硬技术水平', 1.50),
('沟通协作', '团队合作中的沟通风格与协调能力', 1.20),
('时间投入度', '愿意为比赛投入的时间和精力', 1.30),
('创新思维', '提出新颖想法和解决问题的创造力', 1.20),
('抗压能力', '面对截止日期和压力时的表现', 1.00),
('领导力', '在团队中承担组织和推动角色的意愿', 0.80);
```

---

### 5. `match_sessions` — 匹配会话表

> 用户每次发起一次匹配流程就创建一条记录，贯穿 AI 提问到推荐结果的完整生命周期。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 会话唯一标识 |
| `user_id` | `UUID` | FK → users.id, NOT NULL | 发起匹配的用户 |
| `competition_type_id` | `UUID` | FK → competition_types.id, NOT NULL | 本次匹配的目标比赛 |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT 'questioning' | 状态：`questioning`（AI提问中）/ `matching`（算法运行中）/ `completed`（已完成）/ `expired`（已过期） |
| `question_count` | `SMALLINT` | NOT NULL, DEFAULT 0 | 已完成的提问轮数 |
| `user_vector` | `JSONB` | NULL | 最终构建的用户画像向量，由基础信息+问答结果生成，供匹配算法使用 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 会话创建时间 |
| `completed_at` | `TIMESTAMPTZ` | NULL | 匹配完成时间 |

```sql
CREATE TABLE match_sessions (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    competition_type_id  UUID        NOT NULL REFERENCES competition_types(id),
    status               VARCHAR(20) NOT NULL DEFAULT 'questioning'
                            CHECK (status IN ('questioning', 'matching', 'completed', 'expired')),
    question_count       SMALLINT    NOT NULL DEFAULT 0,
    user_vector          JSONB,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at         TIMESTAMPTZ
);

-- 加速按用户查询历史会话
CREATE INDEX idx_match_sessions_user_id ON match_sessions(user_id);
```

---

### 6. `question_answers` — AI 问答记录表

> 存储每次会话中 AI 动态生成的问题及用户的回答，是构建用户画像的原始数据。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 记录唯一标识 |
| `session_id` | `UUID` | FK → match_sessions.id, NOT NULL | 所属匹配会话 |
| `dimension_id` | `UUID` | FK → evaluation_dimensions.id, NULL | 该问题对应的评判维度 |
| `round_number` | `SMALLINT` | NOT NULL | 提问轮次（从 1 开始） |
| `question_text` | `TEXT` | NOT NULL | AI 生成的问题原文 |
| `answer_text` | `TEXT` | NULL | 用户的回答原文（未回答时为 NULL） |
| `ai_score` | `NUMERIC(4,2)` | NULL | AI 对该回答在对应维度上的评分（0~10） |
| `ai_score_reasoning` | `TEXT` | NULL | AI 给出评分的理由（供调试和透明度使用） |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 问题生成时间 |
| `answered_at` | `TIMESTAMPTZ` | NULL | 用户回答时间 |

```sql
CREATE TABLE question_answers (
    id                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id           UUID          NOT NULL REFERENCES match_sessions(id) ON DELETE CASCADE,
    dimension_id         UUID          REFERENCES evaluation_dimensions(id),
    round_number         SMALLINT      NOT NULL,
    question_text        TEXT          NOT NULL,
    answer_text          TEXT,
    ai_score             NUMERIC(4,2)  CHECK (ai_score >= 0 AND ai_score <= 10),
    ai_score_reasoning   TEXT,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now(),
    answered_at          TIMESTAMPTZ,
    UNIQUE (session_id, round_number)
);

CREATE INDEX idx_question_answers_session_id ON question_answers(session_id);
```

---

### 7. `user_profiles` — 用户能力画像表（1:1 与 users）

> 汇总用户在各评判维度上的最终得分，由匹配算法直接读取。每次新的匹配会话完成后更新。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 记录唯一标识 |
| `user_id` | `UUID` | FK → users.id, UNIQUE, NOT NULL | 关联用户（1:1） |
| `tech_skill_score` | `NUMERIC(4,2)` | NULL | 技术能力综合得分（0~10） |
| `communication_score` | `NUMERIC(4,2)` | NULL | 沟通协作得分（0~10） |
| `time_commitment_score` | `NUMERIC(4,2)` | NULL | 时间投入度得分（0~10） |
| `innovation_score` | `NUMERIC(4,2)` | NULL | 创新思维得分（0~10） |
| `stress_tolerance_score` | `NUMERIC(4,2)` | NULL | 抗压能力得分（0~10） |
| `leadership_score` | `NUMERIC(4,2)` | NULL | 领导力得分（0~10） |
| `preferred_role` | `VARCHAR(50)` | NULL | 倾向角色，如 "技术开发"、"项目管理"、"设计" |
| `extended_scores` | `JSONB` | NULL | 扩展维度得分，存储未在固定列中定义的动态维度 |
| `profile_version` | `INTEGER` | NOT NULL, DEFAULT 1 | 画像版本号，每次更新递增 |
| `last_session_id` | `UUID` | FK → match_sessions.id, NULL | 更新本画像的最近一次会话 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 最后更新时间 |

```sql
CREATE TABLE user_profiles (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID          NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    tech_skill_score        NUMERIC(4,2)  CHECK (tech_skill_score    BETWEEN 0 AND 10),
    communication_score     NUMERIC(4,2)  CHECK (communication_score BETWEEN 0 AND 10),
    time_commitment_score   NUMERIC(4,2)  CHECK (time_commitment_score BETWEEN 0 AND 10),
    innovation_score        NUMERIC(4,2)  CHECK (innovation_score    BETWEEN 0 AND 10),
    stress_tolerance_score  NUMERIC(4,2)  CHECK (stress_tolerance_score BETWEEN 0 AND 10),
    leadership_score        NUMERIC(4,2)  CHECK (leadership_score    BETWEEN 0 AND 10),
    preferred_role          VARCHAR(50),
    extended_scores         JSONB,
    profile_version         INTEGER       NOT NULL DEFAULT 1,
    last_session_id         UUID          REFERENCES match_sessions(id),
    updated_at              TIMESTAMPTZ   NOT NULL DEFAULT now()
);
```

---

### 8. `match_results` — 匹配推荐结果表

> 存储算法为用户推荐的 3 位潜在队友，是最终呈现给用户的数据。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | `UUID` | PK | 记录唯一标识 |
| `session_id` | `UUID` | FK → match_sessions.id, NOT NULL | 所属匹配会话 |
| `recommended_user_id` | `UUID` | FK → users.id, NOT NULL | 被推荐的潜在队友用户 ID |
| `rank` | `SMALLINT` | NOT NULL, CHECK (rank IN (1,2,3)) | 推荐排名，固定为 1、2、3 |
| `match_score` | `NUMERIC(5,4)` | NOT NULL | 匹配算法计算的综合匹配度（0.0000~1.0000） |
| `match_reasons` | `JSONB` | NOT NULL | 各维度匹配分析，格式见下方说明 |
| `is_viewed` | `BOOLEAN` | NOT NULL, DEFAULT FALSE | 用户是否已查看该推荐 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | 推荐生成时间 |

**`match_reasons` JSONB 格式示例：**
```json
{
  "summary": "技术互补，沟通风格契合，时间投入度高度一致",
  "dimension_breakdown": [
    { "dimension": "技术能力",   "score": 0.85, "comment": "两人技术栈互补" },
    { "dimension": "沟通协作",   "score": 0.92, "comment": "沟通风格高度匹配" },
    { "dimension": "时间投入度", "score": 0.88, "comment": "均能全力投入备赛" }
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
1. 用户注册
   → 写入 users
   → 写入 user_profiles（得分字段暂为 NULL）
   → 写入 user_competition_preferences

2. 用户发起匹配
   → 创建 match_sessions（status = 'questioning'）

3. AI 动态提问（循环 3~5 轮）
   → 读取 competition_types.name + evaluation_dimensions（构建 AI 提示词）
   → 每轮写入 question_answers.question_text
   → 用户回答后更新 question_answers.answer_text + answered_at
   → AI 评分后更新 question_answers.ai_score + ai_score_reasoning

4. 提问结束，构建用户画像
   → 汇总 question_answers.ai_score → 更新 user_profiles 各得分字段
   → 生成 match_sessions.user_vector（JSONB 向量）
   → 更新 match_sessions.status = 'matching'

5. 运行匹配算法
   → 读取所有 user_profiles（同比赛类型的候选用户）
   → 计算相似度/互补度 → 取 Top 3
   → 写入 match_results（rank 1/2/3）
   → 更新 match_sessions.status = 'completed' + completed_at

6. 展示结果
   → 读取 match_results + users（nickname, school, major, avatar_url）
   → 展示匹配度、维度分析、联系方式入口
   → 更新 match_results.is_viewed = TRUE
```

---

## 注意事项

1. **`user_profiles` 得分不随每次会话重置**，而是加权平均更新，保留历史积累。
2. **`evaluation_dimensions` 表由后端管理员接口维护**，前端无权读写。
3. **`match_sessions.user_vector`** 存储归一化后的浮点数组（JSONB 格式），示例：
   ```json
   { "tech_skill": 0.82, "communication": 0.75, "time_commitment": 0.90, "innovation": 0.65 }
   ```
4. **推荐结果固定 3 条**，由后端常量 `MAX_RECOMMEND_COUNT = 3` 控制，禁止在代码中硬编码数字 `3`。
5. 所有主键均为 **UUID**，禁止使用自增 ID 作为对外接口的标识符。
