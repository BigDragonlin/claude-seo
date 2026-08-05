#!/usr/bin/env python3
"""Validate the local Codex plugin package without third-party dependencies.

This repository is primarily maintained upstream for Claude Code. The Codex
packaging layer is intentionally small, so this checker focuses on the parts
Codex needs to discover the plugin safely:

1. `.codex-plugin/plugin.json` must be valid and complete enough for Codex.
2. The declared `skills` path must point to the repository's `skills/` folder.
3. Every discovered `SKILL.md` must have basic frontmatter with `name` and
   `description`.

The script uses only Python's standard library. That keeps local verification
working on a fresh macOS checkout where PyYAML may not be installed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / ".codex-plugin" / "plugin.json"
TODO_MARKER = "[TODO:"
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
SKILL_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,62}[a-z0-9]$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def main() -> int:
    """Run all Codex plugin checks and print a short report."""

    errors: list[str] = []
    manifest = load_manifest(errors)
    if manifest is not None:
        reject_todo_markers(manifest, "$", errors)
        validate_manifest(manifest, errors)
        validate_skill_files(errors)

    if errors:
        print("Codex plugin validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Codex plugin validation passed")
    print(f"  manifest: {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"  skills:   {len(find_skill_files())} SKILL.md files checked")
    return 0


def load_manifest(errors: list[str]) -> dict[str, Any] | None:
    """Read `.codex-plugin/plugin.json` as a JSON object."""

    if not MANIFEST_PATH.is_file():
        errors.append("missing .codex-plugin/plugin.json")
        return None

    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f".codex-plugin/plugin.json is not valid JSON: {exc}")
        return None

    if not isinstance(payload, dict):
        errors.append(".codex-plugin/plugin.json must contain a JSON object")
        return None

    return payload


def validate_manifest(manifest: dict[str, Any], errors: list[str]) -> None:
    """Validate the Codex plugin manifest fields used by this package."""

    allowed_keys = {
        "id",
        "name",
        "version",
        "description",
        "skills",
        "apps",
        "mcpServers",
        "interface",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
    }
    reject_unknown_fields(manifest, allowed_keys, "plugin.json", errors)

    require_string(manifest, "name", errors)
    version = require_string(manifest, "version", errors)
    if version and SEMVER_RE.fullmatch(version) is None:
        errors.append("plugin.json field version must be strict semver")
    require_string(manifest, "description", errors)

    author = manifest.get("author")
    if not isinstance(author, dict):
        errors.append("plugin.json field author must be an object")
    else:
        reject_unknown_fields(author, {"name", "email", "url"}, "author", errors)
        require_string(author, "name", errors, prefix="author")
        validate_optional_https_url(author, "url", errors, prefix="author")

    skills_path = manifest.get("skills")
    if normalize_relative_path(skills_path) != "skills":
        errors.append("plugin.json field skills must resolve to ./skills/")
    elif not (REPO_ROOT / "skills").is_dir():
        errors.append("plugin.json field skills points to a missing skills directory")

    for companion_key in ("apps", "mcpServers"):
        if companion_key in manifest:
            errors.append(
                f"plugin.json field {companion_key} should not be present "
                "until the matching companion manifest exists"
            )

    validate_interface(manifest.get("interface"), errors)


def validate_interface(value: Any, errors: list[str]) -> None:
    """Validate user-facing Codex plugin metadata."""

    if not isinstance(value, dict):
        errors.append("plugin.json field interface must be an object")
        return

    allowed_keys = {
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "websiteURL",
        "privacyPolicyURL",
        "termsOfServiceURL",
        "brandColor",
        "composerIcon",
        "logo",
        "screenshots",
        "defaultPrompt",
        "default_prompt",
    }
    reject_unknown_fields(value, allowed_keys, "interface", errors)

    for key in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
    ):
        require_string(value, key, errors, prefix="interface")

    capabilities = value.get("capabilities")
    if not isinstance(capabilities, list) or not all(
        isinstance(item, str) and item.strip() for item in capabilities
    ):
        errors.append("plugin.json field interface.capabilities must be an array of strings")

    prompts = value.get("defaultPrompt", value.get("default_prompt"))
    if not isinstance(prompts, list) or not prompts:
        errors.append("plugin.json field interface.defaultPrompt must be a non-empty array")
    elif not all(isinstance(item, str) and item.strip() for item in prompts):
        errors.append("plugin.json field interface.defaultPrompt must contain strings")

    for key in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        validate_optional_https_url(value, key, errors, prefix="interface")


def validate_skill_files(errors: list[str]) -> None:
    """Check each SKILL.md has the minimum Codex-discovery fields."""

    skill_files = find_skill_files()
    if not skill_files:
        errors.append("no SKILL.md files found under skills/ or extensions/")
        return

    for path in skill_files:
        relpath = path.relative_to(REPO_ROOT)
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if not match:
            errors.append(f"{relpath} must start with YAML frontmatter")
            continue

        frontmatter = parse_simple_frontmatter(match.group(1))
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not name:
            errors.append(f"{relpath} frontmatter is missing name")
        elif SKILL_NAME_RE.match(name) is None:
            errors.append(f"{relpath} frontmatter name is not kebab-case: {name}")
        if not description:
            errors.append(f"{relpath} frontmatter is missing description")


def find_skill_files() -> list[Path]:
    """Find core and extension skill manifests."""

    paths: list[Path] = []
    for folder in ("skills", "extensions"):
        root = REPO_ROOT / folder
        if root.is_dir():
            paths.extend(root.rglob("SKILL.md"))
    return sorted(paths)


def parse_simple_frontmatter(raw: str) -> dict[str, str]:
    """Parse simple top-level YAML scalar fields without importing PyYAML."""

    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.startswith((" ", "\t")):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("'\"")
    return fields


def reject_todo_markers(value: Any, path: str, errors: list[str]) -> None:
    """Prevent placeholder text from shipping in the Codex manifest."""

    if isinstance(value, str):
        if TODO_MARKER in value:
            errors.append(f"{path} still contains a TODO placeholder")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            reject_todo_markers(item, f"{path}[{index}]", errors)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            reject_todo_markers(item, f"{path}.{key}", errors)


def require_string(
    payload: dict[str, Any],
    key: str,
    errors: list[str],
    *,
    prefix: str | None = None,
) -> str | None:
    """Require a non-empty string field and return it when valid."""

    value = payload.get(key)
    field = f"{prefix}.{key}" if prefix else key
    if not isinstance(value, str) or not value.strip():
        errors.append(f"plugin.json field {field} must be a non-empty string")
        return None
    return value


def reject_unknown_fields(
    payload: dict[str, Any],
    allowed: set[str],
    prefix: str,
    errors: list[str],
) -> None:
    """Flag fields that Codex plugin ingestion is not expected to use."""

    for key in sorted(set(payload) - allowed):
        errors.append(f"{prefix} field {key} is not expected")


def validate_optional_https_url(
    payload: dict[str, Any],
    key: str,
    errors: list[str],
    *,
    prefix: str,
) -> None:
    """Validate optional URL fields when they are present."""

    value = payload.get(key)
    if value is None:
        return
    parsed = urlparse(value) if isinstance(value, str) else None
    if parsed is None or parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"plugin.json field {prefix}.{key} must be an https URL")


def normalize_relative_path(value: Any) -> str | None:
    """Normalize simple relative manifest paths such as ./skills/."""

    if not isinstance(value, str):
        return None
    return value.strip().removeprefix("./").rstrip("/") or None


if __name__ == "__main__":
    sys.exit(main())
