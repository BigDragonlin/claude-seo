<!-- Updated: 2026-02-07 -->
# MCP 集成

## 概览

Claude SEO 可以与 Model Context Protocol（MCP）服务器集成，以访问外部 API 并增强分析能力。

## 可用集成

### PageSpeed Insights API

直接使用 Google 的 PageSpeed Insights API 获取真实 Core Web Vitals 数据。

**配置：**

1. 从 [Google Cloud Console](https://console.cloud.google.com/) 获取 API key
2. 启用 PageSpeed Insights API
3. 在分析中使用：

```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=URL&key=YOUR_API_KEY"
```

### Google Search Console

如需自然搜索数据，可使用 [ahonn](https://github.com/ahonn/mcp-server-gsc) 的 `mcp-server-gsc` MCP 服务器。它提供搜索表现数据、URL 检查和 sitemap 管理能力。

**配置：**

```json
{
  "mcpServers": {
    "google-search-console": {
      "command": "npx",
      "args": ["-y", "mcp-server-gsc"],
      "env": {
        "GOOGLE_CREDENTIALS_PATH": "/path/to/credentials.json"
      }
    }
  }
}
```

### PageSpeed Insights MCP Server

使用 [enemyrr](https://github.com/enemyrr/mcp-server-pagespeed) 的 `mcp-server-pagespeed`，通过 MCP 执行 Lighthouse 审计、CWV 指标获取和性能评分。

**配置：**

```json
{
  "mcpServers": {
    "pagespeed": {
      "command": "npx",
      "args": ["-y", "mcp-server-pagespeed"],
      "env": {
        "PAGESPEED_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 官方 SEO MCP 服务器（2025-2026）

SEO 方向的 MCP 生态已经明显成熟。以下是可用于生产的集成：

| 工具 | 包 / 端点 | 类型 | 备注 |
|------|-------------------|------|-------|
| **Ahrefs** | `@ahrefs/mcp` | 官方 | 2025 年 7 月发布。支持本地和远程模式。提供反向链接、关键词、站点审计数据。 |
| **Semrush** | `https://mcp.semrush.com/v1/mcp` | 官方（远程） | 通过远程 MCP 端点访问完整 API。提供域名分析、关键词研究、反向链接数据。 |
| **Google Search Console** | `mcp-server-gsc` | 社区 | 作者 ahonn。提供搜索表现、URL 检查、sitemap。 |
| **PageSpeed Insights** | `mcp-server-pagespeed` | 社区 | 作者 enemyrr。提供 Lighthouse 审计、CWV 指标、性能评分。 |
| **DataForSEO** | `dataforseo-mcp-server` | 官方扩展 | 9 个模块、79 个工具、22 个命令。安装：`./extensions/dataforseo/install.sh`。参见[扩展文档](../extensions/dataforseo/README.md)。 |
| **kwrds.ai** | kwrds MCP server | 社区 | 关键词研究、搜索量、难度评分。 |
| **SEO Review Tools** | SEO Review Tools MCP | 社区 | 站点审计和站内分析 API。 |

## API 使用示例

### PageSpeed Insights

```python
import requests

def get_pagespeed_data(url: str, api_key: str) -> dict:
    """Fetch PageSpeed Insights data for a URL."""
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "key": api_key,
        "strategy": "mobile",  # or "desktop"
        "category": ["performance", "accessibility", "best-practices", "seo"]
    }
    response = requests.get(endpoint, params=params)
    return response.json()
```

### 来自 CrUX 的 Core Web Vitals

```python
def get_crux_data(url: str, api_key: str) -> dict:
    """Fetch Chrome UX Report data for a URL."""
    endpoint = "https://chromeuxreport.googleapis.com/v1/records:queryRecord"
    payload = {
        "url": url,
        "formFactor": "PHONE"  # or "DESKTOP"
    }
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    response = requests.post(endpoint, json=payload, headers=headers, params=params)
    return response.json()
```

## 可用指标

### 来自 PageSpeed Insights

| 指标 | 说明 |
|--------|-------------|
| LCP | Largest Contentful Paint（实验室数据） |
| INP | Interaction to Next Paint（估算） |
| CLS | Cumulative Layout Shift（实验室数据） |
| FCP | First Contentful Paint |
| TBT | Total Blocking Time |
| Speed Index | 视觉进度速度 |

### 来自 CrUX（真实用户数据）

| 指标 | 说明 |
|--------|-------------|
| LCP | 第 75 百分位，真实用户 |
| INP | 第 75 百分位，真实用户 |
| CLS | 第 75 百分位，真实用户 |
| TTFB | Time to First Byte |

## 最佳实践

1. **速率限制**：遵守 API 配额（PageSpeed 通常为 25k 请求/天）
2. **缓存**：缓存结果，避免重复 API 调用
3. **真实数据 vs 实验室数据**：排名信号优先参考真实用户数据（CrUX）
4. **错误处理**：优雅处理 API 错误

## 没有 API Key 时

即使没有 API key，Claude SEO 仍然可以：

1. 分析 HTML 源码中的潜在问题
2. 识别常见性能问题
3. 检查阻塞渲染的资源
4. 评估图片优化机会
5. 检测重 JavaScript 实现

分析会注明：实际 Core Web Vitals 测量需要来自真实用户的现场数据。
