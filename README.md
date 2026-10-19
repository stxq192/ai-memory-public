# 公开只读记忆快照

> 私有主库：`ai-memory`（含身份、任务、流水，不公开）
> 本仓库：只放**规则层**，供任何 AI 用 raw 链接直接读取。

## 这是什么

把「怎么跟我协作」这套规则公开出来，让任何 AI（网页版、手机端、别的电脑）不用登录、不用 token，一个 URL 就能加载。

**不含**：真实姓名 / 联系方式 / 在办案件 / 项目数据 / 日常流水。这些只在私有库。

## 文件

```
AGENTS.md              入口：加载顺序与边界
rules/03-taboos.md     禁忌（最高优先级）
rules/01-preferences.md 沟通与输出偏好
rules/02-skills.md     能力与写死口径
rules/04-focus.md      当前关注方向（抽象版，无项目细节）
rules/05-lessons.md    通用经验
```

## 给 AI 的加载指令（复制这段）

```text
先加载我的公开记忆快照，再回答：
https://raw.githubusercontent.com/stxq192/ai-memory-public/main/AGENTS.md
https://raw.githubusercontent.com/stxq192/ai-memory-public/main/rules/03-taboos.md
https://raw.githubusercontent.com/stxq192/ai-memory-public/main/rules/01-preferences.md
https://raw.githubusercontent.com/stxq192/ai-memory-public/main/rules/02-skills.md
https://raw.githubusercontent.com/stxq192/ai-memory-public/main/rules/04-focus.md
https://raw.githubusercontent.com/stxq192/ai-memory-public/main/rules/05-lessons.md

按优先级 禁忌 > 偏好 > 技能 > 关注 > 经验 执行；
读完先给 6 行回执（已加载文件 / 3 条硬约束 / 口径疑问），再回答。
```

## 更新方式

由私有主库人工提炼后推送，**不做自动同步**（防隐私漏出）。每次改动前打 tag：

```bash
git tag -a snap-$(date +%Y%m%d-%H%M) -m "public snapshot"
git push --tags
```

回退：`git revert <提交号>` 或 `git checkout <tag> -- rules/`。
