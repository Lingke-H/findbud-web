# FindBud — 团队协作指南

> 适用场景：3 人 AI 辅助协作开发，规范分支管理与代码合并流程。

---

## 一、分支策略

### 长期分支

| 分支名 | 用途 | 保护规则 |
|--------|------|---------|
| `main` | 唯一稳定分支，始终保持可运行状态 | 禁止直接 push，只接受 PR 合并 |

### 功能分支命名规则

格式：`<类型>/<模块>-<简短描述>`

| 类型前缀 | 适用场景 | 示例 |
|----------|---------|------|
| `feat` | 新功能开发 | `feat/ai-dynamic-questions` |
| `fix` | Bug 修复 | `fix/match-score-overflow` |
| `refactor` | 重构 | `refactor/user-profile-vector` |
| `docs` | 文档更新 | `docs/update-schema` |
| `test` | 测试相关 | `test/ai-service-unit` |

### 个人开发分支

每人建立并维护自己的开发分支，完成后直接向 `main` 提 PR：

```
main
 ├── <你的分支名>     # 个人开发分支，自行命名
 ├── <队友A的分支名>
 └── <队友B的分支名>
```

> 只在自己的分支上开发，不操作他人分支。合并前完成下方 PR 自我检查清单。

---

## 二、日常开发流程

```
1. 从 main 拉取最新代码（保持分支与主线同步）
   git checkout main && git pull origin main

2. 切换到自己的个人分支（首次使用 -b 创建）
   git checkout -b your-branch-name

3. 开发 → 提交（遵循 Commit 规范）
   git add .
   git commit -m "feat(ai-service): 实现动态问题生成接口"

4. 推送到远端
   git push origin your-branch-name

5. 在 GitHub 上向 main 发起 Pull Request
   → 填写 PR 描述（参考下方模板）
   → 完成自我检查清单后，请另一人 Review

6. Review 通过 → Squash and Merge 到 main

7. 合并完成后，本地同步 main 最新代码，再继续下一个功能开发
   git checkout main && git pull origin main
```

---

## 三、Commit 提交规范

格式：`<type>(<scope>): <中文描述>`

```
feat(ai-service): 实现基于比赛类型的动态问题生成
fix(match-algorithm): 修复候选人不足3人时的数组越界问题
refactor(user-profile): 将向量构建逻辑抽离为独立函数
docs(schema): 补充 match_results 表的字段说明
test(ai-service): 添加 generate_next_question 的单元测试
```

---

## 四、PR 自我检查清单

发起 Pull Request **前**，请逐项确认：

### 🔐 安全检查（必须通过，否则不得提交）

- [ ] 代码中没有任何硬编码的 API Key、密码、Token
- [ ] 没有将 `.env` 文件加入暂存区（`git status` 确认）
- [ ] 没有将含有真实密钥的截图或日志文件提交

### 📐 规范检查

- [ ] 所有变量/函数命名符合 `.cursorrules` 中的命名规范（Python `snake_case` / TS `camelCase`）
- [ ] 新增函数均有中文 docstring，说明功能、参数、返回值
- [ ] 复杂业务逻辑有逐步中文注释，无裸逻辑块

### 🧠 业务逻辑检查

- [ ] 涉及 AI 提问模块的代码：确认问题是动态生成的，没有硬编码固定问题列表
- [ ] 涉及推荐结果的代码：推荐数量使用常量 `MAX_RECOMMEND_COUNT`，不出现魔法数字 `3`
- [ ] 数据库操作使用 ORM 参数化查询，无拼接 SQL

### ✅ 功能检查

- [ ] 本地运行通过，主流程可正常跑通
- [ ] 没有引入新的 `print` 调试语句残留在代码中
- [ ] 与 `docs/schema.md` 中的数据模型保持一致，没有自行修改字段名或类型

### 📝 PR 描述模板

```
## 本次改动内容
<!-- 简述做了什么，1~3 句话 -->

## 关联模块
<!-- 前端 / AI提问服务 / 匹配算法 / 数据库 -->

## 测试方式
<!-- 如何验证这个改动是正确的 -->

## 注意事项（给 Reviewer）
<!-- 需要 Reviewer 重点关注的地方，没有则填"无" -->
```

---

## 五、冲突解决原则

1. **`docs/schema.md` 发生冲突**：三人同步对齐后，由最后修改方手动合并，确保字段定义一致。
2. **`backend/app/services/` 发生冲突**：`ai_service.py` 和 `match_service.py` 分属不同负责人，正常情况不应产生冲突；若有，以最新业务讨论结果为准。
3. **禁止用 `--force push` 覆盖 `main` 分支**。
4. **合并前先同步**：提 PR 前先将 `main` 的最新提交 merge 或 rebase 到自己分支，减少冲突概率。

---

## 六、紧急修复流程

若 `main` 出现严重 Bug 需紧急修复：

```
git checkout main && git pull origin main
git checkout -b fix/critical-issue-name
# 修复 → 完成 PR 自我检查清单 → 直接向 main 提 PR
```
