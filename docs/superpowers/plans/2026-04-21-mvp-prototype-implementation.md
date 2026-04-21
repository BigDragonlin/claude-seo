# Claude SEO SaaS MVP Prototype — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Docker container that wraps Claude SEO behind a FastAPI HTTP endpoint, deployable on Cloudflare Containers, proving that a multi-tenant SEO SaaS can be built on the open-source Claude SEO toolkit.

**Architecture:** A thin FastAPI wrapper invokes `claude-agent-sdk`, which launches Claude Code CLI as a subprocess. Claude Code loads Claude SEO's skills/agents from a per-request workspace directory. All LLM calls route to an operator-supplied `ANTHROPIC_BASE_URL` endpoint (opaque to the container). The container is stateless; each request creates and destroys its own workspace.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, `claude-agent-sdk` (Python), Claude Code CLI (Node.js 20), Docker (multi-stage), Cloudflare Containers. Claude SEO v1.7.2 pulled as a git submodule.

---

## Spec Reference

Canonical spec: `docs/superpowers/specs/2026-04-21-mvp-prototype-design.md`

Read it before starting. This plan decomposes the spec into concrete tasks; if there's ambiguity, spec wins. In particular:
- §3.1 / §3.2 — what's in scope and what's explicitly not
- §4.4 — the 8-step request lifecycle
- §5.2 — three hard Go/No-Go criteria (G1/G2/G3)
- §6 — risk register (R6.1 demands Day 2 env-passthrough verification)

## Scope Check

Single coherent subsystem: **one container, one HTTP endpoint, one Claude SEO command (`/seo page`)**. Does **NOT** cover: multi-tenant user management, billing, UI, async queue, other SEO commands. Those are explicitly Phase 2 (spec §10).

No sub-plan decomposition needed.

## Prerequisites (must be in place BEFORE Day 1)

- [ ] Operator provides: `ANTHROPIC_BASE_URL` (Claude-compatible), `ANTHROPIC_API_KEY`, optional `ANTHROPIC_MODEL` (spec §3.3)
- [ ] Cloudflare account with Containers enabled; confirm image-size cap and per-request timeout ≥ 5 min (spec §6 R3)
- [ ] GitHub account with permission to create a private repo
- [ ] Local dev machine with: Docker 24+, Python 3.11+, Node.js 20+, Git 2.40+

---

## File Structure

Plan creates a **new, separate repository** (name suggestion: `claude-seo-wrapper`). Target layout:

```
claude-seo-wrapper/
├── .gitignore
├── .dockerignore
├── .gitmodules                        # submodule pointer
├── claude-seo/                        # git submodule → v1.7.2 tag
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── README.md                          # env var contract + docker run example
├── docs/
│   └── cf-deploy.md                   # CF Containers deploy guide
├── src/wrapper/
│   ├── __init__.py
│   ├── config.py                      # ~40 lines; env var loading with fail-fast
│   ├── url_validator.py               # ~20 lines; wraps claude-seo's validate_url
│   ├── workspace.py                   # ~60 lines; per-request dir lifecycle + symlink
│   ├── runner.py                      # ~80 lines; claude-agent-sdk invocation
│   ├── output_parser.py               # ~50 lines; file-first + msg-stream fallback
│   └── api.py                         # ~60 lines; FastAPI POST /v1/audit
└── tests/
    ├── __init__.py
    ├── conftest.py                    # shared fixtures
    ├── test_config.py
    ├── test_url_validator.py
    ├── test_workspace.py
    ├── test_output_parser.py
    ├── test_runner.py                 # mocks claude-agent-sdk
    ├── test_api.py                    # FastAPI TestClient + mocked runner
    ├── fixtures/
    │   ├── sample_report.md
    │   └── empty_output/              # directory with no files
    └── integration/
        └── test_e2e_real.py           # gated: `E2E_REAL=1`; hits actual endpoint
```

**Rationale:** One file per responsibility (config / URL / workspace / runner / parser / API). Each file ≤ 80 lines. Tests mirror source 1:1 for easy navigation.

---

## Workflow Conventions (read once, apply everywhere)

- **TDD**: every source module gets `test_*.py` written first, run-to-fail, implement, run-to-pass, then commit.
- **Commits**: every task ends with a commit. Commit message format: `feat(<module>): <what>`, `test(<module>): <what>`, `chore: <what>`.
- **Never skip the "run-to-fail" step** — if a test passes before implementation, the test is wrong.
- **Exact paths always** — no relative guesswork.
- **If a step fails unexpectedly, stop and ask**. Don't force broken code forward.

---

# Phase 1 — Repository Scaffold (Day 1)

## Task 1: Initialize wrapper repository

**Files:**
- Create: `claude-seo-wrapper/.gitignore`
- Create: `claude-seo-wrapper/.dockerignore`
- Create: `claude-seo-wrapper/pyproject.toml`
- Create: `claude-seo-wrapper/requirements.txt`
- Create: `claude-seo-wrapper/README.md`

- [ ] **Step 1: Create directory and init git**

```bash
mkdir claude-seo-wrapper
cd claude-seo-wrapper
git init
git branch -M main
```

- [ ] **Step 2: Write `.gitignore`**

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

- [ ] **Step 3: Write `.dockerignore`**

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

- [ ] **Step 4: Write `pyproject.toml`**

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

- [ ] **Step 5: Write `requirements.txt`**

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

- [ ] **Step 6: Write `README.md` stub**

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

- [ ] **Step 7: Commit**

```bash
git add .gitignore .dockerignore pyproject.toml requirements.txt README.md
git commit -m "chore: initialize wrapper repository scaffold"
```

---

## Task 2: Add Claude SEO as git submodule

**Files:**
- Create: `claude-seo-wrapper/.gitmodules`
- Create: `claude-seo-wrapper/claude-seo/` (submodule)

- [ ] **Step 1: Add submodule locked to v1.7.2**

```bash
git submodule add https://github.com/AgriciDaniel/claude-seo.git claude-seo
cd claude-seo && git checkout v1.7.2 && cd ..
git add claude-seo
```

(`-b` takes a branch, not a tag. Clone the default branch first, then `checkout` the tag — Git records the exact commit pointed to by v1.7.2 in the submodule entry.)

- [ ] **Step 2: Verify submodule resolved to v1.7.2**

```bash
cd claude-seo && git describe --tags && cd ..
```

Expected: `v1.7.2`

- [ ] **Step 3: Verify expected Claude SEO files are present**

```bash
test -f claude-seo/skills/seo/SKILL.md && echo "seo skill OK"
test -d claude-seo/agents && echo "agents dir OK"
test -f claude-seo/scripts/google_auth.py && echo "google_auth OK"
```

Expected: three "OK" lines printed.

- [ ] **Step 4: Commit submodule addition**

```bash
git add .gitmodules claude-seo
git commit -m "chore: add claude-seo submodule (v1.7.2)"
```

---

## Task 3: Create minimal Dockerfile that builds

**Files:**
- Create: `claude-seo-wrapper/Dockerfile`

- [ ] **Step 1: Write multi-stage Dockerfile**

```dockerfile
# Stage 1: system deps + Claude Code CLI (Node)
FROM node:20-slim AS node-base
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip \
      git ca-certificates curl \
      chromium \
      libpango-1.0-0 libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Stage 2: Python deps + app
FROM node-base AS app

WORKDIR /app

# Copy the submodule content (build context must include it)
COPY claude-seo/ /app/claude-seo/

# Python venv for app
RUN python3 -m venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Install claude-seo's Python deps (for scripts the skills invoke)
RUN pip install --no-cache-dir -r /app/claude-seo/requirements.txt

# Install wrapper's own deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy wrapper source (created in later tasks; empty placeholder OK for now)
COPY src/ /app/src/

# Chromium for Playwright (claude-seo scripts use it)
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright
RUN python -m playwright install chromium

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Entry point created in Task 11; placeholder for now
CMD ["python", "-c", "print('wrapper image OK')"]
```

- [ ] **Step 2: Create empty `src/wrapper/__init__.py` so Docker COPY doesn't fail**

```bash
mkdir -p src/wrapper
touch src/wrapper/__init__.py
```

- [ ] **Step 3: Build the image (smoke test)**

```bash
docker build -t claude-seo-wrapper:scaffold .
```

Expected: build succeeds; final line shows image tagged. Note image size with:

```bash
docker images claude-seo-wrapper:scaffold --format "{{.Size}}"
```

Expected: between 1.2 GB and 1.8 GB.

- [ ] **Step 4: Smoke-run the container**

```bash
docker run --rm claude-seo-wrapper:scaffold
```

Expected output: `wrapper image OK`

- [ ] **Step 5: Commit**

```bash
git add Dockerfile src/wrapper/__init__.py
git commit -m "chore: add minimal multi-stage Dockerfile that builds"
```

---

# Phase 2 — Configuration Module (Day 2 morning)

## Task 4: Config loader with fail-fast validation

**Files:**
- Create: `src/wrapper/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:

```python
import pytest
from wrapper.config import load_config, ConfigError


def test_load_config_returns_defaults_when_base_url_unset(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    cfg = load_config()

    assert cfg.base_url == "https://api.anthropic.com"
    assert cfg.api_key == "test-key"
    assert cfg.model is None


def test_load_config_respects_all_env_vars(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-real")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://proxy.example.com")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    cfg = load_config()

    assert cfg.base_url == "https://proxy.example.com"
    assert cfg.api_key == "sk-real"
    assert cfg.model == "claude-sonnet-4-6"


def test_load_config_fails_fast_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        load_config()


def test_load_config_fails_fast_when_api_key_empty(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")

    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        load_config()
```

`tests/__init__.py` and `tests/conftest.py` can be empty files for now (created so pytest finds the package).

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: 4 tests, all FAILED with `ModuleNotFoundError: No module named 'wrapper.config'`.

- [ ] **Step 3: Implement `src/wrapper/config.py`**

```python
"""Environment-backed configuration with fail-fast validation.

Reads three env vars and exposes them as a frozen dataclass. Any missing or empty
ANTHROPIC_API_KEY causes an immediate ConfigError — consistent with spec §4.4 step 1.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


class ConfigError(RuntimeError):
    """Raised at startup when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    model: Optional[str]


def load_config() -> Config:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "ANTHROPIC_API_KEY is required but missing or empty. "
            "Set it before starting the wrapper."
        )

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip() or "https://api.anthropic.com"
    model = os.environ.get("ANTHROPIC_MODEL", "").strip() or None

    return Config(base_url=base_url, api_key=api_key, model=model)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
PYTHONPATH=src pytest tests/test_config.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/wrapper/config.py tests/__init__.py tests/conftest.py tests/test_config.py
git commit -m "feat(config): env var loader with fail-fast validation"
```

---

# Phase 3 — URL Validator (Day 2 afternoon)

## Task 5: URL validator wrapping claude-seo's SSRF guard

**Files:**
- Create: `src/wrapper/url_validator.py`
- Create: `tests/test_url_validator.py`

**Context:** Spec §4.4 step 3 mandates reusing `claude-seo/scripts/google_auth.py::validate_url()` for SSRF protection. This module delegates SSRF checks to upstream and tightens to **https-only** on top (spec §5.1 says "HTTPS、非内网、能解析").

**Important — upstream contract (verified from source at `claude-seo/scripts/google_auth.py:366`):**
- Signature: `validate_url(url: str) -> bool`
- Returns `True` for valid public http/https URLs; `False` for anything else
- **Never raises** — it's a pure predicate
- Accepts both `http` and `https` (we enforce https-only in our wrapper)
- Blocks: non-http(s) schemes, missing hostname, `localhost` / `127.0.0.1` / `0.0.0.0` / `::1`, GCP metadata, RFC1918 private ranges

- [ ] **Step 1: Confirm upstream signature before coding**

```bash
grep -n "def validate_url" claude-seo/scripts/google_auth.py
```

Expected: `366:def validate_url(url: str) -> bool:`

If the line number or signature has drifted (upstream version change), **stop and read the full function body** before continuing.

- [ ] **Step 2: Write failing tests**

`tests/test_url_validator.py`:

```python
import pytest
from wrapper.url_validator import validate, InvalidURLError


@pytest.mark.parametrize("url", [
    "https://example.com",
    "https://example.com/path?q=1",
    "https://sub.example.com",
])
def test_validate_accepts_public_https(url):
    # validate() returns the original URL unchanged on success
    assert validate(url) == url


@pytest.mark.parametrize("url,reason", [
    ("http://example.com",           "http-not-https"),           # our wrapper tightens to https-only
    ("ftp://example.com",            "wrong-scheme"),             # upstream rejects
    ("https://localhost",            "loopback-hostname"),        # upstream rejects
    ("https://127.0.0.1",            "loopback-ip"),              # upstream rejects
    ("https://10.0.0.1",             "rfc1918-private"),          # upstream rejects
    ("https://169.254.169.254",      "link-local-metadata"),      # upstream rejects (is_link_local)
    ("not-a-url",                    "no-scheme"),                # upstream rejects
    ("",                             "empty"),                    # wrapper rejects before delegating
])
def test_validate_rejects_unsafe_url(url, reason):
    with pytest.raises(InvalidURLError):
        validate(url)
```

- [ ] **Step 3: Run to verify it fails**

```bash
PYTHONPATH=src pytest tests/test_url_validator.py -v
```

Expected: all FAILED with `ModuleNotFoundError`.

- [ ] **Step 4: Implement `src/wrapper/url_validator.py`**

```python
"""SSRF-safe URL validation.

Delegates the hard SSRF checks to claude-seo/scripts/google_auth.py::validate_url
(CLAUDE.md mandates reusing that function — we don't reimplement). Adds:
  - https-only enforcement (upstream accepts both http and https; MVP tightens)
  - InvalidURLError so callers don't catch bare ValueError
  - empty/non-string guard before delegating
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

# Insert claude-seo scripts dir on path so we can import google_auth by module name
_CLAUDE_SEO_SCRIPTS = Path(__file__).resolve().parents[2] / "claude-seo" / "scripts"
if str(_CLAUDE_SEO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_CLAUDE_SEO_SCRIPTS))

import google_auth  # type: ignore  # noqa: E402


class InvalidURLError(ValueError):
    """Raised when a submitted URL fails validation."""


def validate(url: str) -> str:
    """Return the URL unchanged if safe; raise InvalidURLError otherwise.

    Contract:
      - Input must be a non-empty string
      - Scheme must be 'https' (MVP tightening over upstream)
      - Upstream validate_url must return True (handles private/loopback/metadata)
    """
    if not isinstance(url, str) or not url:
        raise InvalidURLError(f"URL must be a non-empty string: {url!r}")

    scheme = urlparse(url).scheme
    if scheme != "https":
        raise InvalidURLError(f"URL must use https scheme, got {scheme!r}: {url!r}")

    # Upstream returns bool — True=safe, False=unsafe; it never raises.
    if not google_auth.validate_url(url):
        raise InvalidURLError(
            f"URL failed SSRF check (loopback / private / metadata / malformed): {url!r}"
        )
    return url
```

- [ ] **Step 5: Run tests — expect pass**

```bash
PYTHONPATH=src pytest tests/test_url_validator.py -v
```

Expected: all 11 parametrized cases pass (3 accept + 8 reject).

If any **accept** case raises (legal https URL rejected), upstream `validate_url` has become stricter — check if the hostname we picked resolves to a private IP from the dev machine. Swap the test host to `https://example.org`.

If any **reject** case is let through, upstream SSRF is weaker than documented — **stop and escalate**; spec §6 R1/R2 SSRF assumption is broken.

- [ ] **Step 6: Commit**

```bash
git add src/wrapper/url_validator.py tests/test_url_validator.py
git commit -m "feat(url): SSRF-safe URL validator wrapping claude-seo's validate_url"
```

---

# Phase 4 — Workspace Management (Day 3 morning)

## Task 6: Per-request workspace with symlink strategy

**Files:**
- Create: `src/wrapper/workspace.py`
- Create: `tests/test_workspace.py`

**Context:** Spec §4.4 step 4. Each request gets `/workspace/{job_id}/`. Inside: a `.claude/` dir with `skills/` and `agents/` as symlinks to `/app/claude-seo/skills/` and `/app/claude-seo/agents/`. Plus an `output/` dir where Claude SEO will write the report.

- [ ] **Step 1: Write failing tests**

`tests/test_workspace.py`:

```python
from pathlib import Path
import pytest
from wrapper.workspace import Workspace, WorkspaceError


def test_workspace_creates_expected_layout(tmp_path, monkeypatch):
    # Fake "installed" claude-seo locations
    fake_seo = tmp_path / "claude-seo"
    (fake_seo / "skills").mkdir(parents=True)
    (fake_seo / "agents").mkdir(parents=True)

    ws_root = tmp_path / "workspace"
    ws = Workspace(root=ws_root, claude_seo_dir=fake_seo)

    job_dir = ws.create("job-abc")

    assert job_dir == ws_root / "job-abc"
    assert (job_dir / ".claude" / "skills").is_symlink() or (job_dir / ".claude" / "skills").is_dir()
    assert (job_dir / ".claude" / "agents").is_symlink() or (job_dir / ".claude" / "agents").is_dir()
    assert (job_dir / "output").is_dir()


def test_workspace_cleanup_removes_everything(tmp_path):
    fake_seo = tmp_path / "claude-seo"
    (fake_seo / "skills").mkdir(parents=True)
    (fake_seo / "agents").mkdir(parents=True)

    ws = Workspace(root=tmp_path / "workspace", claude_seo_dir=fake_seo)
    job_dir = ws.create("job-xyz")
    assert job_dir.exists()

    ws.cleanup("job-xyz")
    assert not job_dir.exists()


def test_workspace_cleanup_is_idempotent(tmp_path):
    fake_seo = tmp_path / "claude-seo"
    (fake_seo / "skills").mkdir(parents=True)
    (fake_seo / "agents").mkdir(parents=True)
    ws = Workspace(root=tmp_path / "workspace", claude_seo_dir=fake_seo)

    ws.cleanup("never-created")  # must not raise


def test_workspace_rejects_job_id_with_path_traversal(tmp_path):
    fake_seo = tmp_path / "claude-seo"
    (fake_seo / "skills").mkdir(parents=True)
    (fake_seo / "agents").mkdir(parents=True)
    ws = Workspace(root=tmp_path / "workspace", claude_seo_dir=fake_seo)

    with pytest.raises(WorkspaceError):
        ws.create("../escape")
    with pytest.raises(WorkspaceError):
        ws.create("has/slash")
```

- [ ] **Step 2: Run to verify failure**

```bash
PYTHONPATH=src pytest tests/test_workspace.py -v
```

Expected: all FAILED with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/wrapper/workspace.py`**

```python
"""Per-request workspace lifecycle.

Creates /workspace/{job_id}/ with symlinked Claude SEO skills/agents and an
output dir. Cleanup is idempotent. Job IDs are constrained to safe characters
to prevent path traversal.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


_SAFE_JOB_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class WorkspaceError(ValueError):
    """Raised when workspace operations fail or inputs are unsafe."""


@dataclass
class Workspace:
    root: Path
    claude_seo_dir: Path

    def create(self, job_id: str) -> Path:
        if not _SAFE_JOB_ID.match(job_id):
            raise WorkspaceError(
                f"Unsafe job_id: {job_id!r}. Must match {_SAFE_JOB_ID.pattern}"
            )

        job_dir = self.root / job_id
        (job_dir / ".claude").mkdir(parents=True, exist_ok=True)
        (job_dir / "output").mkdir(parents=True, exist_ok=True)

        self._link_or_copy(
            self.claude_seo_dir / "skills",
            job_dir / ".claude" / "skills",
        )
        self._link_or_copy(
            self.claude_seo_dir / "agents",
            job_dir / ".claude" / "agents",
        )
        return job_dir

    def cleanup(self, job_id: str) -> None:
        if not _SAFE_JOB_ID.match(job_id):
            return  # silently ignore unsafe IDs on cleanup
        job_dir = self.root / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)

    @staticmethod
    def _link_or_copy(src: Path, dst: Path) -> None:
        if dst.exists() or dst.is_symlink():
            return
        try:
            os.symlink(src, dst, target_is_directory=True)
        except OSError:
            # Fallback to copy when symlinks are not permitted (rare on Linux)
            shutil.copytree(src, dst)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
PYTHONPATH=src pytest tests/test_workspace.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/wrapper/workspace.py tests/test_workspace.py
git commit -m "feat(workspace): per-request dir lifecycle with symlinked skills/agents"
```

---

# Phase 5 — Runner (Day 2 afternoon + Day 3)

## Task 7: Runner module with mocked SDK tests

**Files:**
- Create: `src/wrapper/runner.py`
- Create: `tests/test_runner.py`

**Context:** Spec §4.4 step 5. This module wraps `claude-agent-sdk.query()`. Unit tests use `unittest.mock` to avoid real LLM calls. Real end-to-end verification happens in Task 8.

> ⚠️ **MVP-only simplification (Phase 2 TODO)**: This module writes to `os.environ` — a **process-level** mutation. In MVP we run sync/single-request, so it's safe. When Phase 2 introduces concurrency (parallel FastAPI requests with different configs), this will cause config bleed between requests. At that point, migrate to per-call env isolation: either `ClaudeAgentOptions(env=...)` if the SDK supports it, or spawn a subprocess with explicit env.

- [ ] **Step 1: Configure pytest-asyncio (do this BEFORE writing async tests)**

Under `[tool.pytest.ini_options]` in `pyproject.toml`, add:

```toml
asyncio_mode = "auto"
```

Without this, async tests get silently skipped with a warning instead of running.

- [ ] **Step 2: Write failing tests**

`tests/test_runner.py`:

```python
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from wrapper.config import Config
from wrapper.runner import run_audit, RunnerError


@pytest.mark.asyncio
async def test_run_audit_invokes_sdk_with_expected_options(tmp_path):
    cfg = Config(base_url="https://api.test", api_key="k", model=None)
    job_dir = tmp_path / "job-1"
    job_dir.mkdir()

    fake_messages = [{"type": "assistant", "text": "partial"}]

    async def fake_query(**kwargs):
        for m in fake_messages:
            yield m

    with patch("wrapper.runner.query", side_effect=fake_query) as mock_query:
        messages = await run_audit(
            url="https://example.com",
            job_dir=job_dir,
            config=cfg,
        )

    assert messages == fake_messages
    mock_query.assert_called_once()
    call_kwargs = mock_query.call_args.kwargs
    assert call_kwargs["prompt"] == "/seo page https://example.com"
    assert call_kwargs["options"].cwd == str(job_dir)
    assert "Skill" in call_kwargs["options"].allowed_tools


@pytest.mark.asyncio
async def test_run_audit_propagates_sdk_errors(tmp_path):
    cfg = Config(base_url="https://api.test", api_key="k", model=None)
    job_dir = tmp_path / "job-2"
    job_dir.mkdir()

    async def boom(**kwargs):
        raise RuntimeError("SDK internal failure")
        yield  # pragma: no cover

    with patch("wrapper.runner.query", side_effect=boom):
        with pytest.raises(RunnerError, match="SDK internal failure"):
            await run_audit(url="https://example.com", job_dir=job_dir, config=cfg)
```

- [ ] **Step 3: Run to verify failure**

```bash
PYTHONPATH=src pytest tests/test_runner.py -v
```

Expected: FAIL with `ModuleNotFoundError: wrapper.runner`.

- [ ] **Step 4: Implement `src/wrapper/runner.py`**

```python
"""claude-agent-sdk invocation wrapper.

Centralizes how we call the SDK so callers don't need to know its shape.
Exposes `run_audit(url, job_dir, config)` returning the raw message list.
Output aggregation (file-first, message-fallback) lives in output_parser.py.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from claude_agent_sdk import ClaudeAgentOptions, query

from .config import Config


class RunnerError(RuntimeError):
    """Raised when the SDK invocation itself fails."""


_ALLOWED_TOOLS = ["Skill", "Read", "Write", "Bash", "Glob", "Grep"]
_MAX_TURNS = 30


async def run_audit(url: str, job_dir: Path, config: Config) -> List[Dict[str, Any]]:
    # ⚠️ MVP-only: process-level env mutation (see task header note).
    # Ensures the child process (Claude Code CLI) sees our API config.
    # Spec §6 R6.1 requires this passthrough be verified Day 2 (Task 8).
    # Phase 2 must move to per-call env isolation before enabling concurrency.
    os.environ["ANTHROPIC_BASE_URL"] = config.base_url
    os.environ["ANTHROPIC_API_KEY"] = config.api_key
    if config.model:
        os.environ["ANTHROPIC_MODEL"] = config.model

    options = ClaudeAgentOptions(
        cwd=str(job_dir),
        setting_sources=["project"],
        allowed_tools=_ALLOWED_TOOLS,
        max_turns=_MAX_TURNS,
    )

    messages: List[Dict[str, Any]] = []
    try:
        async for message in query(prompt=f"/seo page {url}", options=options):
            messages.append(message if isinstance(message, dict) else {"raw": str(message)})
    except Exception as e:
        raise RunnerError(f"claude-agent-sdk failed: {e}") from e
    return messages
```

- [ ] **Step 5: Run tests — expect pass**

```bash
PYTHONPATH=src pytest tests/test_runner.py -v
```

Expected: both tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/wrapper/runner.py tests/test_runner.py pyproject.toml
git commit -m "feat(runner): claude-agent-sdk wrapper with mocked-SDK tests"
```

---

## Task 8: Manual smoke test — real SDK call with env-passthrough verification

**Context:** Spec §6 R6.1 — we MUST prove the env vars reach Claude Code CLI before trusting subsequent tasks. This is a manual check, not an automated test.

- [ ] **Step 1: Install SDK + Claude Code locally (outside Docker)**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install -g @anthropic-ai/claude-code
```

- [ ] **Step 2: Create the `scripts/` directory and write a tiny check script (not committed)**

```bash
mkdir -p scripts
```

`scripts/smoke_sdk.py` (gitignored via `scripts/smoke_*.py` rule in Task 1):

```python
import asyncio, os
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    os.environ["ANTHROPIC_BASE_URL"] = os.environ["SMOKE_BASE_URL"]
    os.environ["ANTHROPIC_API_KEY"] = os.environ["SMOKE_API_KEY"]
    async for m in query(prompt="Reply with exactly: PONG", options=ClaudeAgentOptions()):
        print(m)

asyncio.run(main())
```

- [ ] **Step 3: Run with the operator-supplied endpoint**

```bash
SMOKE_BASE_URL="https://<operator-endpoint>" \
SMOKE_API_KEY="sk-..." \
python scripts/smoke_sdk.py
```

Expected: messages stream from the endpoint; at least one contains "PONG".

- [ ] **Step 4: Diagnose if PONG is not in output**

Possible causes and next steps:
- SDK scrubs env vars → try passing via `ClaudeAgentOptions(env={...})` if the SDK version supports it; otherwise wrap invocation in a subprocess with explicit env.
- Endpoint rejects the request → verify endpoint accepts Claude API format directly (send a raw `curl` to it).
- If neither works, **stop here**. The spec's core assumption is broken; consult with the user before continuing.

- [ ] **Step 5: No commit for this task** (script is gitignored). Record the outcome in a `notes/day2-smoke.md` (also gitignored) for the final test report.

---

## Task 9: Manual smoke test — Claude SEO `/seo page` via SDK

**Context:** Verifies Claude Code can load Claude SEO's Skills from a workspace directory. Still manual, before wiring to FastAPI.

- [ ] **Step 1: Set up a workspace manually**

```bash
mkdir -p /tmp/seo-smoke/.claude
ln -s $(pwd)/claude-seo/skills /tmp/seo-smoke/.claude/skills
ln -s $(pwd)/claude-seo/agents /tmp/seo-smoke/.claude/agents
mkdir -p /tmp/seo-smoke/output
```

- [ ] **Step 2: Write a smoke runner (`scripts/` already exists from Task 8)**

`scripts/smoke_seo_page.py` (gitignored):

```python
import asyncio, os
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    os.environ["ANTHROPIC_BASE_URL"] = os.environ["SMOKE_BASE_URL"]
    os.environ["ANTHROPIC_API_KEY"] = os.environ["SMOKE_API_KEY"]
    opts = ClaudeAgentOptions(
        cwd="/tmp/seo-smoke",
        setting_sources=["project"],
        allowed_tools=["Skill", "Read", "Write", "Bash", "Glob", "Grep"],
        max_turns=30,
    )
    async for m in query(prompt="/seo page https://example.com", options=opts):
        print(m)

asyncio.run(main())
```

- [ ] **Step 3: Run and observe**

```bash
SMOKE_BASE_URL=... SMOKE_API_KEY=... python scripts/smoke_seo_page.py > /tmp/seo-smoke/run.log
```

Expected: run completes within 3 minutes; `/tmp/seo-smoke/output/` contains at least one `.md` file OR the message stream contains a Markdown block with headings like `# SEO` or `## Recommendations`.

- [ ] **Step 4: Decide symlink vs. copy**

If the SDK refused to load skills through symlinks, redo Step 1 with `cp -r` instead of `ln -s`. Whichever works, record the choice for Task 11.

- [ ] **Step 5: Record outcome AND first real SDK message shape in `notes/day3-smoke.md`** (gitignored).

Include:
- Token usage, elapsed time, quality impression
- **Full `repr()` of the first assistant message dict** printed by the smoke script — this is the ground truth for Task 10's `_extract_text` parsing. Task 10 reads this note to know exactly which keys to look for instead of guessing.

---

# Phase 6 — Output Parser (Day 3 evening)

## Task 10: Output parser with file-first + message-stream fallback

**Files:**
- Create: `src/wrapper/output_parser.py`
- Create: `tests/fixtures/sample_report.md`
- Create: `tests/fixtures/empty_output/.gitkeep`
- Create: `tests/test_output_parser.py`

**Context:** Spec §4.4 step 6 — primary strategy reads `{job_dir}/output/*.md`; fallback extracts from SDK message stream.

- [ ] **Step 1: Create fixture files**

```bash
mkdir -p tests/fixtures/empty_output
touch tests/fixtures/empty_output/.gitkeep
```

`tests/fixtures/sample_report.md`:

```markdown
# SEO Analysis for example.com

## Priority Recommendations

1. Add meta description
2. Fix H1 structure
```

- [ ] **Step 2: Write failing tests**

`tests/test_output_parser.py`:

```python
from pathlib import Path
import pytest
from wrapper.output_parser import extract_report, EmptyReportError


FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_prefers_output_dir_file(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    (output / "report.md").write_text((FIXTURES / "sample_report.md").read_text(), encoding="utf-8")
    messages = [{"type": "assistant", "text": "ignored"}]

    report = extract_report(job_dir=tmp_path, messages=messages)

    assert "SEO Analysis for example.com" in report


def test_extract_falls_back_to_messages_when_output_empty(tmp_path):
    (tmp_path / "output").mkdir()
    messages = [
        {"type": "assistant", "text": "# Report\n\nfallback content"},
    ]

    report = extract_report(job_dir=tmp_path, messages=messages)

    assert "fallback content" in report


def test_extract_raises_when_both_sources_empty(tmp_path):
    (tmp_path / "output").mkdir()
    with pytest.raises(EmptyReportError):
        extract_report(job_dir=tmp_path, messages=[])


def test_extract_concatenates_multiple_output_files(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    (output / "01.md").write_text("# A\nalpha")
    (output / "02.md").write_text("# B\nbeta")

    report = extract_report(job_dir=tmp_path, messages=[])

    assert "alpha" in report and "beta" in report
```

- [ ] **Step 3: Run to verify failure**

```bash
PYTHONPATH=src pytest tests/test_output_parser.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement `src/wrapper/output_parser.py`**

```python
"""Extract the final report from a job's workspace.

Primary: concatenate *.md files from {job_dir}/output/ in sorted order.
Fallback: scan SDK message stream for assistant text blocks.
Raises EmptyReportError if neither source yields content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List


class EmptyReportError(RuntimeError):
    """Raised when no report content was produced."""


def extract_report(job_dir: Path, messages: Iterable[Dict[str, Any]]) -> str:
    output_dir = job_dir / "output"
    if output_dir.is_dir():
        md_files = sorted(output_dir.glob("*.md"))
        if md_files:
            parts = [p.read_text(encoding="utf-8") for p in md_files]
            joined = "\n\n".join(parts).strip()
            if joined:
                return joined

    # Fallback: message stream
    collected: List[str] = []
    for m in messages:
        text = _extract_text(m)
        if text:
            collected.append(text)
    joined = "\n\n".join(collected).strip()
    if joined:
        return joined

    raise EmptyReportError(
        f"No report content in {output_dir} and no assistant text in messages"
    )


def _extract_text(message: Dict[str, Any]) -> str:
    if not isinstance(message, dict):
        return ""
    # Try common SDK shapes; be liberal in what we accept
    if message.get("type") == "assistant" and isinstance(message.get("text"), str):
        return message["text"]
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                pieces.append(block["text"])
        return "\n".join(pieces)
    return ""
```

- [ ] **Step 5: Run tests — expect pass**

```bash
PYTHONPATH=src pytest tests/test_output_parser.py -v
```

Expected: all 4 pass.

- [ ] **Step 6: Commit**

```bash
git add src/wrapper/output_parser.py tests/fixtures/ tests/test_output_parser.py
git commit -m "feat(output): file-first + message-stream fallback report extractor"
```

---

# Phase 7 — FastAPI Application (Day 4)

## Task 11: POST /v1/audit endpoint

**Files:**
- Create: `src/wrapper/api.py`
- Create: `tests/test_api.py`

**Context:** Spec §4.4 full lifecycle. Wires config → URL validation → workspace → runner → output parser → response. One endpoint only.

> **Phase 2 TODO (non-blocking)**: `@app.on_event("startup")` is deprecated in newer FastAPI versions in favor of the `lifespan` context manager. MVP uses the old form because it's simpler and still works; migrate when touching this file in Phase 2.

- [ ] **Step 1: Write failing tests**

`tests/test_api.py`:

```python
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path / "workspace"))
    monkeypatch.setenv("CLAUDE_SEO_DIR", str(tmp_path / "claude-seo"))
    # Provide the fake claude-seo structure so workspace.Workspace doesn't fail
    (tmp_path / "claude-seo" / "skills").mkdir(parents=True)
    (tmp_path / "claude-seo" / "agents").mkdir(parents=True)

    from wrapper import api
    return TestClient(api.app)


def test_audit_returns_report_on_success(client, tmp_path):
    async def fake_runner(url, job_dir, config):
        # Simulate claude-seo writing the report to output/
        (job_dir / "output").mkdir(parents=True, exist_ok=True)
        (job_dir / "output" / "report.md").write_text("# OK\ngreat findings")
        return [{"type": "assistant", "text": "..."}]

    with patch("wrapper.api.run_audit", side_effect=fake_runner):
        r = client.post("/v1/audit", json={"url": "https://example.com"})

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "great findings" in body["report"]


def test_audit_rejects_invalid_url(client):
    r = client.post("/v1/audit", json={"url": "http://localhost"})
    assert r.status_code == 400
    assert "InvalidURL" in r.text or "invalid" in r.text.lower()


def test_audit_returns_error_when_runner_fails(client):
    async def boom(url, job_dir, config):
        raise RuntimeError("sdk down")

    with patch("wrapper.api.run_audit", side_effect=boom):
        r = client.post("/v1/audit", json={"url": "https://example.com"})

    assert r.status_code == 500
    body = r.json()
    assert body["status"] == "error"
```

- [ ] **Step 2: Run to verify failure**

```bash
PYTHONPATH=src pytest tests/test_api.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/wrapper/api.py`**

```python
"""FastAPI HTTP surface — one endpoint: POST /v1/audit.

Lifecycle (spec §4.4):
  1. Load config (on import via startup hook).
  2. Validate URL.
  3. Build workspace.
  4. Call runner.
  5. Extract report.
  6. Cleanup.
  7. Return JSON.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import Config, load_config
from .output_parser import EmptyReportError, extract_report
from .runner import RunnerError, run_audit
from .url_validator import InvalidURLError, validate
from .workspace import Workspace, WorkspaceError

logger = logging.getLogger(__name__)
app = FastAPI(title="Claude SEO Wrapper", version="0.1.0")


class AuditRequest(BaseModel):
    url: str = Field(..., description="Target URL to analyze")


class AuditResponse(BaseModel):
    status: str
    report: str | None = None
    error: str | None = None
    elapsed_ms: int
    job_id: str


_config: Config | None = None
_workspace: Workspace | None = None


@app.on_event("startup")
def _startup() -> None:
    global _config, _workspace
    _config = load_config()
    _workspace = Workspace(
        root=Path(os.environ.get("WORKSPACE_ROOT", "/workspace")),
        claude_seo_dir=Path(os.environ.get("CLAUDE_SEO_DIR", "/app/claude-seo")),
    )
    logger.info("Wrapper ready. base_url=%s", _config.base_url)


@app.post("/v1/audit", response_model=AuditResponse)
async def audit(req: AuditRequest) -> AuditResponse:
    assert _config is not None and _workspace is not None, "startup did not run"

    job_id = uuid.uuid4().hex[:16]
    started = time.monotonic()

    try:
        url = validate(req.url)
    except InvalidURLError as e:
        raise HTTPException(status_code=400, detail=f"InvalidURL: {e}")

    try:
        job_dir = _workspace.create(job_id)
    except WorkspaceError as e:
        raise HTTPException(status_code=500, detail=f"WorkspaceError: {e}")

    try:
        messages = await run_audit(url=url, job_dir=job_dir, config=_config)
    except RunnerError as e:
        _workspace.cleanup(job_id)
        logger.exception("run_audit failed")
        return AuditResponse(
            status="error",
            error=str(e),
            elapsed_ms=int((time.monotonic() - started) * 1000),
            job_id=job_id,
        )
    except Exception as e:  # noqa: BLE001
        _workspace.cleanup(job_id)
        logger.exception("unexpected runner failure")
        return AuditResponse(
            status="error",
            error=f"unexpected: {e}",
            elapsed_ms=int((time.monotonic() - started) * 1000),
            job_id=job_id,
        )

    try:
        report = extract_report(job_dir=job_dir, messages=messages)
    except EmptyReportError as e:
        _workspace.cleanup(job_id)
        return AuditResponse(
            status="error",
            error=f"EmptyReport: {e}",
            elapsed_ms=int((time.monotonic() - started) * 1000),
            job_id=job_id,
        )

    _workspace.cleanup(job_id)
    return AuditResponse(
        status="ok",
        report=report,
        elapsed_ms=int((time.monotonic() - started) * 1000),
        job_id=job_id,
    )
```

- [ ] **Step 4: Run tests — expect pass**

```bash
PYTHONPATH=src pytest tests/test_api.py -v
```

Expected: all 3 pass. Error-path tests should pass because FastAPI converts `HTTPException` into proper JSON automatically; if 500 path test fails, adjust the `return` vs `raise` pattern to be consistent.

- [ ] **Step 5: Commit**

```bash
git add src/wrapper/api.py tests/test_api.py
git commit -m "feat(api): POST /v1/audit endpoint with full lifecycle"
```

---

## Task 12: Local end-to-end test (without Docker)

- [ ] **Step 1: Start the server**

```bash
PYTHONPATH=src \
WORKSPACE_ROOT=/tmp/seo-workspace \
CLAUDE_SEO_DIR=$(pwd)/claude-seo \
ANTHROPIC_BASE_URL=<operator URL> \
ANTHROPIC_API_KEY=<operator key> \
uvicorn wrapper.api:app --host 127.0.0.1 --port 8000
```

- [ ] **Step 2: From another terminal, POST a real URL**

```bash
curl -s -X POST http://127.0.0.1:8000/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}' | jq .
```

Expected: within 1–3 minutes, JSON response with `"status": "ok"` and a `report` field containing a Markdown-formatted SEO analysis of example.com.

- [ ] **Step 3: Test URL rejection path**

```bash
curl -s -X POST http://127.0.0.1:8000/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"http://localhost"}' | jq .
```

Expected: HTTP 400 with `InvalidURL` message.

- [ ] **Step 4: Auto-log both runs to `notes/day4-e2e.md`** (gitignored)

```bash
mkdir -p notes
{
  echo "=== Happy path $(date -Iseconds) ==="
  curl -s -X POST http://127.0.0.1:8000/v1/audit \
    -H "Content-Type: application/json" \
    -d '{"url":"https://example.com"}' | jq .
  echo
  echo "=== Rejection path $(date -Iseconds) ==="
  curl -s -X POST http://127.0.0.1:8000/v1/audit \
    -H "Content-Type: application/json" \
    -d '{"url":"http://localhost"}' | jq .
} | tee -a notes/day4-e2e.md
```

Also append manually: elapsed time observations, any warnings from server logs, first 20 lines of the report.

- [ ] **Step 5: No commit needed** (smoke testing, not code changes).

---

# Phase 8 — Dockerization (Day 4 evening / Day 5 morning)

## Task 13: Finalize Dockerfile entry point

**Files:**
- Modify: `Dockerfile` (change the placeholder `CMD`)

- [ ] **Step 1: Replace the final `CMD` line**

Change:

```dockerfile
CMD ["python", "-c", "print('wrapper image OK')"]
```

to:

```dockerfile
CMD ["uvicorn", "wrapper.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Rebuild the image**

```bash
docker build -t claude-seo-wrapper:e2e .
```

Expected: build succeeds. Record final image size.

- [ ] **Step 3: Run the container with env vars**

```bash
docker run --rm -p 8000:8000 \
  -e ANTHROPIC_BASE_URL=<operator URL> \
  -e ANTHROPIC_API_KEY=<operator key> \
  claude-seo-wrapper:e2e
```

Expected: logs show `Wrapper ready. base_url=...`; server listens on 8000.

- [ ] **Step 4: Repeat the `curl` tests from Task 12, Step 2 + 3**

Expected: same successful and failing responses. If the container has trouble but local Python did not, **stop and investigate** — common causes: missing Chromium in image, permission issues on `/workspace`, PATH issues with Claude Code CLI.

- [ ] **Step 5: Commit the Dockerfile change**

```bash
git add Dockerfile
git commit -m "chore(docker): wire uvicorn as container entrypoint"
```

---

## Task 14: Wire workspace root + verify container-level env passthrough

**Files:**
- Modify: `Dockerfile` — ensure `/workspace` exists and is writable

- [ ] **Step 1: Add workspace dir creation to Dockerfile**

Before the `EXPOSE 8000` line, add:

```dockerfile
RUN mkdir -p /workspace && chmod 777 /workspace
ENV WORKSPACE_ROOT=/workspace
ENV CLAUDE_SEO_DIR=/app/claude-seo
```

- [ ] **Step 2: Rebuild and rerun**

```bash
docker build -t claude-seo-wrapper:e2e .
docker run --rm -p 8000:8000 \
  -e ANTHROPIC_BASE_URL=... \
  -e ANTHROPIC_API_KEY=... \
  claude-seo-wrapper:e2e
```

- [ ] **Step 3: Run `curl` with 5 different URLs (recorded in `notes/day5-local-eval.md`)**

```bash
for url in \
  "https://example.com" \
  "https://www.alibaba.com" \
  "https://www.wikipedia.org" \
  "https://stripe.com/pricing" \
  "https://news.ycombinator.com"; do
  echo "=== $url ==="
  curl -s -X POST http://127.0.0.1:8000/v1/audit \
    -H "Content-Type: application/json" \
    -d "{\"url\":\"$url\"}" | jq -r '.status, .elapsed_ms'
done
```

Expected: each returns `ok` with elapsed_ms ≤ 180000 (3 min).

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "chore(docker): pre-create /workspace and default env vars"
```

---

# Phase 9 — Local Evaluation (Day 5)

## Task 15: 5-URL × 3-run evaluation + report

**Files:**
- Create: `notes/day5-local-eval.md` (gitignored scratch)
- Output: scored data for final report

- [ ] **Step 1: Run each of the 5 URLs three times**

Use the loop from Task 14 Step 3, wrapped in another loop that runs it 3 times. Capture each full JSON response to a file:

```bash
mkdir -p /tmp/eval-local
for i in 1 2 3; do
  for url in url1 url2 url3 url4 url5; do
    curl -s -X POST http://127.0.0.1:8000/v1/audit \
      -H "Content-Type: application/json" \
      -d "{\"url\":\"$url\"}" \
      > "/tmp/eval-local/run${i}_$(echo $url | sha1sum | cut -c1-8).json"
  done
done
```

- [ ] **Step 2: For each run, record**
  - elapsed_ms
  - Report quality score (use spec §5.1 10-point rubric)
  - Token count if the operator endpoint returns it (otherwise note "unknown")
  - Any error / partial report

- [ ] **Step 3: Compute statistics**
  - P50 / P95 elapsed time
  - Mean quality score
  - Pass rate (non-error runs / total)

- [ ] **Step 4: Fail-fast check**

If ANY of the following is true, stop and escalate before Phase 10:
- Pass rate < 80%
- P95 elapsed > 180s
- Mean quality < 6/10

These violate G1/G2/G3 already — no point deploying to CF until local works.

- [ ] **Step 5: No commit** — results go into `notes/day5-local-eval.md` which will feed the final test report (Task 19).

---

# Phase 10 — Cloudflare Containers Deployment (Day 6–7)

## Task 16: Set up Cloudflare Worker and Durable Object routing

**Files (in a new `cf/` subdir):**
- Create: `cf/wrangler.toml`
- Create: `cf/src/worker.ts`

**Context:** CF Containers are fronted by a Worker + a Durable Object. This task sets up the minimum viable Worker that forwards `POST /v1/audit` to the container.

> ⚠️ **Before starting this task** — open https://developers.cloudflare.com/containers/ and verify the current `[[containers]]` TOML schema + `DurableObject` + `container` API surface. CF Containers is public beta and schema fields (`class_name`, `image`, `instance_type`, `max_instances`) have been renamed in past releases. The snippets below reflect **2026-04 state at spec writing**; if `wrangler deploy` fails with a schema error, checking current docs is the first debug step.

- [ ] **Step 1: Install Wrangler**

```bash
npm install -g wrangler
wrangler --version
```

Expected: version ≥ 3.0.

- [ ] **Step 2: Write `cf/wrangler.toml`**

```toml
name = "claude-seo-wrapper-proxy"
main = "src/worker.ts"
compatibility_date = "2026-02-01"

[[containers]]
class_name = "AuditContainer"
image = "./.."   # build context points at repo root (Dockerfile)
instance_type = "standard-1"   # 1 GB RAM per spec §11
max_instances = 5

[[durable_objects.bindings]]
name = "AUDIT_DO"
class_name = "AuditContainer"

[[migrations]]
tag = "v1"
new_sqlite_classes = ["AuditContainer"]
```

(Exact `instance_type` names may differ; confirm against current CF docs during Day 6.)

- [ ] **Step 3: Write `cf/src/worker.ts`**

```typescript
import { DurableObject } from "cloudflare:workers";

export interface Env {
  AUDIT_DO: DurableObjectNamespace<AuditContainer>;
  ANTHROPIC_BASE_URL: string;
  ANTHROPIC_API_KEY: string;
  ANTHROPIC_MODEL?: string;
}

export class AuditContainer extends DurableObject<Env> {
  container: globalThis.Container;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    this.container = ctx.container!;
  }

  async fetch(request: Request): Promise<Response> {
    if (!this.container.running) {
      await this.container.start({
        envVars: {
          ANTHROPIC_BASE_URL: this.env.ANTHROPIC_BASE_URL,
          ANTHROPIC_API_KEY: this.env.ANTHROPIC_API_KEY,
          ANTHROPIC_MODEL: this.env.ANTHROPIC_MODEL ?? "",
        },
      });
    }
    return this.container.getTcpPort(8000).fetch(request);
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname !== "/v1/audit" || request.method !== "POST") {
      return new Response("Not Found", { status: 404 });
    }
    const id = env.AUDIT_DO.idFromName("singleton");
    const stub = env.AUDIT_DO.get(id);
    return stub.fetch(request);
  },
};
```

- [ ] **Step 4: Set secrets in CF**

```bash
cd cf
wrangler secret put ANTHROPIC_API_KEY
wrangler secret put ANTHROPIC_BASE_URL
# Optional:
# wrangler secret put ANTHROPIC_MODEL
```

- [ ] **Step 5: Commit**

```bash
git add cf/wrangler.toml cf/src/worker.ts
git commit -m "feat(cf): Worker + Durable Object routing to container"
```

---

## Task 17: Deploy to Cloudflare Containers

- [ ] **Step 1: Deploy**

```bash
cd cf
wrangler deploy
```

Expected: deploy succeeds; prints a `*.workers.dev` URL.

- [ ] **Step 2: First request (triggers container start)**

```bash
curl -v -X POST https://<your-worker>.workers.dev/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

Expected: first request may take extra seconds (cold start); subsequent within same minute are fast.

- [ ] **Step 3: If startup fails, inspect logs**

```bash
wrangler tail
```

Look for Python startup errors, missing env vars, or image pull failures. Common fixes:
- Image too large → trim Dockerfile (move Chromium to cache mount; remove dev deps)
- Timeout too tight → adjust per CF docs
- Env var missing → re-run `wrangler secret put`

- [ ] **Step 4: Record first successful response** — status, elapsed_ms, report excerpt — in `notes/day6-cf-deploy.md`.

---

## Task 18: Repeat 5-URL × 3-run evaluation on CF

- [ ] **Step 1: Copy Task 15's loop, targeting the CF URL**

```bash
BASE=https://<your-worker>.workers.dev
# (same loops as Task 15, swapping 127.0.0.1:8000 for $BASE)
```

- [ ] **Step 2: Compute same stats as Task 15**

- [ ] **Step 3: Apply the absolute pass thresholds (same as Task 15 Step 4)**

  CF must meet ALL of these, on its own (not just "relatively close to local"):
  - Pass rate ≥ 80%
  - P95 elapsed ≤ 3 minutes (180000 ms)
  - Mean quality ≥ 6/10

  AND the CF-vs-local comparison (spec §5.1 Stage B):
  - Elapsed time ≤ +30% over local p95 (cold-start budget)
  - Report content diff from local ≤ 5% (use a simple word-count or line-count diff)
  - Quality score must not regress vs. local

- [ ] **Step 4: If any check fails, stop and escalate** — do NOT proceed to Go/No-Go with failing CF data.

- [ ] **Step 5: Results go into `notes/day7-cf-eval.md`**

---

# Phase 11 — Final Report & Decision (Day 8–10)

## Task 19: Compile the MVP test report

**Files:**
- Create: `docs/mvp-test-report.md` (committed — this IS a deliverable per spec §9 D5)

- [ ] **Step 1: Write `docs/mvp-test-report.md` with these sections**

```markdown
# Claude SEO SaaS MVP — Test Report

**Date:** <YYYY-MM-DD>
**Spec:** docs/superpowers/specs/2026-04-21-mvp-prototype-design.md
**Spec version:** v2 (post-feedback)

## Executive Summary

- G1 (both envs work): PASS / FAIL
- G2 (p95 ≤ 3 min): PASS / FAIL — actual: _ s
- G3 (cost ≤ 5 CNY): PASS / FAIL — actual: _ CNY
- **Go/No-Go:** Go / No-Go (see §7)

## Environment

- Wrapper image: `<tag>` (size: _ GB)
- Claude SEO version: v1.7.2
- Endpoint: <redacted>
- Model (if reported): <name>

## Local Results (Phase 9 / Task 15)

Table: URL, run#, status, elapsed_ms, quality (1–10), notes.

## Cloudflare Results (Phase 10 / Task 18)

Same table shape as above.

## Observations

- What surprised us
- What broke and how we fixed it (including Day 2 env passthrough outcome and Day 3 symlink decision)
- Cost / token data

## Risks Surfaced

Reference the risk register in spec §6 — which risks materialized, which did not.

## Go / No-Go Decision

Per spec §5.2. If any of G1/G2/G3 failed, state which and what's needed to re-attempt.

## Phase 2 Recommendations

3–5 bullets on what to tackle next, grounded in what we observed.
```

- [ ] **Step 2: Fill in all `<...>` placeholders from `notes/*.md` files**

- [ ] **Step 3: Commit the report**

```bash
git add docs/mvp-test-report.md
git commit -m "docs: MVP test report with Go/No-Go decision"
```

---

## Task 20: Final deliverables checklist

- [ ] **Step 1: Verify all deliverables per spec §9**
  - D1: Wrapper repo on GitHub (private) — push `main` branch
  - D2: Dockerfile — in repo
  - D3: README — env var contract + docker run example
  - D4: CF deploy guide — `docs/cf-deploy.md` (write a short one if missing)
  - D5: Test report — `docs/mvp-test-report.md`
  - D6: Go/No-Go decision — last section of D5

- [ ] **Step 2: If a deliverable is missing, create it and commit**

- [ ] **Step 3: Push to GitHub**

```bash
# Create private repo via GitHub UI first; then:
git remote add origin git@github.com:<user>/claude-seo-wrapper.git
git push -u origin main
```

- [ ] **Step 4: Tag the MVP completion commit**

```bash
git tag -a v0.1.0-mvp -m "MVP prototype complete; see docs/mvp-test-report.md"
git push origin v0.1.0-mvp
```

---

## Done

If all checkboxes are ticked and the test report says Go, MVP is proved. Hand the repo + report to the user; next conversation brainstorms Phase 2 (multi-tenant, async queue, etc.) based on what was actually learned.
