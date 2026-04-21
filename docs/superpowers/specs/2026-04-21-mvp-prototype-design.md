# Claude SEO SaaS 集成 — MVP 原型设计文档

| 字段 | 值 |
|---|---|
| 创建日期 | 2026-04-21 |
| 文档状态 | Draft（待 review） |
| 阶段 | MVP 原型（验证技术可执行性） |
| 预计工作量 | 1–2 周 |
| 主要决策者 | 项目所有者（外贸建站 + SEO + GEO 业务方） |

---

## 1. 背景与动机

### 1.1 项目所有者业务

- **业务**：外贸建站 + SEO + GEO 服务，面向想做海外市场的中国企业
- **现状**：已上线产品网站，部署在 Cloudflare 上
- **诉求**：在已上线网站上集成一个 SEO 工具，作为引流入口或付费功能（用户提交 URL → 拿到分析报告 → 转化为线索/客户）

### 1.2 为什么用 Claude SEO

Claude SEO 是一个开源的、覆盖 17+ 子能力的 SEO 分析工具集（技术 SEO、E-E-A-T、Schema、GEO、本地 SEO 等）。能直接复用其能力比从零造轮子省 6–12 个月。

### 1.3 集成的根本难点

Claude SEO 是 **Claude Code 插件格式**，不是普通 Python 库——它的"智能"在 markdown SKILL.md 文件里，需要由 Claude 模型驱动才能工作。直接 import 不可用。所以"集成"必然涉及：

1. 找到能"代码驱动 Claude SEO"的运行时（→ Claude Agent SDK）
2. 套一层 HTTP 接口让外部系统调用（→ FastAPI 包装）
3. 解决多租户隔离（→ 每请求独立工作目录 + 环境变量注入）
4. 解决跨平台部署（→ Docker 容器 + Cloudflare Containers）
5. 解决成本问题（→ 翻译代理 + DeepSeek 替代 Claude）

---

## 2. MVP 原型的明确目标

**MVP 只回答 3 个二选一问题**——任何一个答 NO 即立刻停止主方案，启用备选：

| # | 问题 | YES 的判据 |
|---|---|---|
| 1 | "HTTP 请求 → 容器里的 Claude SEO → 返回 SEO 报告"链路能跑通吗？ | 本地 `docker run` + `curl POST` 真实 URL，拿到非空、有意义的 SEO 报告（不是 hello world、不是错误信息） |
| 2 | 同样的镜像在 Cloudflare Containers 上能跑通吗？ | 镜像推到 CF，外网 `curl POST`，拿到同等质量报告 |
| 3 | 用 DeepSeek（不是 Claude）跑，质量和成本可接受吗？ | 单次响应 ≤ 3 分钟、单次 token 成本 ≤ 5 元人民币、报告质量主观判断"够用" |

**MVP 不证明的**：产品能不能赚钱、UI 是否好用、完整 audit 流程是否健壮、多租户在百级并发下是否稳定。这些是 Phase 2 及以后的事。

---

## 3. 范围

### 3.1 In Scope（这版必做）

- [x] 一个 Docker 镜像，包含：
  - Node.js（运行 Claude Code CLI 所需）
  - Claude Code CLI
  - claude-agent-sdk Python 包
  - Claude SEO 项目（git submodule 形式，**锁定到 v1.7.2 tag**）
  - 翻译代理（one-api 或 LiteLLM）
  - FastAPI + uvicorn
  - Python 依赖（requirements.txt）
- [x] 一个 FastAPI HTTP 接口：`POST /v1/audit`
  - 入参：`{"url": "https://example.com"}`
  - 出参：`{"status": "ok", "report": "# SEO 分析\n..."}` 或 `{"status": "error", "error": "..."}`
- [x] 同步阻塞模式（接口收到请求后等到分析完成才返回，1–3 分钟）
- [x] 每请求独立工作目录：`/workspace/{job_id}/`，结束后清理
- [x] 模型层：DeepSeek V3（通过翻译代理调用）
- [x] 调用的 Claude SEO 命令：**只做 `/seo page`**
- [x] 部署目标：本地 Docker → Cloudflare Containers
- [x] 实测报告（Markdown）：实际响应时间、Token 成本、遇到的坑、Go/No-Go 结论

### 3.2 Out of Scope（这版明确不做，Phase 2+）

- ❌ 前端 UI（用 curl / Postman 测）
- ❌ 用户登录、注册、鉴权
- ❌ 付费 / 订阅 / 配额
- ❌ 数据库（D1 / R2 / KV）
- ❌ 多租户隔离（单请求工作目录已足够，不做完整租户体系）
- ❌ 异步队列、Webhook 回调、邮件通知
- ❌ PDF 报告生成
- ❌ 其他 Claude SEO 命令（`audit`、`technical`、`schema`、`geo` 等全推 Phase 2）
- ❌ DataForSEO / Firecrawl / Banana 扩展
- ❌ 接入用户现有 Next.js 网站
- ❌ 监控、日志聚合、告警
- ❌ CI/CD 自动化部署
- ❌ Phase 1 不上 Claude Haiku 做"架构验证基线"（用户拍板跳过）

---

## 4. 架构

### 4.1 组件总览

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Container                            │
│                                                              │
│  ┌────────────────┐                                          │
│  │  FastAPI       │  ← POST /v1/audit  (来自外部 curl)        │
│  │  (uvicorn)     │                                          │
│  └────────┬───────┘                                          │
│           │ ① 创建 /workspace/{job_id}/                       │
│           │    ② 设置环境变量: ANTHROPIC_BASE_URL=本地代理       │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  claude-agent-sdk (Python)                             │  │
│  │   ↓ 子进程启动                                          │  │
│  │  Claude Code CLI                                       │  │
│  │   ↓ 加载 .claude/skills/seo/                           │  │
│  │   ↓ 执行 /seo page <url>                               │  │
│  └────────┬───────────────────────────────────────────────┘  │
│           │ ③ 模型 API 调用（被 ANTHROPIC_BASE_URL 重定向）       │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  翻译代理 (one-api / LiteLLM, 本地 :8080)               │  │
│  │   - 把 Claude API 格式翻译成 OpenAI 格式                  │  │
│  └────────┬───────────────────────────────────────────────┘  │
│           │ ④ HTTPS 出网                                      │
└───────────┼──────────────────────────────────────────────────┘
            ▼
   ┌──────────────────┐
   │ DeepSeek API     │
   │ (api.deepseek.   │
   │  com)            │
   └──────────────────┘
```

### 4.2 关键决策与原因

| 决策 | 选择 | 原因 |
|---|---|---|
| 运行时 | Cloudflare Containers | 用户已用 CF；2026/02 扩容 15 倍后资源充足；Docker 镜像可移植到 Fly.io 等备选 |
| 调用方式 | Claude Agent SDK + Claude Code CLI | 唯一支持原生加载 Claude SEO Skills 的运行时；不改 Claude SEO 源码 |
| Claude SEO 引入方式 | git submodule | 升级时 `git submodule update --remote` 即可；wrapper 仓库独立；满足用户"一键升级"诉求 |
| 模型 | DeepSeek V3 | 用户拍板；成本是 Claude Sonnet 的 1/50；国内付款方便 |
| 模型对接方式 | 翻译代理（ANTHROPIC_BASE_URL → 本地 one-api/LiteLLM → DeepSeek） | Claude Code 只能说 Claude API 协议；DeepSeek 说 OpenAI 协议；代理在中间翻译 |
| HTTP 框架 | FastAPI | Python 主流；异步友好；OpenAPI 自动生成（未来对接前端方便） |
| 接口模式 | 同步阻塞 | MVP 简化；不引入队列复杂度；超时设 5 分钟 |
| 工作目录策略 | `/workspace/{job_id}/` 每请求新建 | 简单、隔离干净；不依赖 HOME 改写技巧 |

### 4.3 容器里的目录布局

```
/app/
  ├── wrapper/                    # FastAPI wrapper 代码（独立仓库）
  │   ├── main.py                 # POST /v1/audit
  │   ├── runner.py               # claude-agent-sdk 调用封装
  │   └── requirements.txt
  │
  ├── claude-seo/                 # git submodule, 锁定到 v1.7.2
  │   ├── skills/
  │   ├── agents/
  │   ├── scripts/
  │   └── requirements.txt
  │
  ├── proxy/                      # 翻译代理
  │   └── litellm_config.yaml     # 或 one-api 的配置
  │
  └── /workspace/                 # 运行时按 job_id 创建子目录
      └── {job_id}/
          ├── .claude/
          │   ├── skills/         # 优先 symlink 自 /app/claude-seo/skills/（Day 3 实测；symlink 不行则 copy）
          │   └── agents/         # 优先 symlink 自 /app/claude-seo/agents/（同上）
          └── output/             # Claude SEO 写报告的地方
```

### 4.4 一次请求的生命周期

1. **接收**：FastAPI 收到 `POST /v1/audit {"url": "https://example.com"}`
2. **校验**：检查 URL 合法（HTTPS、非内网、能解析）。**复用 `claude-seo/scripts/google_auth.py` 的 `validate_url()`**（CLAUDE.md 强制要求的 SSRF 防护，避免重复造轮子）
3. **建工作目录**：`mkdir -p /workspace/{job_id}` ；symlink Claude SEO skills/agents 进去
4. **设环境**：
   - `ANTHROPIC_BASE_URL=http://localhost:8080` （指向本地翻译代理）
   - `ANTHROPIC_API_KEY=sk-deepseek-...`（其实是 DeepSeek key，代理会转）
5. **调 SDK**：
   ```python
   options = ClaudeAgentOptions(
       cwd=f"/workspace/{job_id}",
       setting_sources=["project"],
       allowed_tools=["Skill", "Read", "Write", "Bash", "Glob", "Grep"],
       max_turns=30,
   )
   async for message in query(prompt=f"运行 /seo page {url}", options=options):
       collect(message)
   ```
6. **聚合输出**：**主策略——读取 `/workspace/{job_id}/output/` 下的报告文件**（Claude SEO 写文件比拼接消息流稳定）；**兜底策略——从 SDK 消息流里提取 AssistantMessage 内容**（防止 Claude SEO 没写文件时还能拿到东西）
7. **返回**：`{"status": "ok", "report": "...", "elapsed_ms": 142000, "token_usage": {...}}`
8. **清理**：`rm -rf /workspace/{job_id}`

---

## 5. 验证计划

### 5.1 三段验证

**阶段 A：本地 Docker 验证（前 3 天）**
- 在开发机 `docker build` + `docker run`
- `curl -X POST http://localhost:8000/v1/audit -d '{"url":"https://example.com"}'`
- 通过：返回 200 + 非空有意义的 Markdown 报告
- 失败：进入 Risk 章节的 Fallback 流程

**阶段 B：Cloudflare Containers 部署验证（第 4–7 天）**
- 镜像推到 CF Container registry
- 配 Worker + Durable Object 路由
- 外网 `curl POST` 同样测试
- 通过：返回 200 + 同等质量报告（响应时间允许稍慢，含冷启动）
- 失败：考虑 Fly.io / Railway 备选

**阶段 C：成本与质量评估（第 8–10 天）**
- 对 5 个不同行业的真实 URL 各跑 3 次（共 15 次）
- 记录：响应时间、token 数、成本、报告质量人工评分（1–10）
- 通过：平均响应 ≤ 3 分钟、单次 ≤ 5 元、平均质量 ≥ 6/10
- 失败：换模型（Kimi / 通义千问）或考虑 Claude Haiku 备选

**质量评分标准（10 分制 rubric，避免 Day 10 主观争议）**：

| 维度 | 满分 | 说明 |
|---|---|---|
| 可执行建议数 | 2 分 | 报告里有 ≥3 条具体可改的 SEO 建议（不是空话）= 2 分；1–2 条 = 1 分；0 条 = 0 分 |
| 关键元素检测准确性 | 2 分 | title / meta description / H1 / Schema 等关键元素的检测和事实描述准确 = 2 分；有事实错误 = 0 分 |
| 报告结构清晰度 | 2 分 | 有清晰的章节划分、优先级标记 = 2 分；散乱难读 = 0 分 |
| 无幻觉 | 4 分 | 不编造网页上不存在的内容、不虚构 SEO 术语 = 4 分；轻微幻觉扣 2 分；严重幻觉 0 分 |

≥ 6/10 即合格；< 6/10 则触发 Fallback 流程。

### 5.2 三条硬验收标准（Go/No-Go）

| # | 标准 | 测量 |
|---|---|---|
| G1 | 本地+CF 都能跑通 | 阶段 A 和 B 都返回有意义报告 |
| G2 | 性能可接受 | 95% 请求响应 ≤ 3 分钟 |
| G3 | 成本可接受 | 平均单次 ≤ 5 元人民币 |

**全过 → MVP 通过 → 进入 Phase 2 产品化设计**
**任意一条不过 → 启动对应 Fallback 或停止主方案**

---

## 6. 风险与缓解

| # | 风险 | 严重度 | 缓解 |
|---|---|---|---|
| R1 | DeepSeek 对 Claude SEO 的提示词响应质量差，输出 SEO 报告不专业 | 🔴 高 | 单独评分 5 个真实 URL；如评分 < 6/10，切 Kimi 或 通义千问 Max 试 |
| R2 | DeepSeek 调用工具语法兼容性差，sub-agent 调用失败 | 🟠 中 | 只用 `/seo page`（不调 sub-agent）就能绕开大部分；Phase 2 再处理多 agent 协作 |
| R3 | Cloudflare Containers 仍是 public beta，可能有未知限制 | 🟠 中 | **Day 0 提前确认**：单镜像大小上限、单请求超时是否 ≥ 5 分钟、可选实例规格——任何一项不满足立刻切 Fly.io；备选：Fly.io（同 Docker 镜像），Railway，Render |
| R4 | 镜像太大（超过 CF 限制），构建/推送慢 | 🟡 低 | 用多阶段构建；Chromium 单独 layer；预估 1.5–2 GB |
| R5 | Claude Code CLI 在容器里跑不起来（依赖 Node.js 运行时） | 🟠 中 | 用 `node:20-slim` 基础镜像 + 单独装 Python；测试镜像启动 |
| R6 | claude-agent-sdk 加载 Claude SEO Skills 时找不到 | 🟡 低 | 仔细按官方文档配 `setting_sources=["project"]`；调试日志 |
| R7 | 翻译代理（one-api/LiteLLM）转换 Claude → OpenAI 格式有 bug | 🟠 中 | 先用 LiteLLM（更主流国际），不行再换 one-api |
| R8 | 单次成本超过 5 元 | 🟡 低 | DeepSeek V3 已经极便宜；超出的话基本意味着单次 token > 1M，应该是有 bug 而不是真的贵 |

---

## 7. Fallback 决策树（按出问题先后顺序）

```
主方案不通？
  │
  ├── 容器跑不起来？
  │    ├── 先排查镜像构建（Dockerfile 简化测试）
  │    └── 不行 → 换 base image（试 python:3.11-slim 而非 node:20-slim）
  │
  ├── Cloudflare Containers 部署失败？
  │    └── 切 Fly.io（一周内可切换，同镜像）
  │
  ├── DeepSeek 报告质量太差？
  │    ├── 试 Kimi（Moonshot K2）
  │    ├── 试通义千问 Max
  │    └── 全不行 → 认栽用 Claude Haiku（贵 10 倍但能跑）
  │
  ├── Claude Agent SDK + 翻译代理整体不兼容？
  │    └── 激进方案：放弃 Agent SDK，DeepSeek SDK + 自写编排
  │       （失去一键升级 Claude SEO 的好处，工作量翻 1 倍）
  │
  └── 成本超预算？
       └── 优化提示词缓存；裁剪 SKILL.md 中无关章节
```

---

## 8. 时间表（10 个工作日）

| 天数 | 任务 |
|---|---|
| Day 1 | 仓库初始化；Dockerfile 草稿；本地装 Claude Code + claude-agent-sdk |
| Day 2 | 翻译代理（LiteLLM）配通，本地能用 Claude Code + DeepSeek 跑简单对话 |
| Day 3 | 把 Claude SEO 加进容器；Agent SDK 调用 `/seo page` 跑通 |
| Day 4 | FastAPI 包装，本地 `curl POST` 走通端到端 |
| Day 5 | 5 个真实 URL 的本地评测（响应、成本、质量） |
| Day 6 | 部署到 Cloudflare Containers；调通 Worker + DO 路由 |
| Day 7 | CF 上重跑 5 个 URL 的评测 |
| Day 8 | 整理实测数据；写实测报告 |
| Day 9 | Buffer / 修坑 |
| Day 10 | 最终评审 + Go/No-Go 决策 |

---

## 9. 交付物

| # | 交付物 | 形式 |
|---|---|---|
| D1 | wrapper 仓库源代码 | GitHub repo |
| D2 | Dockerfile | repo 内 |
| D3 | LiteLLM 配置示例 | repo 内 |
| D4 | 部署文档（本地 + CF Containers） | repo 的 README.md |
| D5 | 实测报告 | Markdown，含响应时间、成本、质量评分、坑及解决 |
| D6 | Go/No-Go 决策声明 | 实测报告末尾，明确"是否进入 Phase 2" |

---

## 10. Phase 2 预览（不属本 spec，仅备忘）

MVP 通过后，下一阶段考虑：

- 多租户体系（用户、租户、API key 管理）
- 异步队列（Cloudflare Queues 或 Redis）
- 数据库（D1 任务表 + R2 报告存储）
- PDF 报告生成
- 完整 audit 命令、GEO 命令、技术 SEO 命令
- 接入用户现有 Next.js 网站（前端 UI）
- 付费 / 订阅
- 监控、日志、告警

---

## 11. 待 review 后明确的事项

以下问题在 spec review 后或实施过程中再定，本 spec 不锁死：

- [ ] wrapper 仓库托管位置（GitHub public / private）
- [ ] DeepSeek API key 来源（用户自有 / 平台共享）
- [ ] 翻译代理具体选 LiteLLM 还是 one-api（实测后定）
- [ ] CF Container 实例规格（256 MB / 1 GB / 4 GB）
- [ ] CI/CD 是否在 MVP 阶段引入（倾向不引入，手动 push 镜像）
