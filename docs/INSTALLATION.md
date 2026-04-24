# 安装指南

## 前置条件

- **Python 3.10+**，并已安装 pip
- **Git**，用于克隆仓库
- 已安装并配置 **Claude Code CLI**

可选：
- **Playwright**，用于截图能力

## 快速安装

### Unix/macOS/Linux

```bash
curl -fsSL https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
git clone --depth 1 https://github.com/AgriciDaniel/claude-seo.git
cd claude-seo
powershell -ExecutionPolicy Bypass -File install.ps1
```

## 手动安装

1. **克隆仓库**

```bash
git clone https://github.com/AgriciDaniel/claude-seo.git
cd claude-seo
```

2. **运行安装脚本**

```bash
./install.sh
```

3. **安装 Python 依赖**（如果未自动完成）

安装器会在 `~/.claude/skills/seo/.venv/` 创建虚拟环境。如果失败，可手动安装：

```bash
# 方案 A：使用虚拟环境
~/.claude/skills/seo/.venv/bin/pip install -r ~/.claude/skills/seo/requirements.txt

# 方案 B：安装到用户级环境
pip install --user -r ~/.claude/skills/seo/requirements.txt
```

4. **安装 Playwright 浏览器**（可选，用于视觉分析）

```bash
pip install playwright
playwright install chromium
```

Playwright 是可选依赖。没有它时，视觉分析会退回使用 WebFetch。

## 安装路径

安装器会将文件复制到：

| 组件 | 路径 |
|-----------|------|
| 主技能 | `~/.claude/skills/seo/` |
| 子技能 | `~/.claude/skills/seo-*/` |
| 子代理 | `~/.claude/agents/seo-*.md` |

## 验证安装

1. 启动 Claude Code：

```bash
claude
```

2. 检查技能是否已加载：

```
/seo
```

你应该会看到帮助信息，或提示输入 URL。

## 卸载

```bash
curl -fsSL https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/uninstall.sh | bash
```

也可以手动卸载：

```bash
rm -rf ~/.claude/skills/seo
rm -rf ~/.claude/skills/seo-audit
rm -rf ~/.claude/skills/seo-backlinks
rm -rf ~/.claude/skills/seo-competitor-pages
rm -rf ~/.claude/skills/seo-content
rm -rf ~/.claude/skills/seo-dataforseo
rm -rf ~/.claude/skills/seo-geo
rm -rf ~/.claude/skills/seo-google
rm -rf ~/.claude/skills/seo-hreflang
rm -rf ~/.claude/skills/seo-image-gen
rm -rf ~/.claude/skills/seo-images
rm -rf ~/.claude/skills/seo-local
rm -rf ~/.claude/skills/seo-maps
rm -rf ~/.claude/skills/seo-page
rm -rf ~/.claude/skills/seo-plan
rm -rf ~/.claude/skills/seo-programmatic
rm -rf ~/.claude/skills/seo-schema
rm -rf ~/.claude/skills/seo-sitemap
rm -rf ~/.claude/skills/seo-technical
rm -f ~/.claude/agents/seo-*.md
```

## 升级

升级到最新版本：

```bash
# 卸载当前版本
curl -fsSL https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/uninstall.sh | bash

# 安装新版本
curl -fsSL https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/install.sh | bash
```

## 故障排查

### “Skill not found” 错误

确认技能安装在正确位置：

```bash
ls ~/.claude/skills/seo/SKILL.md
```

如果文件不存在，请重新运行安装器。

### Python 依赖错误

手动安装依赖：

```bash
pip install beautifulsoup4 requests lxml playwright Pillow urllib3 validators
```

### Playwright 截图错误

安装 Chromium 浏览器：

```bash
playwright install chromium
```

### Unix 权限错误

确保脚本具备可执行权限：

```bash
chmod +x ~/.claude/skills/seo/scripts/*.py
```
