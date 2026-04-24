# Claude SEO SaaS MVP 原型 — 实施计划

> **给代理工作者的要求：** 实施本计划时必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项执行。复选框（`- [ ]`）用于跟踪进度。

**目标：** 构建一个 Docker 容器，用 FastAPI HTTP 接口包装 Claude SEO，并可部署到 Cloudflare Containers，以验证基于开源 Claude SEO 工具包构建多租户 SEO SaaS 的可行性。

**架构：** FastAPI 薄封装调用 `claude-agent-sdk`，后者以子进程方式启动 Claude Code CLI。Claude Code 从每次请求独立的工作目录中加载 Claude SEO 的 skills/agents。所有 LLM 调用都路由到运维提供的 `ANTHROPIC_BASE_URL` 端点（容器内部不感知具体实现）。容器保持无状态；每次请求创建并销毁自己的 workspace。

**技术栈：** Python 3.11、FastAPI、uvicorn、`claude-agent-sdk`（Python）、Claude Code CLI（Node.js 20）、Docker（multi-stage）、Cloudflare Containers。Claude SEO v1.7.2 以 git submodule 方式引入。

---

## 规格引用

权威规格：`docs/superpowers/specs/2026-04-21-mvp-prototype-design.md`

开始前必须先阅读规格。若本计划与规格存在歧义，以规格为准，尤其是：
- §3.1 / §3.2：范围内与明确不做的内容
- §4.4：8 步请求生命周期
- §5.2：三个硬性 Go/No-Go 标准（G1/G2/G3）
- §6：风险登记表（R6.1 要求 Day 2 验证环境变量透传）

## 范围检查

单一连贯子系统：**一个容器、一个 HTTP endpoint、一个 Claude SEO 命令（`/seo page`）**。

明确不包含：多租户用户管理、计费、UI、异步队列、其他 SEO 命令。这些属于规格 §10 的 Phase 2。

不需要再拆分子计划。

## 前置条件（Day 1 前必须具备）

- [ ] 运维提供：`ANTHROPIC_BASE_URL`（Claude 兼容）、`ANTHROPIC_API_KEY`、可选 `ANTHROPIC_MODEL`（规格 §3.3）
- [ ] Cloudflare 账号已启用 Containers；确认镜像大小限制和单请求超时时间 ≥ 5 分钟（规格 §6 R3）
- [ ] GitHub 账号具备创建私有仓库权限
- [ ] 本地开发机具备：Docker 24+、Python 3.11+、Node.js 20+、Git 2.40+

---

## 文件结构

计划创建一个**新的独立仓库**（建议名称：`claude-seo-wrapper`）。目标结构：

```text
claude-seo-wrapper/
├── .gitignore
├── .dockerignore
├── .gitmodules                         # submodule 指针
├── claude-seo/                         # git submodule → v1.7.2 tag
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── README.md                           # 环境变量契约 + docker run 示例
├── docs/
│   └── cf-deploy.md                    # CF Containers 部署指南
├── src/wrapper/
│   ├── __init__.py
│   ├── config.py                       # 约 40 行；环境变量加载 + fail-fast
│   ├── url_validator.py                # 约 20 行；封装 claude-seo 的 validate_url
│   ├── workspace.py                    # 约 60 行；每请求目录生命周期 + symlink
│   ├── runner.py                       # 约 80 行；claude-agent-sdk 调用
│   ├── output_parser.py                # 约 50 行；文件优先 + 消息流回退
│   └── api.py                          # 约 60 行；FastAPI POST /v1/audit
└── tests/
    ├── __init__.py
    ├── conftest.py                     # 共享 fixtures
    ├── test_config.py
    ├── test_url_validator.py
    ├── test_workspace.py
    ├── test_output_parser.py
    ├── test_runner.py                  # mock claude-agent-sdk
    ├── test_api.py                     # FastAPI TestClient + mocked runner
    ├── fixtures/
    │   ├── sample_report.md
    │   └── empty_output/
    └── integration/
        └── test_e2e_real.py            # gated: `E2E_REAL=1`；访问真实 endpoint
```

**理由：** 每个文件只负责一个职责（config / URL / workspace / runner / parser / API）。单文件尽量 ≤80 行。测试与源码 1:1 对应，便于导航。

---

## 工作流约定（读一次，所有任务都适用）

- **TDD**：每个源码模块都先写 `test_*.py`，先运行到失败，再实现，再运行到通过，最后提交。
- **提交**：每个任务结束必须 commit。提交信息格式：`feat(<module>): <what>`、`test(<module>): <what>`、`chore: <what>`。
- **不要跳过 run-to-fail**：如果测试在实现前就通过，说明测试写错了。
- **路径必须精确**：不要凭感觉使用相对路径。
- **遇到非预期失败就停止并询问**：不要硬推坏代码继续前进。

---

# Phase 1 — 仓库脚手架（Day 1）

## Task 1：初始化 wrapper 仓库

**文件：**
- 创建：`claude-seo-wrapper/.gitignore`
- 创建：`claude-seo-wrapper/.dockerignore`
- 创建：`claude-seo-wrapper/pyproject.toml`
- 创建：`claude-seo-wrapper/requirements.txt`
- 创建：`claude-seo-wrapper/README.md`

- [ ] **Step 1：创建目录并初始化 git**

```bash
mkdir claude-seo-wrapper
cd claude-seo-wrapper
git init
git branch -M main
```

- [ ] **Step 2：编写 `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
*.swp

# Env / secrets — NEVER commit
.env
.env.local
*.key
secrets/

# Local smoke tests & ad-hoc notes (may contain API keys / endpoint URLs)
notes/
scripts/smoke_*.py
/tmp/

# Build artifacts
dist/
build/
*.log
```

- [ ] **Step 3：编写 `.dockerignore`**

```dockerignore
.git/
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
tests/
docs/
.env*
*.md
!README.md
```

- [ ] **Step 4：编写 `pyproject.toml`**

```toml
[project]
name = "claude-seo-wrapper"
version = "0.1.0"
description = "FastAPI wrapper exposing Claude SEO as an HTTP service"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v --strict-markers"
markers = [
    "integration: real-endpoint integration tests (set E2E_REAL=1 to run)",
]
```

- [ ] **Step 5：编写 `requirements.txt`**

```txt
# Runtime
fastapi>=0.110.0,<1.0.0
uvicorn[standard]>=0.27.0,<1.0.0
claude-agent-sdk>=0.1.0
anyio>=4.2.0

# URL + safety
validators>=0.22.0,<1.0.0

# Dev / test
pytest>=7.4.0,<9.0.0
pytest-asyncio>=0.23.0,<1.0.0
httpx>=0.27.0,<1.0.0    # for FastAPI TestClient
```

- [ ] **Step 6：编写 `README.md` stub**

```markdown
# claude-seo-wrapper

FastAPI wrapper that exposes [Claude SEO](https://github.com/AgriciDaniel/claude-seo)
as an HTTP service, suitable for containerized deployment on Cloudflare Containers.

## Environment Variables

| Name | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_BASE_URL` | No | `https://api.anthropic.com` | Claude-compatible endpoint |
| `ANTHROPIC_API_KEY` | **Yes** | — | API key for the endpoint above |
| `ANTHROPIC_MODEL` | No | (Claude Code default) | Override model name |

## Run Locally

```bash
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-... \
  -e ANTHROPIC_BASE_URL=https://your.endpoint \
  ghcr.io/<your-org>/claude-seo-wrapper:latest
```

## API

`POST /v1/audit` — see `docs/` for details.
```

- [ ] **Step 7：提交**

```bash
git add .gitignore .dockerignore pyproject.toml requirements.txt README.md
git commit -m "chore: initialize wrapper repository scaffold"
```

## Task 2：以 git submodule 添加 Claude SEO

**文件：**
- 创建：`claude-seo-wrapper/.gitmodules`
- 创建：`claude-seo-wrapper/claude-seo/`（submodule）

- [ ] **Step 1：添加 submodule 并锁定到 v1.7.2**

```bash
git submodule add https://github.com/AgriciDaniel/claude-seo.git claude-seo
cd claude-seo && git checkout v1.7.2 && cd ..
git add claude-seo
```

说明：`-b` 接收分支而不是 tag。先 clone 默认分支，再 `checkout` tag；Git 会在 submodule 条目中记录 v1.7.2 指向的精确 commit。

- [ ] **Step 2：验证 submodule 解析到 v1.7.2**

```bash
cd claude-seo && git describe --tags && cd ..
```

期望：`v1.7.2`

- [ ] **Step 3：提交**

```bash
git add .gitmodules claude-seo
git commit -m "chore: add claude-seo submodule pinned to v1.7.2"
```

## Task 3：创建可构建的最小 Dockerfile

**文件：**
- 创建：`claude-seo-wrapper/Dockerfile`
- 创建：`claude-seo-wrapper/src/wrapper/__init__.py`

- [ ] 编写 multi-stage Dockerfile：第一阶段安装 Node.js 20 与 Claude Code CLI；第二阶段安装 Python 3.11 依赖、Claude SEO 依赖、Playwright/Chromium，并复制 wrapper 源码。
- [ ] 构建镜像：

```bash
docker build -t claude-seo-wrapper:scaffold .
```

- [ ] 检查镜像大小：

```bash
docker image inspect claude-seo-wrapper:scaffold --format "{{.Size}}"
```

期望：约 1.2 GB 到 1.8 GB。

- [ ] 烟测容器：

```bash
docker run --rm claude-seo-wrapper:scaffold
```

期望输出：`wrapper image OK`

- [ ] 提交：

```bash
git add Dockerfile src/wrapper/__init__.py
git commit -m "chore: add minimal multi-stage Dockerfile that builds"
```

---

# Phase 2 — 配置模块（Day 2 上午）

## Task 4：带 fail-fast 验证的配置加载器

**文件：**
- 创建：`src/wrapper/config.py`
- 创建：`tests/__init__.py`
- 创建：`tests/conftest.py`
- 创建：`tests/test_config.py`

- [ ] 先写失败测试，覆盖：默认 `ANTHROPIC_BASE_URL`、读取全部环境变量、缺失/空 `ANTHROPIC_API_KEY` 立即失败。
- [ ] 运行测试确认失败：

```bash
pytest tests/test_config.py -v
```

期望：`ModuleNotFoundError: No module named 'wrapper.config'`。

- [ ] 实现 `src/wrapper/config.py`：读取 `ANTHROPIC_API_KEY`、`ANTHROPIC_BASE_URL`、`ANTHROPIC_MODEL`；缺失 key 时抛 `ConfigError`；默认 base URL 为 `https://api.anthropic.com`。
- [ ] 运行测试确认通过：

```bash
PYTHONPATH=src pytest tests/test_config.py -v
```

期望：4 passed。

- [ ] 提交：

```bash
git add src/wrapper/config.py tests/__init__.py tests/conftest.py tests/test_config.py
git commit -m "feat(config): env var loader with fail-fast validation"
```

---

# Phase 3 — URL 验证器（Day 2 下午）

## Task 5：封装 claude-seo SSRF 防护的 URL 验证器

**文件：**
- 创建：`src/wrapper/url_validator.py`
- 创建：`tests/test_url_validator.py`

**上下文：** 规格 §4.4 step 3 要求复用 `claude-seo/scripts/google_auth.py::validate_url()` 做 SSRF 防护。wrapper 在此基础上额外强制 **https-only**（规格 §5.1：“HTTPS、非内网、能解析”）。

**上游契约（从 `claude-seo/scripts/google_auth.py:366` 验证）：**
- 签名：`validate_url(url: str) -> bool`
- 对有效公网 http/https URL 返回 `True`；其他返回 `False`
- 不抛异常，是纯谓词
- 接受 `http` 和 `https`（wrapper 再强制 https-only）
- 阻止：非 http(s) 协议、缺失 hostname、`localhost` / `127.0.0.1` / `0.0.0.0` / `::1`、GCP metadata、RFC1918 私有网段

- [ ] 先确认上游签名：

```bash
grep -n "def validate_url" claude-seo/scripts/google_auth.py
```

- [ ] 写失败测试：接受 `https://example.com`；拒绝 `http://example.com`、`file://...`、localhost、内网 IP、空字符串。
- [ ] 实现 wrapper：动态把 `claude-seo/scripts` 加入 `sys.path`，导入 `google_auth.validate_url`，并在上游通过后再检查 scheme 为 `https`。
- [ ] 运行测试：

```bash
PYTHONPATH=src pytest tests/test_url_validator.py -v
```

- [ ] 提交：

```bash
git add src/wrapper/url_validator.py tests/test_url_validator.py
git commit -m "feat(url): wrap claude-seo ssrf guard with https-only policy"
```

---

# Phase 4 — Workspace 管理（Day 3 上午）

## Task 6：每请求独立 workspace 与 symlink 策略

**文件：**
- 创建：`src/wrapper/workspace.py`
- 创建：`tests/test_workspace.py`

- [ ] 设计 `Workspace` 上下文管理器，为每个请求创建 `/workspace/{job_id}/`。
- [ ] 在 workspace 中链接或复制 Claude SEO 所需的 `skills/`、`agents/`、`scripts/`。
- [ ] 请求结束后清理 workspace，避免租户间状态泄漏。
- [ ] 测试覆盖：目录创建、唯一 job_id、资源链接存在、退出后清理。
- [ ] 运行测试：

```bash
PYTHONPATH=src pytest tests/test_workspace.py -v
```

- [ ] 提交：

```bash
git add src/wrapper/workspace.py tests/test_workspace.py
git commit -m "feat(workspace): isolate each request in temporary workspace"
```

---

# Phase 5 — Runner（Day 2 下午 + Day 3）

## Task 7：带 mocked SDK 测试的 runner 模块

**文件：**
- 创建：`src/wrapper/runner.py`
- 创建：`tests/test_runner.py`

- [ ] 定义 runner 输入：URL、workspace、config。
- [ ] 通过 `claude-agent-sdk` 启动 Claude Code，并执行 `/seo page <url>`。
- [ ] 把 `ANTHROPIC_BASE_URL`、`ANTHROPIC_API_KEY`、`ANTHROPIC_MODEL` 透传给子进程环境。
- [ ] 测试使用 mock SDK，验证 prompt、工作目录、环境变量与超时策略。
- [ ] 运行测试：

```bash
PYTHONPATH=src pytest tests/test_runner.py -v
```

- [ ] 提交：

```bash
git add src/wrapper/runner.py tests/test_runner.py
git commit -m "feat(runner): invoke claude seo through agent sdk"
```

## Task 8：手动烟测 — 真实 SDK 调用与环境变量透传

- [ ] 使用运维提供的 endpoint 与 key，运行最小 prompt 确认 SDK 能访问目标模型。
- [ ] 验证请求实际走 `ANTHROPIC_BASE_URL`，而不是默认 Anthropic endpoint。
- [ ] 记录响应时间、token 使用量（如果可用）和失败信息。
- [ ] 若透传失败，停止主方案并回到规格风险 R6.1。

## Task 9：手动烟测 — 通过 SDK 执行 Claude SEO `/seo page`

- [ ] 使用真实 URL 执行 `/seo page https://example.com`。
- [ ] 确认输出不是 hello world，也不是错误堆栈，而是有意义的 SEO 报告。
- [ ] 保存原始输出样本，供 output parser 测试使用。

---

# Phase 6 — 输出解析器（Day 3 晚）

## Task 10：文件优先 + 消息流回退的 output parser

**文件：**
- 创建：`src/wrapper/output_parser.py`
- 创建：`tests/test_output_parser.py`
- 创建：`tests/fixtures/sample_report.md`
- 创建：`tests/fixtures/empty_output/`

- [ ] 优先从 workspace 中读取报告文件（如 `FULL-AUDIT-REPORT.md`、`PAGE-REPORT.md` 或其他约定文件）。
- [ ] 若没有文件，则从 SDK 消息流中提取最后一个有意义文本。
- [ ] 空输出或错误输出应返回明确错误，而不是假装成功。
- [ ] 测试覆盖：文件优先、消息回退、空目录、空消息。
- [ ] 运行测试：

```bash
PYTHONPATH=src pytest tests/test_output_parser.py -v
```

- [ ] 提交：

```bash
git add src/wrapper/output_parser.py tests/test_output_parser.py tests/fixtures
git commit -m "feat(output): parse reports with file-first fallback"
```

---

# Phase 7 — FastAPI 应用（Day 4）

## Task 11：`POST /v1/audit` endpoint

**文件：**
- 创建：`src/wrapper/api.py`
- 创建：`tests/test_api.py`

- [ ] 定义请求体：`{"url": "https://example.com"}`。
- [ ] 定义成功响应：`{"status": "ok", "report": "# SEO 分析\n..."}`。
- [ ] 定义错误响应：`{"status": "error", "error": "..."}`。
- [ ] endpoint 生命周期：加载 config → 验证 URL → 创建 workspace → 调用 runner → 解析输出 → 清理 workspace。
- [ ] 测试覆盖：成功请求、无效 URL、runner 报错、缺失配置。
- [ ] 运行测试：

```bash
PYTHONPATH=src pytest tests/test_api.py -v
```

- [ ] 提交：

```bash
git add src/wrapper/api.py tests/test_api.py
git commit -m "feat(api): expose audit endpoint"
```

## Task 12：本地端到端测试（不使用 Docker）

- [ ] 启动服务：

```bash
PYTHONPATH=src uvicorn wrapper.api:app --host 127.0.0.1 --port 8000
```

- [ ] 调用接口：

```bash
curl -X POST http://127.0.0.1:8000/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

- [ ] 验证：返回 `status=ok`，报告非空且包含 SEO 分析内容。

---

# Phase 8 — Docker 化（Day 4 晚 / Day 5 上午）

## Task 13：完善 Dockerfile entry point

- [ ] Docker 默认命令启动 `uvicorn wrapper.api:app --host 0.0.0.0 --port 8000`。
- [ ] 确保 `PYTHONPATH=src` 或安装包路径正确。
- [ ] 确保容器中存在 Claude Code CLI、Claude SEO submodule、Python 依赖和 Playwright/Chromium。
- [ ] 重新构建镜像并运行单元测试或导入检查。

## Task 14：接入 workspace root 并验证容器级环境变量透传

- [ ] 运行容器：

```bash
docker run --rm -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-... \
  -e ANTHROPIC_BASE_URL=https://your.endpoint \
  -e ANTHROPIC_MODEL=your-model \
  claude-seo-wrapper:latest
```

- [ ] 通过 `curl` 调用 `/v1/audit`，确认端到端成功。
- [ ] 若环境变量没有传入 Claude Code 子进程，立即停止并修复 runner。

---

# Phase 9 — 本地评估（Day 5）

## Task 15：5 个 URL × 3 次运行评估与报告

- [ ] 选择 5 个 URL，覆盖 SaaS、内容页、产品页、本地业务页、复杂 JS 页面。
- [ ] 每个 URL 连续运行 3 次。
- [ ] 记录：成功率、响应时间、成本、报告质量评分（0-10）、主要失败模式。
- [ ] 判断本地是否满足 G1/G3：真实报告、≤3 分钟、单次 token 成本 ≤5 元人民币、质量评分 ≥6/10。

---

# Phase 10 — Cloudflare Containers 部署（Day 6–7）

## Task 16：设置 Cloudflare Worker 与 Durable Object 路由

- [ ] 创建 Cloudflare Worker 项目和 Containers 配置。
- [ ] 配置路由，使外部 `POST /v1/audit` 能转发到容器。
- [ ] 使用 `wrangler secret put ANTHROPIC_API_KEY` 写入密钥。
- [ ] 可选写入：

```bash
wrangler secret put ANTHROPIC_BASE_URL
wrangler secret put ANTHROPIC_MODEL
```

## Task 17：部署到 Cloudflare Containers

- [ ] 构建并推送镜像。
- [ ] 部署 Worker/Container。
- [ ] 从公网执行 `curl POST`。
- [ ] 验证返回报告质量与本地一致。

## Task 18：在 Cloudflare 上重复 5 个 URL × 3 次评估

- [ ] 使用与 Task 15 相同的 URL 和评分方法。
- [ ] 将本地 `127.0.0.1:8000` 替换为 Cloudflare 公开 endpoint。
- [ ] 比较本地与 CF：成功率、延迟、成本、失败原因。

---

# Phase 11 — 最终报告与决策（Day 8–10）

## Task 19：编写 MVP 测试报告

**文件：**
- 创建：`docs/mvp-test-report.md`

建议结构：

```markdown
# Claude SEO SaaS MVP — 测试报告

## Executive Summary

## Environment

## Local Results (Phase 9 / Task 15)

## Cloudflare Results (Phase 10 / Task 18)

## Observations

## Risks Surfaced

## Go / No-Go Decision

## Phase 2 Recommendations
```

报告必须回答：
- G1：HTTP → 容器 → Claude SEO → LLM endpoint → SEO 报告链路是否跑通？
- G2：同一镜像在 Cloudflare Containers 上是否跑通？
- G3：质量与成本是否可接受？

## Task 20：最终交付清单

- [ ] 私有 GitHub 仓库已创建并推送：

```bash
# 先通过 GitHub UI 创建私有仓库，然后：
git remote add origin git@github.com:<org>/claude-seo-wrapper.git
git push -u origin main
```

- [ ] Docker 镜像可本地运行
- [ ] Cloudflare Containers 部署可访问
- [ ] 本地与 CF 评估结果已写入 `docs/mvp-test-report.md`
- [ ] Go/No-Go 结论明确
- [ ] 若 Go：列出 Phase 2 建议（异步队列、租户隔离、计费、UI、命令扩展）
- [ ] 若 No-Go：列出阻断原因和替代方案

## 完成定义

本计划完成时，应满足：
1. `POST /v1/audit` 可对真实 URL 返回非空、有意义的 SEO 报告。
2. 本地 Docker 与 Cloudflare Containers 均通过端到端测试。
3. 环境变量透传已验证，模型 endpoint 不写死在容器内。
4. 每次请求使用独立 workspace，请求结束后清理。
5. 最终报告给出明确 Go/No-Go 决策。
