# 【xyh 专属】AI 工作启动包

> **使用方式**：每次打开新的 AI 对话，把下方「===复制开始===」到「===复制结束===」之间的全部内容粘贴进去，然后再说你想要什么。

---

===复制开始===

## 项目背景

我在开发一款叫 **FindBud（找搭子）** 的网页应用后端，面向**宁波诺丁汉大学**学生，当前 MVP 聚焦**数学建模比赛搭子**。后端使用 Python + FastAPI，数据库用 PostgreSQL。

**完整业务流程（三个 Phase）：**

**Phase I：用户信息采集**
1. 收集 6 项基础信息：姓名、性别、年级、专业、组队目标、是否长期组队
2. 机动前置问题（1-2 题）：根据组队目标分流，例如"你倾向在数学建模团队担任什么角色？A.建模手 B.论文手 C.编程手 D.无倾向"
3. AI 生成**选择题**量化三大向量维度：
   - **技能向量**（相对实力）：数学建模实力 / 编程实现 / 论文排版
   - **性格动能因子**：领导者 / 支持者 / 执行者
   - **绝对实力**：比赛经验 / 是否获奖 / 夺冠欲望

**Phase II：匹配算法**
4. 通过"平行与正交的效用函数"在 Mock 数据库中计算帕累托最优组合，输出前 3 位候选人

**Phase III：展示结果**
5. 固定推荐 **3 位** 最合适的队友

**我负责的部分：**
- **AI 提示词设计**：设计选择题题目，控制三大维度的量化方式和权重
- **建立数据库**：根据 xzf 和 hlk 确定的需求，负责建表和初始化
- **后端 API 开发**（与 hlk 合作）

---

## 数据库说明

**表结构由 xzf 和 hlk 根据各自的页面/功能需求来确定，我负责汇总后建表和初始化。**

最终确认的表结构统一记录在 `docs/schema.md`，以那个文件为准。

我自己直接控制的部分只有 `evaluation_dimensions`（评判维度表），因为维度的权重比例是 AI 提示词设计的核心：

```
evaluation_dimensions:
  id UUID, name VARCHAR, description TEXT,
  weight NUMERIC(3,2),   -- 每个维度在匹配中的影响比例，由我控制
  is_active BOOLEAN
```

---

## AI 提示词核心设计（我的重点工作）

### 设计目标
设计 AI 生成的**选择题**，量化用户三大维度的向量值，供匹配算法使用。

### 三大向量维度（必须覆盖）

| 维度 | 子项 | 说明 |
|------|------|------|
| **技能向量**（相对实力） | 数学建模实力、编程实现、论文排版 | 衡量用户在团队中的技能分布 |
| **性格动能因子** | 领导者、支持者、执行者 | 衡量用户在团队中的角色倾向 |
| **绝对实力** | 比赛经验、是否获奖、夺冠欲望 | 衡量用户的综合竞赛背景 |

### 问题形式
- AI 生成的题目必须是**选择题**（ABCD），不是开放问答
- 每道题的选项对应具体的向量值，便于后端直接量化存储
- 参考 `docs/` 下的标签设计文档（详细标签设计思路见"标签(仅数学建模大赛).md"）

### 已有骨架文件
`backend/app/services/ai_service.py` 中已定义：
```python
# 构建系统提示词（我需要完善这个函数）
def build_question_system_prompt(competition_type, dimensions) -> str

# 调用 AI API 生成选择题（API Key 从环境变量 AI_API_KEY 读取）
async def generate_next_question(session_id, competition_type, dimensions,
                                  conversation_history, current_round) -> QuestionItem

# 将用户选择的选项映射为向量值
async def score_user_answer(question_id, dimension_name,
                             question_text, answer_text) -> AnswerScoreResult
```

### AI API 配置（从 .env 读取，禁止硬编码）
```python
api_key = os.getenv("AI_API_KEY")        # AI 平台的 Key
api_base = os.getenv("AI_API_BASE_URL")  # 如 https://api.openai.com/v1
model = os.getenv("AI_MODEL_NAME")       # 如 gpt-4o
```

---

## 编码规范（必须遵守）

- **变量/函数**：`snake_case`，函数名动词开头
- **类**：`PascalCase`
- **常量**：`UPPER_SNAKE_CASE`
- **注释**：全部写中文
- **AI API Key**：只从 `os.getenv()` 读取，**绝对禁止硬编码**
- **推荐数量**：使用常量 `MAX_RECOMMEND_COUNT = 3`，不写魔法数字 `3`
- **不要修改** `frontend/` 目录下任何文件

---

## 需求描述模板

```
我需要实现：[数据库建表 / 提示词函数 / 后端接口]
具体要做的事：[描述]
涉及的数据表：[参考 docs/schema.md]
输入/输出：[接收什么，返回什么]
注意事项：[特殊约束]
```

===复制结束===

---

## 示例提示词

**示例 1：建立数据表**
```
请帮我用 SQLAlchemy ORM 定义数据表的 Model 类，文件放在 backend/app/models/ 目录。
表结构如下：[把 docs/schema.md 里 xzf 和 hlk 最终确认的表结构粘贴到这里]
主键全部用 UUID，时间字段用 TIMESTAMPTZ。
每个 Model 类写中文注释说明用途，所有字段也加中文注释。
```

**示例 2：完善 AI 提示词，控制维度权重**
```
请帮我完善 backend/app/services/ai_service.py 中的 build_question_system_prompt() 函数。
要求：
1. 将 dimensions 列表中每个维度的 weight 字段转换为百分比，注入到提示词中，让 AI 知道每个维度的重要程度
2. 提示词要求 AI 按权重高的维度优先提问
3. 明确告知 AI：生成的问题必须结合具体的比赛类型情境，不同用户的问题不能完全一样
所有注释用中文。
```

**示例 3：初始化评判维度数据**
```
请帮我写一个 Python 脚本 backend/scripts/init_dimensions.py，
向 evaluation_dimensions 表插入以下 6 条初始数据：
技术能力（weight=1.5）、沟通协作（weight=1.2）、时间投入度（weight=1.3）、
创新思维（weight=1.2）、抗压能力（weight=1.0）、领导力（weight=0.8）。
使用 SQLAlchemy，从 .env 读取数据库连接，所有注释用中文。
```
