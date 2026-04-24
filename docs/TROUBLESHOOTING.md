# 故障排查

## 常见问题

### 技能未加载

**症状：** `/seo` 命令无法识别

**解决方案：**

1. 验证安装：
```bash
ls ~/.claude/skills/seo/SKILL.md
```

2. 检查 `SKILL.md` 是否有正确的 frontmatter：
```bash
head -5 ~/.claude/skills/seo/SKILL.md
```
应该以 `---` 开头，后面跟 YAML。

3. 重启 Claude Code：
```bash
claude
```

4. 重新运行安装器：
```bash
curl -fsSL https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/install.sh | bash
```

---

### Python 依赖错误

**症状：** `ModuleNotFoundError: No module named 'requests'`

**解决方案：**

从 v1.2.0 起，依赖会安装到虚拟环境中。请尝试：

```bash
# 使用虚拟环境 pip
~/.claude/skills/seo/.venv/bin/pip install -r ~/.claude/skills/seo/requirements.txt
```

如果虚拟环境不存在，请使用 `--user` 安装：
```bash
pip install --user -r ~/.claude/skills/seo/requirements.txt
```

或逐个安装：
```bash
pip install --user beautifulsoup4 requests lxml playwright Pillow urllib3 validators
```

### requirements.txt 未找到

**症状：** 安装后出现 `No such file: requirements.txt`

**解决方案：** 从 v1.2.0 起，`requirements.txt` 会复制到技能目录：

```bash
ls ~/.claude/skills/seo/requirements.txt
```

如果缺失，请直接下载：
```bash
curl -fsSL https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/requirements.txt \
  -o ~/.claude/skills/seo/requirements.txt
```

### Windows Python 检测问题

**症状：** `python is not recognized` 或 `pip points to wrong Python`

**解决方案（v1.2.0+）：** Windows 安装器现在会同时尝试 `python` 和 `py -3`。如果二者都失败：

1. 从 [python.org](https://python.org) 安装 Python，并勾选 “Add to PATH”
2. 或使用 Windows 启动器：`py -3 -m pip install -r requirements.txt`
3. 使用 `python -m pip`，不要直接使用裸 `pip`

---

### Playwright 截图错误

**症状：** `playwright._impl._errors.Error: Executable doesn't exist`

**解决方案：**
```bash
playwright install chromium
```

如果失败：
```bash
pip install playwright
python -m playwright install chromium
```

---

### 权限被拒绝错误

**症状：** 运行脚本时出现 `Permission denied`

**解决方案：**
```bash
chmod +x ~/.claude/skills/seo/scripts/*.py
```

---

### 找不到子代理

**症状：** `Agent 'seo-technical' not found`

**解决方案：**

1. 验证代理文件存在：
```bash
ls ~/.claude/agents/seo-*.md
```

2. 检查代理 frontmatter：
```bash
head -5 ~/.claude/agents/seo-technical.md
```

3. 重新安装代理：
```bash
cp /path/to/claude-seo/agents/*.md ~/.claude/agents/
```

---

### 超时错误

**症状：** `Request timed out after 30 seconds`

**解决方案：**

1. 目标站点可能较慢：请重试
2. 增加脚本调用中的超时时间
3. 检查网络连接
4. 某些站点会阻止自动化请求

---

### Schema 验证误报

**症状：** Hook 阻止了有效 schema

**检查项：**

1. 确认占位符已替换
2. 验证 `@context` 为 `https://schema.org`
3. 检查是否使用已废弃类型（HowTo、SpecialAnnouncement）
4. 在 [Google 富媒体搜索结果测试](https://search.google.com/test/rich-results) 中验证

---

### 审计性能较慢

**症状：** 完整审计耗时过长

**解决方案：**

1. 审计最多抓取 500 个页面：大型站点需要更久
2. 子代理会并行运行以加快分析
3. 如需更快检查，请对具体 URL 使用 `/seo page`
4. 检查站点响应是否较慢

---

## 获取帮助

1. **查看文档：** 阅读 [COMMANDS.md](COMMANDS.md) 和 [ARCHITECTURE.md](ARCHITECTURE.md)

2. **GitHub Issues：** 在仓库中报告 bug

3. **日志：** 查看 Claude Code 输出中的错误详情

## 调试模式

如需查看详细输出，请检查 Claude Code 内部日志，或直接运行脚本：

```bash
# 测试抓取
python3 ~/.claude/skills/seo/scripts/fetch_page.py https://example.com

# 测试解析
python3 ~/.claude/skills/seo/scripts/parse_html.py page.html --json

# 测试截图
python3 ~/.claude/skills/seo/scripts/capture_screenshot.py https://example.com
```
