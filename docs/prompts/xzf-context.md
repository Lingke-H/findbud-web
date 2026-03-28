# 【xzf 专属】AI 工作启动包

> **使用方式**：每次打开新的 AI 对话，把下方「===复制开始===」到「===复制结束===」之间的全部内容粘贴进去，然后再说你想要什么。

---

===复制开始===

## 项目背景（网页版）

我在开发一款叫 **FindBud（找搭子）** 的网页应用，面向**宁波诺丁汉大学**学生，当前 MVP 聚焦**数学建模比赛搭子**。前端用 **React + Vite**，在浏览器里运行，不需要手机。

**完整业务流程（三个 Phase）：**

**Phase I：用户信息采集**
1. 收集 6 项基础信息：姓名、性别、年级、专业、组队目标、是否长期组队
2. 机动前置问题（1-2 题选择题）：根据组队目标分流，例如"你倾向在数学建模团队担任什么角色？A.建模手 B.论文手 C.编程手 D.无倾向"
3. AI 生成选择题，量化三大维度向量（技能向量、性格动能因子、绝对实力）

**Phase II：匹配算法**
4. 后端通过"平行与正交的效用函数"在 Mock 数据库中找出最优 3 位候选人

**Phase III：展示结果**
5. 固定推荐 **3 位** 最合适的队友并展示

**我负责的部分：前端页面开发（React + Vite 网页版）**
- 基础信息收集页面（6 项）
- 机动前置问题页面（选择题，根据组队目标显示）
- AI 选择题页面（向量量化阶段）
- 匹配结果展示页面（调用后端匹配接口）

---

## 我需要实现的页面

| 页面 | 文件名 | 功能 |
|------|--------|------|
| 基础信息填写页 | `OnboardingPage.tsx` | 收集 6 项基础信息：姓名、性别、年级、专业、组队目标、是否长期组队 |
| 机动前置问题页 | `PreQuestionPage.tsx` | 根据组队目标展示 1-2 道选择题（主观因素收集） |
| AI 向量收集页 | `AIQuestionPage.tsx` | 展示 AI 生成的选择题，用户逐题作答，量化三大维度 |
| 匹配结果页 | `MatchResultPage.tsx` | 展示 3 位推荐队友的卡片，含匹配维度说明和联系方式 |

---

## 数据结构

> **说明**：下面是目前参考的字段定义。**如果你这边的页面需要额外的字段，直接告诉 xyh，由 xyh 加到数据库里**。不要自己再 `frontend/` 以外的地方添加字段。

### 用户基础信息（6 项）
```typescript
interface User {
  id: string;              // UUID
  name: string;            // 姓名
  gender: string;          // 性别
  grade: string;           // 年级，如 "大二"
  major: string;           // 专业
  teamGoal: string;        // 组队目标，如 "数学建模比赛"
  wantLongTerm: boolean;   // 是否想要长期组队
}
```

### 选择题（机动前置 + AI 向量收集）
```typescript
interface ChoiceQuestion {
  questionId: string;
  questionText: string;    // 问题正文
  options: Array<{
    label: string;         // 选项标签，如 "A"
    text: string;          // 选项文字，如 "建模手"
  }>;
  phase: 'pre' | 'ai';    // pre=机动前置问题，ai=AI向量收集
  dimension?: string;      // 对应的向量维度（AI 阶段）
}
```

### 用户向量（AI 阶段量化结果）
```typescript
interface UserVector {
  skillVector: {           // 技能向量（相对实力）
    modeling: number;      // 数学建模实力
    coding: number;        // 编程实现
    writing: number;       // 论文排版
  };
  personalityFactor: {     // 性格动能因子
    leader: number;        // 领导者
    supporter: number;     // 支持者
    executor: number;      // 执行者
  };
  absoluteStrength: {      // 绝对实力
    experience: number;    // 比赛经验
    hasAward: boolean;     // 是否获奖
    ambition: number;      // 夺冠欲望
  };
}
```

### 匹配结果（固定 3 条）
```typescript
interface MatchCandidate {
  candidateUserId: string;
  rank: 1 | 2 | 3;
  matchScore: number;        // 0~1 之间，如 0.87
  summary: string;           // 匹配摘要文字
  dimensionBreakdown: Array<{
    dimension: string;
    score: number;
    comment: string;
  }>;
  nickname: string;
  school: string;
  major: string;
  avatarUrl?: string;
  contactInfo?: string;      // 联系方式，匹配后才展示
}
```

---

## 需要调用的后端接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/competition-types` | GET | 获取所有比赛类型（含标签，用于展示选择页） |
| `/api/v1/users` | POST | 提交用户基础信息 |
| `/api/v1/fixed-questions` | GET | 获取人工预设的固定问题列表 |
| `/api/v1/match-sessions` | POST | 基础信息填完后创建匹配会话 |
| `/api/v1/match-sessions/{sessionId}/answer` | POST | 提交固定问题的回答 |
| `/api/v1/match-sessions/{sessionId}/results` | GET | 获取最终推荐的 3 位队友 |

所有接口返回格式：
```json
{ "code": 200, "message": "success", "data": {} }
```

---

## 编码规范（必须遵守）

- **组件/页面**：`PascalCase`，文件名 `PascalCase.tsx`，放在 `frontend/src/pages/`
- **变量/函数**：`camelCase`，如 `fetchMatchResults()`
- **常量**：`UPPER_SNAKE_CASE`，如 `MAX_BUDDIES = 3`
- **注释**：全部写中文
- **推荐数量**：一律用常量 `MAX_BUDDIES = 3`，不要直接写数字 `3`
- **后端 API 地址**：从环境变量 `import.meta.env.VITE_API_BASE_URL` 读取，不要硬编码 `http://localhost:8000`
- **不要修改** `backend/` 目录下的任何文件

---

## 需求描述模板

```
我需要实现：[页面名称 / 组件]
这个页面要做的事：[具体描述]
用到的数据字段：[从上面数据结构中选]
调用的接口：[从上面接口列表中选]
用户操作流程：[点了什么 → 发生什么 → 跳转到哪]
UI 风格：[简洁/卡片/列表等，可不填]
```

===复制结束===

---

## 示例提示词

**示例 1：比赛类型标签选择页**
```
请帮我实现 frontend/src/pages/CompetitionSelectPage.tsx。
这是一个 React 网页组件，用 fetch 调用 GET /api/v1/competition-types 获取列表。
按 category 字段分组展示带标签的比赛类型（如"技术类"下面有"黑客马拉松""ACM"等）。
用户可以多选，选中的条目高亮显示。
点击"下一步"按钮后，把选中的 competitionTypeId 列表传给下一个页面。
后端地址从 import.meta.env.VITE_API_BASE_URL 读取。样式简洁，所有注释用中文。
```

**示例 2：固定问题页**
```
请帮我实现 frontend/src/pages/FixedQuestionPage.tsx。
这是一个 React 网页组件，进入页面时调用 GET /api/v1/fixed-questions 获取 1-2 个固定问题，按 orderIndex 顺序展示。
每题展示问题文字和一个文本输入框，用户填写回答。
全部填完点击"提交"，依次调用 POST /api/v1/match-sessions/{sessionId}/answer 提交每题答案，成功后跳转到 AI 提问等待页。
后端地址从 import.meta.env.VITE_API_BASE_URL 读取，所有注释用中文。
```

**示例 3：匹配结果展示页**
```
请帮我实现 frontend/src/pages/MatchResultPage.tsx。
这是一个 React 网页组件，进入页面时调用 GET /api/v1/match-sessions/{sessionId}/results 获取推荐结果。
用卡片形式展示 3 位队友，每张卡片显示：头像、昵称、学校专业、matchScore（转为百分比）、summary 文字、联系方式按钮。
使用常量 MAX_BUDDIES = 3 控制渲染数量，不要硬编码 3。
后端地址从 import.meta.env.VITE_API_BASE_URL 读取，所有注释用中文。
```

---

## 前置软件安装（仅首次，装过跳过）

需要安装 **Node.js**：https://nodejs.org → 选 LTS 版本，一路下一步。
安装完**关闭并重新打开 PowerShell** 后，运行 `node --version` 验证是否成功。

---

## 本地环境启动（Windows PowerShell，只需做一次的步骤标注了"仅首次"）

```powershell
# 【仅首次】安装前端依赖（在项目根目录执行）
npm install --prefix frontend

# 【仅首次】复制环境变量文件
Copy-Item frontend\.env.example frontend\.env

# 每次开始写代码前启动前端开发服务器
npm run dev --prefix frontend
```

> 启动成功后访问 http://localhost:5173 就能看到页面，保存代码后浏览器自动刷新。
