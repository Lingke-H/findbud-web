# 【xzf 专属】AI 工作启动包

> **使用方式**：每次打开新的 AI 对话，把下方「===复制开始===」到「===复制结束===」之间的全部内容粘贴进去，然后再说你想要什么。

---

===复制开始===

## 项目背景（网页版）

我在开发一款叫 **FindBud（找搭子）** 的网页应用，帮助大学生找比赛队友。前端用 **React + Vite**，在浏览器里运行，不需要手机。

**完整业务流程：**
1. 用户填写基础信息 + 选择目标比赛类型（带标签）
2. 完成 1-2 个人工设计的固定问题
3. 系统 AI 根据比赛类型再动态提问 3~5 个个性化问题
4. 后端运行匹配算法，固定推荐 **3 位** 最合适的队友并展示

**我负责的部分：前端页面开发（React + Vite 网页版）**
- 用户信息收集页面
- 目标比赛类型的标签选择模块
- 人工设计的固定问题页面（1-2题）
- 匹配结果展示页面（调用后端匹配接口）

---

## 我需要实现的页面

| 页面 | 文件名 | 功能 |
|------|--------|------|
| 基础信息填写页 | `OnboardingPage.tsx` | 收集昵称、学校、专业、年级 |
| 比赛类型选择页 | `CompetitionSelectPage.tsx` | 带标签的比赛类型多选，如"数学建模""黑客马拉松" |
| 固定问题页 | `FixedQuestionPage.tsx` | 展示人工预设的 1-2 个固定问题，用户输入回答 |
| 匹配结果页 | `MatchResultPage.tsx` | 展示 3 位推荐队友的卡片，含匹配度和联系方式 |

---

## 数据结构

> **说明**：下面是目前参考的字段定义。**如果你这边的页面需要额外的字段，直接告诉 xyh，由 xyh 加到数据库里**。不要自己再 `frontend/` 以外的地方添加字段。

### 用户基础信息
```typescript
interface User {
  id: string;           // UUID
  nickname: string;     // 昵称
  school: string;       // 学校
  major: string;        // 专业
  grade: string;        // 年级，如 "大二"
  avatarUrl?: string;
  bio?: string;
}
```

### 比赛类型（带标签）
```typescript
interface CompetitionType {
  id: string;
  name: string;         // 如 "数学建模"
  category: string;     // 大类标签，如 "技术类"、"学科类"
}
```

### 固定问题
```typescript
interface FixedQuestion {
  questionId: string;
  questionText: string;   // 问题正文
  orderIndex: number;     // 展示顺序（1 或 2）
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
