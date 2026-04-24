# 命令参考

## 概览

所有 Claude SEO 命令都以 `/seo` 开头，后接一个子命令。

## 命令列表

### `/seo audit <url>`

使用并行分析进行整站 SEO 审计。

**示例：**
```
/seo audit https://example.com
```

**功能：**
1. 抓取最多 500 个页面
2. 检测业务类型
3. 并行委派给 7 个专业子代理
4. 生成 SEO 健康评分（0-100）
5. 创建按优先级排序的行动计划

**输出：**
- `FULL-AUDIT-REPORT.md`
- `ACTION-PLAN.md`
- `screenshots/`（如果 Playwright 可用）

---

### `/seo page <url>`

深度单页分析。

**示例：**
```
/seo page https://example.com/about
```

**分析内容：**
- 页面 SEO（标题、meta、标题层级、URL）
- 内容质量（字数、可读性、E-E-A-T）
- 技术元素（canonical、robots、Open Graph）
- Schema 标记
- 图片（alt 文本、尺寸、格式）
- Core Web Vitals 潜在问题

---

### `/seo technical <url>`

覆盖 9 个类别的技术 SEO 审计。

**示例：**
```
/seo technical https://example.com
```

**类别：**
1. 可抓取性
2. 可索引性
3. 安全性
4. URL 结构
5. 移动端优化
6. Core Web Vitals（LCP、INP、CLS）
7. 结构化数据
8. JavaScript 渲染
9. IndexNow 协议

---

### `/seo content <url>`

E-E-A-T 与内容质量分析。

**示例：**
```
/seo content https://example.com/blog/post
```

**评估内容：**
- Experience 信号（第一手经验）
- Expertise（作者资质）
- Authoritativeness（外部认可）
- Trustworthiness（透明度、安全性）
- AI 引用就绪度
- 内容新鲜度

---

### `/seo schema <url>`

Schema 标记检测、验证与生成。

**示例：**
```
/seo schema https://example.com
```

**功能：**
- 检测现有 schema（JSON-LD、Microdata、RDFa）
- 按 Google 要求验证
- 识别缺失机会
- 生成可直接使用的 JSON-LD

---

### `/seo geo <url>`

AI Overviews / 生成式引擎优化（GEO）。

**示例：**
```
/seo geo https://example.com/blog/guide
```

**分析内容：**
- 可引用评分（可引用事实、统计数据）
- 结构可读性（标题、列表、表格）
- 实体清晰度（定义、上下文）
- 权威信号（资质、来源）
- 结构化数据支持

---

### `/seo images <url>`

图片优化分析。

**示例：**
```
/seo images https://example.com
```

**检查内容：**
- alt 文本是否存在及其质量
- 文件大小（标记 >200KB）
- 格式（WebP/AVIF 建议）
- 响应式图片（srcset、sizes）
- 懒加载
- CLS 防护（尺寸声明）

---

### `/seo sitemap <url>`

分析现有 XML sitemap。

**示例：**
```
/seo sitemap https://example.com/sitemap.xml
```

**验证内容：**
- XML 格式
- URL 数量（每个文件 <50k）
- URL 状态码
- lastmod 准确性
- 已废弃标签（priority、changefreq）
- 与抓取页面的覆盖率对比

---

### `/seo sitemap generate`

使用行业模板生成新的 sitemap。

**示例：**
```
/seo sitemap generate
```

**流程：**
1. 选择或自动检测业务类型
2. 交互式规划结构
3. 应用质量门槛（30/50 个本地页面限制）
4. 生成有效 XML
5. 创建文档

---

### `/seo plan <type>`

战略 SEO 规划。

**类型：** `saas`、`local`、`ecommerce`、`publisher`、`agency`

**示例：**
```
/seo plan saas
```

**创建内容：**
- 完整 SEO 策略
- 竞争分析
- 内容日历
- 实施路线图（4 个阶段）
- 站点架构设计

---

### `/seo competitor-pages [url|generate]`

竞品对比页面生成。

**示例：**
```
/seo competitor-pages https://example.com/vs/competitor
/seo competitor-pages generate
```

**能力：**
- 生成 “X vs Y” 对比页布局
- 创建 “Alternatives to X” 页面结构
- 构建带评分的功能对比矩阵
- 生成 Product + AggregateRating schema 标记
- 应用转化优化的 CTA 布局
- 强制遵循公平性准则（准确数据、来源引用）

---

### `/seo hreflang [url]`

Hreflang 与国际 SEO 审计和生成。

**示例：**
```
/seo hreflang https://example.com
```

**能力：**
- 验证自引用 hreflang 标签
- 检查返回标签互惠性（A→B 需要 B→A）
- 验证 x-default 标签是否存在
- 验证 ISO 639-1 语言代码和 ISO 3166-1 地区代码
- 检查 canonical URL 与 hreflang 的一致性
- 检测协议不匹配（HTTP 与 HTTPS）
- 生成正确的 hreflang link 标签和 sitemap XML

---

### `/seo programmatic [url|plan]`

面向规模化生成页面的程序化 SEO 分析与规划。

**示例：**
```
/seo programmatic https://example.com/tools/
/seo programmatic plan
```

**能力：**
- 评估数据源质量（CSV、JSON、API、数据库）
- 规划每页具备独特内容的模板引擎
- 设计 URL 模式策略（`/tools/[tool-name]`、`/[city]/[service]`）
- 自动化内链（hub/spoke、相关项目、面包屑）
- 强制执行薄内容防护（质量门槛、字数阈值）
- 防止索引膨胀（低价值页 noindex、分页、分面导航）

---

### `/seo dataforseo [command]`

通过 DataForSEO MCP 服务器获取实时 SEO 数据（扩展）。覆盖 9 个 API 模块，共 22 个命令。

**前置条件：** 已安装 DataForSEO 扩展（`./extensions/dataforseo/install.sh`）

**SERP 分析：**
```
/seo dataforseo serp <keyword>              # Google 自然结果（也支持 Bing/Yahoo）
/seo dataforseo serp-youtube <keyword>      # YouTube 搜索结果
/seo dataforseo youtube <video_id>          # YouTube 视频深度分析
```

**关键词研究：**
```
/seo dataforseo keywords <seed>             # 关键词想法和建议
/seo dataforseo volume <keywords>           # 搜索量指标
/seo dataforseo difficulty <keywords>       # 关键词难度评分
/seo dataforseo intent <keywords>           # 搜索意图分类
/seo dataforseo trends <keyword>            # Google Trends 数据
```

**域名与竞品：**
```
/seo dataforseo backlinks <domain>          # 完整反向链接画像
/seo dataforseo competitors <domain>        # 竞品分析
/seo dataforseo ranked <domain>             # 已排名关键词
/seo dataforseo intersection <domains>      # 关键词/反链重叠
/seo dataforseo traffic <domains>           # 流量估算
/seo dataforseo subdomains <domain>         # 带排名数据的子域名
/seo dataforseo top-searches <domain>       # 提及域名的热门查询
```

**技术 / 站内：**
```
/seo dataforseo onpage <url>                # 站内分析（Lighthouse）
/seo dataforseo tech <domain>               # 技术栈检测
/seo dataforseo whois <domain>              # WHOIS 数据
```

**内容与商业数据：**
```
/seo dataforseo content <keyword/url>       # 内容分析和趋势
/seo dataforseo listings <keyword>          # 商业列表搜索
```

**AI 可见性 / GEO：**
```
/seo dataforseo ai-scrape <query>           # 面向 GEO 的 ChatGPT 网页抓取器
/seo dataforseo ai-mentions <keyword>       # LLM 提及追踪
```

---

### `/seo image-gen [use-case] <description>`

用于 SEO 资产的 AI 图片生成（扩展）。由 Gemini 通过 nanobanana-mcp 提供支持。

**前置条件：** 已安装 Banana 扩展（`./extensions/banana/install.sh`）

**使用场景：**
```
/seo image-gen og <description>          # OG/社交预览图（16:9，1K）
/seo image-gen hero <description>        # 博客 hero 图（16:9，2K）
/seo image-gen product <description>     # 产品摄影图（4:3，2K）
/seo image-gen infographic <description> # 信息图视觉（2:3，4K）
/seo image-gen custom <description>      # 使用完整 Creative Director 流程自定义生成
/seo image-gen batch <description> [N]   # 生成 N 个变体（默认：3）
```

**示例：**
```
/seo image-gen og "Professional SaaS analytics dashboard with clean UI"
/seo image-gen hero "Dramatic sunset over modern city skyline"
/seo image-gen product "Wireless noise-canceling headphones on marble surface"
```

**功能：**
1. 将 SEO 使用场景映射到优化后的领域模式、宽高比和分辨率
2. 构建 6 组件 Reasoning Brief（Creative Director 流程）
3. 通过 Gemini API 生成图片
4. 提供 SEO 检查清单（alt 文本、文件命名、WebP、schema 标记）

---

## 快速参考

| 命令 | 使用场景 |
|---------|----------|
| `/seo audit <url>` | 整站审计 |
| `/seo competitor-pages [url\|generate]` | 竞品对比页面 |
| `/seo content <url>` | E-E-A-T 分析 |
| `/seo geo <url>` | AI 搜索优化 |
| `/seo hreflang [url]` | Hreflang/i18n SEO 审计 |
| `/seo images <url>` | 图片优化 |
| `/seo image-gen [use-case] <desc>` | AI 图片生成（扩展） |
| `/seo page <url>` | 单页分析 |
| `/seo plan <type>` | 战略规划 |
| `/seo programmatic [url\|plan]` | 程序化 SEO 分析 |
| `/seo schema <url>` | Schema 验证 |
| `/seo sitemap <url>` | Sitemap 验证 |
| `/seo sitemap generate` | 创建新 sitemap |
| `/seo technical <url>` | 技术 SEO 检查 |
| `/seo dataforseo [command]` | 实时 SEO 数据（扩展） |
