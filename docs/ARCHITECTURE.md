# 架构

## 概览

Claude SEO 遵循 Anthropic 官方 Claude Code 技能规范，采用模块化、多技能架构。

## 目录结构

```text
~/.claude/
├── skills/
│   ├── seo/                         # 主编排技能
│   │   ├── SKILL.md                 # 入口点，包含路由逻辑
│   │   └── references/              # 按需加载的参考文件
│   │       ├── cwv-thresholds.md
│   │       ├── schema-types.md
│   │       ├── eeat-framework.md
│   │       └── quality-gates.md
│   ├── seo-audit/                   # 整站审计
│   ├── seo-competitor-pages/        # 竞品对比页面
│   ├── seo-content/                 # E-E-A-T 分析
│   ├── seo-geo/                     # AI 搜索优化
│   ├── seo-hreflang/                # Hreflang/i18n SEO
│   ├── seo-images/                  # 图片优化
│   ├── seo-page/                    # 单页分析
│   ├── seo-plan/                    # 战略规划
│   │   └── assets/                  # 行业模板
│   ├── seo-programmatic/            # 程序化 SEO
│   ├── seo-schema/                  # Schema 标记
│   ├── seo-sitemap/                 # Sitemap 分析/生成
│   └── seo-technical/               # 技术 SEO
└── agents/
    ├── seo-technical.md             # 技术 SEO 专家
    ├── seo-content.md               # 内容质量审阅者
    ├── seo-schema.md                # Schema 标记专家
    ├── seo-sitemap.md               # Sitemap 架构师
    ├── seo-performance.md           # 性能分析师
    └── seo-visual.md                # 视觉分析师
```

## 组件类型

### Skills

Skills 是带 YAML frontmatter 的 Markdown 文件，用于定义能力和操作说明。

**SKILL.md 格式：**
```yaml
---
name: skill-name
description: >
  When to use this skill. Include activation keywords
  and concrete use cases.
---

# Skill Title

Instructions and documentation...
```

### Subagents

Subagents 是可被委派任务的专业工作者。它们拥有自己的上下文和工具。

**Agent 格式：**
```yaml
---
name: agent-name
description: What this agent does.
tools: Read, Bash, Write, Glob, Grep
---

Instructions for the agent...
```

### Reference Files

Reference files 存放静态数据，按需加载，以避免主技能文件膨胀。

## 编排流程

### 完整审计（`/seo audit`）

```text
用户请求
  ↓
主编排器：skills/seo/SKILL.md
  ├─ 检测业务类型
  ├─ 并行启动专业子代理
  │   ├─ Technical Agent
  │   ├─ Content Agent
  │   ├─ Schema Agent
  │   ├─ Sitemap Agent
  │   ├─ Performance Agent
  │   └─ Visual Agent
  ├─ 汇总结果
  └─ 生成报告与行动计划
```

### 单技能命令

```text
用户命令（例如 /seo schema <url>）
  ↓
主技能路由
  ↓
对应子技能（例如 seo-schema/SKILL.md）
  ↓
按需加载参考文件和脚本
  ↓
输出分析结果或生成文件
```

## 核心设计原则

### 1. 渐进式披露

主技能只包含路由逻辑和高层说明。详细知识存放在子技能和参考文件中，只有在需要时才加载。

**收益：**
- 降低上下文占用
- 保持主入口快速、清晰
- 便于独立维护各个能力模块

### 2. 模块化职责

每个子技能聚焦一个 SEO 领域：技术、内容、schema、sitemap、图片、GEO、国际化等。

**收益：**
- 更容易测试和扩展
- 避免单一大文件难以维护
- 可以按任务选择最相关的上下文

### 3. 子代理并行化

完整审计会把不同维度的分析委派给多个专业子代理并行执行。

**收益：**
- 缩短整站审计时间
- 让每个子代理专注自己的专业视角
- 最终结果由主编排器统一汇总

### 4. 安全优先

脚本层面使用 URL 验证和 SSRF 防护；技能层面通过质量门槛避免输出不可靠建议。

**关键约束：**
- 所有抓取脚本都应调用 `validate_url()`
- 阻止本地地址、私有网段和危险协议
- 避免生成带占位符或废弃类型的 schema
- 不建议大规模创建低质量本地页面

## 执行脚本

Python 脚本位于 `scripts/`，为技能提供可执行能力。

| 脚本 | 用途 |
|------|------|
| `fetch_page.py` | 带 SSRF 防护的页面抓取 |
| `parse_html.py` | 解析 HTML 中的 SEO 元素 |
| `pagespeed_check.py` | 调用 PageSpeed Insights |
| `capture_screenshot.py` | 使用 Playwright 截图 |
| `drift_baseline.py` | 捕获 SEO 基线 |
| `drift_compare.py` | 对比当前页面与基线 |
| `schema_validate.py` | 验证结构化数据 |
| `sitemap_analyze.py` | 分析 XML sitemap |

## 数据流

```text
输入 URL
  ↓
URL 验证（SSRF 防护）
  ↓
页面抓取 / API 调用 / 截图
  ↓
HTML、性能、schema、内容等维度解析
  ↓
技能或子代理分析
  ↓
Markdown 报告、JSON-LD、行动计划或其他输出
```

## 质量门槛

### 1. 技术准确性

- 使用当前 Core Web Vitals 指标：LCP、INP、CLS
- 识别已废弃或不再推荐的 schema 类型
- 对 canonical、robots、hreflang 等基础信号进行一致性检查

### 2. 内容质量

- E-E-A-T 框架用于判断经验、专业性、权威性和可信度
- GEO 分析关注可引用性、实体清晰度和结构可读性
- 避免只基于字数给出低质量建议

### 3. 防护规则

- 程序化 SEO 需要唯一内容和索引控制
- 本地页面数量达到 30 个给出警告，50 个作为硬性停止阈值
- Schema 生成必须替换占位符并避免过时类型
- 强制使用 INP 替代 FID

### 4. 行业感知

- 为不同业务类型提供模板
- 从首页信号自动检测行业
- 按行业输出定制建议

## 文件命名约定

| 类型 | 模式 | 示例 |
|------|---------|---------|
| Skill | `seo-{name}/SKILL.md` | `seo-audit/SKILL.md` |
| Agent | `seo-{name}.md` | `seo-technical.md` |
| Reference | `{topic}.md` | `cwv-thresholds.md` |
| Script | `{action}_{target}.py` | `fetch_page.py` |
| Template | `{industry}.md` | `saas.md` |

## 扩展点

### 添加新的子技能

1. 创建 `skills/seo-newskill/SKILL.md`
2. 添加包含 name 和 description 的 YAML frontmatter
3. 编写技能说明
4. 更新主入口 `skills/seo/SKILL.md`，将请求路由到新技能

### 添加新的子代理

1. 创建 `agents/seo-newagent.md`
2. 添加包含 name、description、tools 的 YAML frontmatter
3. 编写代理说明
4. 在相关技能中引用该代理

### 添加新的参考文件

1. 在合适的 `references/` 目录中创建文件
2. 在技能中添加按需加载说明

## 扩展

扩展是可选附加组件，通过 MCP 服务器集成外部数据源。它们位于 `extensions/<name>/`，并包含自己的安装/卸载脚本。

```text
extensions/
├── dataforseo/                    # DataForSEO MCP 集成
│   ├── README.md                  # 扩展文档
│   ├── install.sh                 # Unix 安装器
│   ├── install.ps1                # Windows 安装器
│   ├── uninstall.sh               # Unix 卸载器
│   ├── uninstall.ps1              # Windows 卸载器
│   ├── field-config.json          # API 响应字段过滤
│   ├── skills/
│   │   └── seo-dataforseo/
│   │       └── SKILL.md           # 子技能（22 个命令）
│   ├── agents/
│   │   └── seo-dataforseo.md      # 子代理
│   └── docs/
│       └── DATAFORSEO-SETUP.md    # 账号设置指南
└── banana/                        # Banana 图片生成（Gemini AI）
    ├── README.md                  # 扩展文档
    ├── install.sh                 # Unix 安装器
    ├── uninstall.sh               # Unix 卸载器
    ├── skills/
    │   └── seo-image-gen/
    │       └── SKILL.md           # 子技能（6 个命令）
    ├── agents/
    │   └── seo-image-gen.md       # 图片审计子代理
    ├── scripts/                   # Python 脚本（仅标准库）
    │   ├── generate.py            # 直接 API 回退
    │   ├── edit.py                # 图片编辑回退
    │   ├── batch.py               # CSV 批处理工作流
    │   ├── cost_tracker.py        # 用量和成本追踪
    │   ├── presets.py             # 品牌预设管理
    │   ├── setup_mcp.py           # MCP 配置
    │   └── validate_setup.py      # 安装验证
    ├── references/                # 按需知识
    │   ├── prompt-engineering.md  # 6 组件 Reasoning Brief
    │   ├── gemini-models.md       # 模型规格和价格
    │   ├── mcp-tools.md           # MCP 工具参考
    │   ├── post-processing.md     # ImageMagick 配方
    │   ├── cost-tracking.md       # 成本追踪指南
    │   ├── presets.md             # 预设 schema
    │   └── seo-image-presets.md   # SEO 专用预设
    └── docs/
        └── BANANA-SETUP.md        # API key 和 MCP 设置
```

### 可用扩展

| 扩展 | 包 | 增加内容 |
|-----------|---------|-------------|
| **DataForSEO** | `dataforseo-mcp-server` | 22 个命令：实时 SERP、关键词、反向链接、站内分析、内容分析、商业列表、AI 可见性、LLM 提及 |
| **Banana Image Gen** | `@ycse/nanobanana-mcp` | 6 个命令：OG 图、hero 图、产品图、信息图、自定义生成，以及通过 Gemini AI 批量生成 |

### 扩展约定

每个扩展遵循以下模式：
1. 自包含于 `extensions/<name>/`
2. 自带 `install.sh` 和 `install.ps1`，用于复制文件并配置 MCP
3. 自带 `uninstall.sh` 和 `uninstall.ps1`，用于干净地回滚安装
4. 将技能安装到 `~/.claude/skills/seo-<name>/`
5. 将代理安装到 `~/.claude/agents/seo-<name>.md`
6. 将 MCP 配置合并到 `~/.claude/settings.json`（非破坏式）
