# Claude SEO Wrapper 增量骨架实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先搭出可构建、可运行、可 curl 验证的 Docker + FastAPI 最小骨架，再逐层加入 Node.js、Claude Code CLI 和 Claude SEO 文件，为后续 SDK 与真实 `/seo page` 调用做准备。

**Architecture:** 本计划只实现增量组装的第 0–2 层：第 0 层提供 FastAPI mock 服务；第 1 层把 Node.js 20 与 Claude Code CLI 放进镜像并提供环境检查；第 2 层把 Claude SEO 以 submodule 方式加入镜像并验证关键目录存在。暂不调用 `claude-agent-sdk`，暂不连接真实 LLM endpoint，暂不部署 Cloudflare Containers。

**Tech Stack:** Python 3.11、FastAPI、uvicorn、pytest、httpx、Docker、Node.js 20、Claude Code CLI、Claude SEO git submodule。

---

## Scope Check

本计划只覆盖“先把架子和镜像搭出来”的增量阶段，目标是降低后续集成风险。

**包含：**
- 新建独立 wrapper 仓库结构。
- 可运行 FastAPI 服务。
- `/health` 健康检查。
- mock 版 `POST /v1/audit`。
- Docker 镜像构建和本地运行。
- 镜像内安装 Node.js 20 与 Claude Code CLI。
- 引入 Claude SEO submodule 并在镜像内验证文件存在。

**不包含：**
- 不接入 `claude-agent-sdk`。
- 不调用 `/seo page`。
- 不配置 `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_KEY`。
- 不做 workspace 隔离。
- 不做报告文件解析。
- 不部署 Cloudflare Containers。

---

## Target File Structure

```text
claude-seo-wrapper/
├── .dockerignore
├── .gitignore
├── .gitmodules
├── Dockerfile
├── README.md
├── claude-seo/                 # git submodule，先只验证存在，不调用
├── pyproject.toml
├── requirements.txt
├── src/
│   └── wrapper/
│       ├── __init__.py
│       ├── api.py              # FastAPI app、/health、mock /v1/audit
│       └── runtime_checks.py   # 镜像内运行时依赖检查
└── tests/
    ├── __init__.py
    ├── test_api.py
    └── test_runtime_checks.py
```

**边界说明：**
- `api.py` 只负责 HTTP 层和 mock 响应。
- `runtime_checks.py` 只负责检查外部命令和 Claude SEO 文件是否存在。
- Dockerfile 只负责打包可运行环境，不承担业务逻辑。

---

## Workflow Rules

- 每个任务先写测试，再实现，再运行验证。
- 每个任务完成后提交一次。
- 每层都必须能 `docker build`、`docker run`、`curl` 验证。
- 后续任务不能破坏前一层的验收命令。

---

# Phase 0 — 最小 FastAPI 骨架

## Task 1: 初始化 wrapper 仓库骨架

**Files:**
- Create: `claude-seo-wrapper/.gitignore`
- Create: `claude-seo-wrapper/.dockerignore`
- Create: `claude-seo-wrapper/pyproject.toml`
- Create: `claude-seo-wrapper/requirements.txt`
- Create: `claude-seo-wrapper/README.md`
- Create: `claude-seo-wrapper/src/wrapper/__init__.py`
- Create: `claude-seo-wrapper/tests/__init__.py`

- [ ] **Step 1: 创建目录并初始化 git**

```bash
mkdir claude-seo-wrapper
cd claude-seo-wrapper
git init
git branch -M main
mkdir -p src/wrapper tests
```

Expected: 当前目录为 `claude-seo-wrapper`，且 `git status` 可正常执行。

- [ ] **Step 2: 写入 `.gitignore`**

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.env
.env.*
*.log
.idea/
.vscode/
```

- [ ] **Step 3: 写入 `.dockerignore`**

```dockerignore
.git/
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
.env*
tests/
*.log
```

- [ ] **Step 4: 写入 `pyproject.toml`**

```toml
[project]
name = "claude-seo-wrapper"
version = "0.1.0"
description = "Incremental FastAPI wrapper for Claude SEO"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v"
```

- [ ] **Step 5: 写入 `requirements.txt`**

```txt
fastapi>=0.110.0,<1.0.0
uvicorn[standard]>=0.27.0,<1.0.0
pytest>=7.4.0,<9.0.0
httpx>=0.27.0,<1.0.0
```

- [ ] **Step 6: 写入 `README.md`**

```markdown
# claude-seo-wrapper

Claude SEO 的增量式 FastAPI wrapper。

当前阶段目标：先构建可运行 Docker 镜像和 mock HTTP API，再逐步加入 Claude Code、Claude SEO、SDK 和真实 SEO 分析。

## Local Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn wrapper.api:app --host 127.0.0.1 --port 8000
```

## Docker

```bash
docker build -t claude-seo-wrapper:base .
docker run --rm -p 8000:8000 claude-seo-wrapper:base
```

## API

- `GET /health`
- `POST /v1/audit`
```

- [ ] **Step 7: 创建空包文件**

```bash
touch src/wrapper/__init__.py tests/__init__.py
```

Windows PowerShell 可用：

```powershell
New-Item -ItemType File -Force src/wrapper/__init__.py, tests/__init__.py
```

- [ ] **Step 8: 提交**

```bash
git add .gitignore .dockerignore pyproject.toml requirements.txt README.md src/wrapper/__init__.py tests/__init__.py
git commit -m "chore: initialize incremental wrapper scaffold"
```

---

## Task 2: 添加 FastAPI mock API

**Files:**
- Create: `claude-seo-wrapper/src/wrapper/api.py`
- Create: `claude-seo-wrapper/tests/test_api.py`

- [ ] **Step 1: 写失败测试 `tests/test_api.py`**

```python
from fastapi.testclient import TestClient

from wrapper.api import app


client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_audit_returns_mock_report_for_https_url():
    response = client.post("/v1/audit", json={"url": "https://example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["url"] == "https://example.com"
    assert body["mode"] == "mock"
    assert body["report"].startswith("# SEO 分析")


def test_audit_rejects_missing_url():
    response = client.post("/v1/audit", json={})

    assert response.status_code == 422
```

- [ ] **Step 2: 运行测试确认失败**

```bash
PYTHONPATH=src pytest tests/test_api.py -v
```

Expected: FAIL，错误包含 `ModuleNotFoundError: No module named 'wrapper.api'`。

- [ ] **Step 3: 实现 `src/wrapper/api.py`**

```python
from pydantic import BaseModel, HttpUrl
from fastapi import FastAPI


app = FastAPI(title="Claude SEO Wrapper", version="0.1.0")


class AuditRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/audit")
def audit(request: AuditRequest) -> dict[str, str]:
    url = str(request.url).rstrip("/")
    return {
        "status": "ok",
        "mode": "mock",
        "url": url,
        "report": f"# SEO 分析\n\n这是 `{url}` 的 mock SEO 报告。",
    }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
PYTHONPATH=src pytest tests/test_api.py -v
```

Expected: 3 passed。

- [ ] **Step 5: 本地启动并 curl 验证**

```bash
PYTHONPATH=src uvicorn wrapper.api:app --host 127.0.0.1 --port 8000
```

另开终端：

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

Expected:
- `/health` 返回 `{"status":"ok"}`。
- `/v1/audit` 返回 `status=ok`、`mode=mock`、非空 Markdown 报告。

- [ ] **Step 6: 提交**

```bash
git add src/wrapper/api.py tests/test_api.py
git commit -m "feat(api): add mock audit endpoint"
```

---

## Task 3: 添加最小 Docker 镜像

**Files:**
- Create: `claude-seo-wrapper/Dockerfile`
- Modify: `claude-seo-wrapper/README.md`

- [ ] **Step 1: 写入 `Dockerfile`**

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "wrapper.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 构建镜像**

```bash
docker build -t claude-seo-wrapper:base .
```

Expected: build 成功，无 Python 依赖安装错误。

- [ ] **Step 3: 运行容器**

```bash
docker run --rm -p 8000:8000 claude-seo-wrapper:base
```

Expected: uvicorn 启动日志显示监听 `0.0.0.0:8000`。

- [ ] **Step 4: curl 验证容器 API**

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

Expected: 与本地 uvicorn 运行结果一致。

- [ ] **Step 5: 记录镜像大小**

```bash
docker image inspect claude-seo-wrapper:base --format "{{.Size}}"
```

Expected: 得到一个整数 byte 值。当前阶段通常应明显小于最终镜像。

- [ ] **Step 6: 更新 README Docker 标签说明**

把 README 中 Docker 示例保持为：

```markdown
```bash
docker build -t claude-seo-wrapper:base .
docker run --rm -p 8000:8000 claude-seo-wrapper:base
```
```

- [ ] **Step 7: 提交**

```bash
git add Dockerfile README.md
git commit -m "chore(docker): add minimal FastAPI image"
```

---

# Phase 1 — 加入 Node.js 与 Claude Code CLI

## Task 4: 镜像内安装 Node.js 20 与 Claude Code CLI

**Files:**
- Modify: `claude-seo-wrapper/Dockerfile`
- Create: `claude-seo-wrapper/src/wrapper/runtime_checks.py`
- Create: `claude-seo-wrapper/tests/test_runtime_checks.py`
- Modify: `claude-seo-wrapper/src/wrapper/api.py`

- [ ] **Step 1: 写失败测试 `tests/test_runtime_checks.py`**

```python
from wrapper.runtime_checks import summarize_runtime


def test_summarize_runtime_reports_dependency_keys():
    result = summarize_runtime()

    assert "python" in result
    assert "node" in result
    assert "claude" in result
```

- [ ] **Step 2: 运行测试确认失败**

```bash
PYTHONPATH=src pytest tests/test_runtime_checks.py -v
```

Expected: FAIL，错误包含 `ModuleNotFoundError: No module named 'wrapper.runtime_checks'`。

- [ ] **Step 3: 实现 `src/wrapper/runtime_checks.py`**

```python
from __future__ import annotations

import shutil
import subprocess
import sys


def _version(command: list[str]) -> str:
    executable = shutil.which(command[0])
    if executable is None:
        return "missing"
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        return f"error: {exc.__class__.__name__}"

    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else "unknown"


def summarize_runtime() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "node": _version(["node", "--version"]),
        "claude": _version(["claude", "--version"]),
    }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
PYTHONPATH=src pytest tests/test_runtime_checks.py -v
```

Expected: 1 passed。宿主机没有 node 或 claude 时也应通过，因为返回 `missing` 是允许的。

- [ ] **Step 5: 给 API 增加 `/runtime` endpoint**

修改 `src/wrapper/api.py` 为：

```python
from pydantic import BaseModel, HttpUrl
from fastapi import FastAPI

from wrapper.runtime_checks import summarize_runtime


app = FastAPI(title="Claude SEO Wrapper", version="0.1.0")


class AuditRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/runtime")
def runtime() -> dict[str, str]:
    return summarize_runtime()


@app.post("/v1/audit")
def audit(request: AuditRequest) -> dict[str, str]:
    url = str(request.url).rstrip("/")
    return {
        "status": "ok",
        "mode": "mock",
        "url": url,
        "report": f"# SEO 分析\n\n这是 `{url}` 的 mock SEO 报告。",
    }
```

- [ ] **Step 6: 扩展 API 测试**

在 `tests/test_api.py` 末尾追加：

```python

def test_runtime_returns_dependency_summary():
    response = client.get("/runtime")

    assert response.status_code == 200
    body = response.json()
    assert "python" in body
    assert "node" in body
    assert "claude" in body
```

- [ ] **Step 7: 运行 Python 测试**

```bash
PYTHONPATH=src pytest tests/test_api.py tests/test_runtime_checks.py -v
```

Expected: 4 passed。

- [ ] **Step 8: 修改 Dockerfile 安装 Node.js 20 和 Claude Code CLI**

将 `Dockerfile` 改为：

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @anthropic-ai/claude-code \
    && apt-get purge -y --auto-remove curl gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "wrapper.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 9: 构建 CLI 镜像**

```bash
docker build -t claude-seo-wrapper:cli .
```

Expected: build 成功，`npm install -g @anthropic-ai/claude-code` 无错误。

- [ ] **Step 10: 验证镜像内命令**

```bash
docker run --rm claude-seo-wrapper:cli node --version
docker run --rm claude-seo-wrapper:cli claude --version
```

Expected:
- `node --version` 输出 `v20...`。
- `claude --version` 输出版本号或 CLI 版本信息。

- [ ] **Step 11: 验证 `/runtime`**

```bash
docker run --rm -p 8000:8000 claude-seo-wrapper:cli
```

另开终端：

```bash
curl http://127.0.0.1:8000/runtime
```

Expected: JSON 中 `node` 不是 `missing`，`claude` 不是 `missing`。

- [ ] **Step 12: 提交**

```bash
git add Dockerfile src/wrapper/runtime_checks.py src/wrapper/api.py tests/test_runtime_checks.py tests/test_api.py
git commit -m "chore(runtime): add node and claude cli checks"
```

---

# Phase 2 — 加入 Claude SEO 文件

## Task 5: 添加 Claude SEO submodule 并验证目录

**Files:**
- Create: `claude-seo-wrapper/.gitmodules`
- Create: `claude-seo-wrapper/claude-seo/`
- Modify: `claude-seo-wrapper/src/wrapper/runtime_checks.py`
- Modify: `claude-seo-wrapper/tests/test_runtime_checks.py`
- Modify: `claude-seo-wrapper/src/wrapper/api.py`

- [ ] **Step 1: 添加 submodule 并锁定 tag**

```bash
git submodule add https://github.com/AgriciDaniel/claude-seo.git claude-seo
cd claude-seo
git checkout v1.7.2
cd ..
```

Expected:

```bash
cd claude-seo && git describe --tags && cd ..
```

输出 `v1.7.2`。

- [ ] **Step 2: 扩展 runtime checks 测试**

将 `tests/test_runtime_checks.py` 改为：

```python
from pathlib import Path

from wrapper.runtime_checks import claude_seo_paths, summarize_runtime


def test_summarize_runtime_reports_dependency_keys():
    result = summarize_runtime()

    assert "python" in result
    assert "node" in result
    assert "claude" in result
    assert "claude_seo" in result


def test_claude_seo_paths_uses_supplied_root(tmp_path):
    root = tmp_path / "claude-seo"
    (root / "skills" / "seo").mkdir(parents=True)
    (root / "agents").mkdir()
    (root / "scripts").mkdir()

    result = claude_seo_paths(root)

    assert result == {
        "root": "present",
        "skills_seo": "present",
        "agents": "present",
        "scripts": "present",
    }


def test_claude_seo_paths_reports_missing_paths(tmp_path):
    root = tmp_path / "missing-claude-seo"

    result = claude_seo_paths(root)

    assert result == {
        "root": "missing",
        "skills_seo": "missing",
        "agents": "missing",
        "scripts": "missing",
    }
```

- [ ] **Step 3: 运行测试确认失败**

```bash
PYTHONPATH=src pytest tests/test_runtime_checks.py -v
```

Expected: FAIL，错误包含 `cannot import name 'claude_seo_paths'`。

- [ ] **Step 4: 实现 Claude SEO 路径检查**

将 `src/wrapper/runtime_checks.py` 改为：

```python
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_CLAUDE_SEO_ROOT = Path(os.environ.get("CLAUDE_SEO_ROOT", "/app/claude-seo"))


def _version(command: list[str]) -> str:
    executable = shutil.which(command[0])
    if executable is None:
        return "missing"
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        return f"error: {exc.__class__.__name__}"

    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else "unknown"


def _presence(path: Path) -> str:
    return "present" if path.exists() else "missing"


def claude_seo_paths(root: Path = DEFAULT_CLAUDE_SEO_ROOT) -> dict[str, str]:
    return {
        "root": _presence(root),
        "skills_seo": _presence(root / "skills" / "seo"),
        "agents": _presence(root / "agents"),
        "scripts": _presence(root / "scripts"),
    }


def summarize_runtime() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "node": _version(["node", "--version"]),
        "claude": _version(["claude", "--version"]),
        "claude_seo": claude_seo_paths(),
    }
```

- [ ] **Step 5: 调整 API runtime 响应类型**

将 `src/wrapper/api.py` 改为：

```python
from typing import Any

from pydantic import BaseModel, HttpUrl
from fastapi import FastAPI

from wrapper.runtime_checks import summarize_runtime


app = FastAPI(title="Claude SEO Wrapper", version="0.1.0")


class AuditRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/runtime")
def runtime() -> dict[str, Any]:
    return summarize_runtime()


@app.post("/v1/audit")
def audit(request: AuditRequest) -> dict[str, str]:
    url = str(request.url).rstrip("/")
    return {
        "status": "ok",
        "mode": "mock",
        "url": url,
        "report": f"# SEO 分析\n\n这是 `{url}` 的 mock SEO 报告。",
    }
```

- [ ] **Step 6: 运行测试确认通过**

```bash
PYTHONPATH=src pytest tests/test_api.py tests/test_runtime_checks.py -v
```

Expected: 6 passed。

- [ ] **Step 7: 修改 Dockerfile 复制 Claude SEO**

在 `COPY src ./src` 前增加：

```dockerfile
COPY claude-seo ./claude-seo
```

完整 Dockerfile 应为：

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV CLAUDE_SEO_ROOT=/app/claude-seo

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @anthropic-ai/claude-code \
    && apt-get purge -y --auto-remove curl gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY claude-seo ./claude-seo
COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "wrapper.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 8: 构建包含 Claude SEO 的镜像**

```bash
docker build -t claude-seo-wrapper:with-seo .
```

Expected: build 成功。

- [ ] **Step 9: 验证容器内 Claude SEO 目录**

```bash
docker run --rm claude-seo-wrapper:with-seo test -d /app/claude-seo/skills/seo
docker run --rm claude-seo-wrapper:with-seo test -d /app/claude-seo/agents
docker run --rm claude-seo-wrapper:with-seo test -d /app/claude-seo/scripts
```

Expected: 三条命令 exit code 都为 0。

- [ ] **Step 10: 验证 `/runtime` 显示 Claude SEO present**

```bash
docker run --rm -p 8000:8000 claude-seo-wrapper:with-seo
```

另开终端：

```bash
curl http://127.0.0.1:8000/runtime
```

Expected: `claude_seo.root`、`claude_seo.skills_seo`、`claude_seo.agents`、`claude_seo.scripts` 均为 `present`。

- [ ] **Step 11: 提交**

```bash
git add .gitmodules claude-seo Dockerfile src/wrapper/runtime_checks.py src/wrapper/api.py tests/test_runtime_checks.py
git commit -m "chore(seo): add claude seo submodule to image"
```

---

# Final Verification

- [ ] **Step 1: 运行完整 Python 测试**

```bash
PYTHONPATH=src pytest -v
```

Expected: 所有测试通过。

- [ ] **Step 2: 构建最终增量镜像**

```bash
docker build -t claude-seo-wrapper:incremental-foundation .
```

Expected: build 成功。

- [ ] **Step 3: 运行最终镜像**

```bash
docker run --rm -p 8000:8000 claude-seo-wrapper:incremental-foundation
```

- [ ] **Step 4: 验证三个 endpoint**

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/runtime
curl -X POST http://127.0.0.1:8000/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

Expected:
- `/health` 返回 `{"status":"ok"}`。
- `/runtime` 返回 Python、Node、Claude CLI、Claude SEO 目录检查结果。
- `/v1/audit` 返回 mock SEO 报告。

- [ ] **Step 5: 记录下一阶段入口条件**

进入下一阶段前必须满足：
1. Docker 镜像可稳定构建。
2. 容器启动后 `/health` 正常。
3. `/runtime` 显示 `node`、`claude` 不为 `missing`。
4. `/runtime` 显示 Claude SEO 四个路径均为 `present`。
5. `/v1/audit` mock 接口稳定返回。

下一阶段才开始加入：`ANTHROPIC_*` 配置、`claude-agent-sdk`、最小 prompt、真实 `/seo page` 调用。

---

# Self-Review

- **Spec coverage:** 覆盖 specs 中 Docker、FastAPI、Node.js、Claude Code CLI、Claude SEO submodule、本地 curl 验证的前置增量能力；刻意不覆盖 endpoint、SDK、Cloudflare 和真实 SEO 调用。
- **Placeholder scan:** 本计划无 TBD/TODO；每个代码步骤包含明确文件内容或明确修改片段。
- **Type consistency:** `summarize_runtime()` 在 Task 4 返回 `dict[str, str]`，Task 5 扩展为 `dict[str, object]`，API 同步调整为 `dict[str, Any]`。
- **Scope check:** 范围单一，产出可独立验证的软件骨架。
