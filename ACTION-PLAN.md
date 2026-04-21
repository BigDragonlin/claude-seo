# SEO Action Plan — 01codetech.com

**Generated:** 2026-04-02  
**Overall Score:** 42/100  
**Target Score (after Sprint 1–2):** 65–70/100  

---

## Priority Legend

| Level | Definition | Timeline |
|---|---|---|
| 🔴 Critical | Blocks indexing, penalties, or is an immediate credibility risk | Fix within 48 hours |
| 🟠 High | Significantly impacts rankings and trust | Fix within 1 week |
| 🟡 Medium | Optimization opportunity with clear ROI | Fix within 1 month |
| 🟢 Low | Nice-to-have improvement | Backlog |

---

## Sprint 1 — Fix Foundations (48 hours) — Estimated score gain: +10 pts

### 🔴 1. Fix robots.txt and favicon.ico (HTTP 500)

**File:** Server config / Next.js middleware  
**Effort:** 2 hours  
**Impact:** Critical — restores defined crawler policy; fixes favicon display

The root-level static file handler is broken. Both `/robots.txt` and `/favicon.ico` return HTTP 500. In Next.js, place `robots.txt` and `favicon.ico` in the `/public` directory — Next.js serves them automatically without any route handler needed.

```
/public/robots.txt
/public/favicon.ico
```

Minimum `robots.txt` content:

```
User-agent: *
Allow: /

# Declare sitemap location
Sitemap: https://01codetech.com/sitemap.xml
```

Verify after deploy: `curl -I https://01codetech.com/robots.txt` → expect `HTTP/2 200`

---

### 🔴 2. Add Canonical Tags to Every Page Template

**File:** Layout component (`app/layout.tsx` or `pages/_app.tsx`)  
**Effort:** 1 hour  
**Impact:** Critical — prevents duplicate content; establishes URL authority

In Next.js App Router:

```tsx
// app/[lang]/layout.tsx
import { Metadata } from 'next'

export async function generateMetadata({ params }): Promise<Metadata> {
  const canonical = `https://01codetech.com/${params.lang}${params.slug || ''}`
  return {
    alternates: {
      canonical: canonical,
    }
  }
}
```

Or manually in `<head>`:

```html
<link rel="canonical" href="https://01codetech.com/zh/seo-service" />
```

---

### 🔴 3. Fix Duplicate Title Tags and Meta Descriptions

**File:** Page-level metadata in each route  
**Effort:** 3 hours  
**Impact:** High — duplicate titles cause Google to rewrite them; hurts CTR

Each page needs a unique title (50–60 chars) and description (150–160 chars):

| Page | Title | Meta Description |
|---|---|---|
| /zh | 01tech — 技术驱动的出海增长引擎 | 01tech 专注技术驱动的出海增长——外贸建站、SEO 与 GEO 策略。已服务 50+ 出海企业，帮助你在 Google 和 AI 搜索中被全球买家发现。立即免费咨询。 |
| /zh/seo-service | 外贸 SEO 优化服务 — Google 白帽排名增长 \| 01tech | 技术 SEO + 内容双引擎，帮助外贸企业在 Google 目标关键词获得稳定自然排名。3 步 SEO 飞轮策略，持续获取高意向买家。查看成功案例。 |
| /zh/web-design | 高转化率外贸网站设计 — 多语言响应式建站 \| 01tech | 专为海外买家设计的外贸网站——响应式布局、多语言适配、以询盘转化为核心目标。已帮助多家出海企业实现询盘量 450% 增长。 |
| /zh/geo-service | GEO 生成式引擎优化 — AI 搜索推荐策略 \| 01tech | 面向 ChatGPT、Perplexity、Google AI Overview 的新一代优化策略。让 AI 搜索引擎在回答采购问题时推荐你的品牌。 |
| /zh/about | 关于 01tech — 技术驱动出海增长团队 \| 01tech | 01tech 是一支专注出海数字营销的团队，提供外贸建站、SEO 与 GEO 服务。了解我们的团队背景与服务理念。 |
| /zh/news | 出海 SEO 与 GEO 行业洞察 — 新闻动态 \| 01tech | 01tech 出海增长洞察：Google 算法更新解读、GEO 实战指南、AI 搜索趋势分析。每周更新，助力出海决策。 |

---

### 🔴 4. Add Open Graph and Twitter Card Tags

**File:** Layout/metadata component  
**Effort:** 2 hours  
**Impact:** High — social sharing, Bing Copilot, Perplexity citation metadata

Add to every page's `<head>` (unique per page):

```html
<!-- Open Graph -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://01codetech.com/zh/" />
<meta property="og:title" content="01tech — 技术驱动的出海增长引擎" />
<meta property="og:description" content="外贸建站、SEO 与 GEO 策略，帮助中国企业被全球买家发现" />
<meta property="og:image" content="https://01codetech.com/images/og-homepage-zh.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:locale" content="zh_CN" />

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="01tech — 技术驱动的出海增长引擎" />
<meta name="twitter:description" content="外贸建站、SEO 与 GEO 策略，帮助中国企业被全球买家发现" />
<meta name="twitter:image" content="https://01codetech.com/images/og-homepage-zh.jpg" />
```

Create OG images: 1200×630px, one per key page. Use brand colors (dark navy background, gold accent text).

---

### 🔴 5. Add hreflang x-default

**File:** Layout component  
**Effort:** 30 minutes  
**Impact:** High — tells Google which URL to serve for unmatched locales

```html
<link rel="alternate" hreflang="x-default" href="https://01codetech.com/en" />
```

Add this alongside the existing 10 language annotations on every page.

---

### 🔴 6. Deploy llms.txt

**File:** `/public/llms.txt`  
**Effort:** 1 hour  
**Impact:** High — signals AI readiness; curates content for LLM crawlers

```
# 01tech — Technology-Driven Overseas Growth Engine
# https://01codetech.com/llms.txt

> 01tech is a digital marketing agency based in Wuxi, China, specializing in SEO,
> GEO (Generative Engine Optimization), and conversion-focused web design for Chinese
> businesses expanding to global markets.

## Core Services
- [GEO Optimization](https://01codetech.com/en/geo-service): AI search visibility for B2B exporters — helps brands appear in ChatGPT, Perplexity, and Google AI Overviews
- [SEO Service](https://01codetech.com/en/seo-service): White-hat Google SEO for international trade sites
- [Web Design](https://01codetech.com/en/web-design): Conversion-focused, multilingual websites for global buyers

## Insights & Research
- [News & Insights](https://01codetech.com/en/news): GEO trends, Google algorithm updates, AI search guides

## About
- [About 01tech](https://01codetech.com/en/about): Team background and service philosophy

## License
Content on this site is available for AI training and citation under RSL 1.0.
```

---

### 🔴 7. Replace QQ Email with Domain Email

**File:** Footer component, contact forms, all metadata  
**Effort:** 1 hour  
**Impact:** Critical trust signal — QQ email communicates freelancer scale, not agency

Change `1363992060@qq.com` → `hello@01codetech.com` (or `contact@01codetech.com`) across:
- Homepage footer
- Contact forms
- Any schema markup
- Email signature

Configure domain email forwarding if not already set up.

---

## Sprint 2 — Core Indexability (1–2 weeks) — Estimated score gain: +12 pts

### 🔴 8. Implement Organization + LocalBusiness JSON-LD

**File:** `/zh/layout.tsx` or homepage component  
**Effort:** 3 hours  
**Impact:** Critical — entity recognition, Knowledge Panel eligibility, AI citation

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://01codetech.com/#organization",
      "name": "01tech",
      "alternateName": "零一科技",
      "url": "https://01codetech.com/zh",
      "logo": {
        "@type": "ImageObject",
        "url": "https://01codetech.com/images/logo.png",
        "width": 200,
        "height": 60
      },
      "contactPoint": {
        "@type": "ContactPoint",
        "telephone": "+86-17630827576",
        "contactType": "customer service",
        "availableLanguage": ["Chinese", "English"],
        "email": "hello@01codetech.com"
      }
    },
    {
      "@type": "ProfessionalService",
      "@id": "https://01codetech.com/#localbusiness",
      "name": "01tech 数字营销",
      "url": "https://01codetech.com/zh",
      "telephone": "+86-17630827576",
      "email": "hello@01codetech.com",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "锡悦城SPACE四楼",
        "addressLocality": "梁溪区",
        "addressRegion": "江苏省无锡市",
        "postalCode": "214000",
        "addressCountry": "CN"
      },
      "hasOfferCatalog": {
        "@type": "OfferCatalog",
        "name": "数字营销服务",
        "itemListElement": [
          {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "外贸网站设计", "url": "https://01codetech.com/zh/web-design"}},
          {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "SEO优化", "url": "https://01codetech.com/zh/seo-service"}},
          {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "GEO策略", "url": "https://01codetech.com/zh/geo-service"}}
        ]
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://01codetech.com/#website",
      "name": "01tech",
      "url": "https://01codetech.com",
      "publisher": {"@id": "https://01codetech.com/#organization"}
    }
  ]
}
</script>
```

---

### 🟠 9. Fix Sitemap — Regenerate with Correct Language-Prefixed URLs

**File:** Sitemap generator (likely `app/sitemap.ts` in Next.js)  
**Effort:** 4 hours  
**Impact:** Critical — current sitemap provides zero indexation guidance

Correct sitemap pattern (per URL, with hreflang annotations):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://01codetech.com/zh/seo-service</loc>
    <xhtml:link rel="alternate" hreflang="zh" href="https://01codetech.com/zh/seo-service"/>
    <xhtml:link rel="alternate" hreflang="en" href="https://01codetech.com/en/seo-service"/>
    <xhtml:link rel="alternate" hreflang="ja" href="https://01codetech.com/ja/seo-service"/>
    <!-- ... all 10 language variants + x-default -->
    <xhtml:link rel="alternate" hreflang="x-default" href="https://01codetech.com/en/seo-service"/>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <!-- Repeat for all pages -->
</urlset>
```

Total expected URLs: ~15 pages × 10 languages = 150 entries minimum.

---

### 🟠 10. Add Article JSON-LD to All News Pages

**File:** News article page component  
**Effort:** 2 hours  
**Impact:** High — enables article rich results; adds freshness signals; improves AI citation

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "[Article Title]",
  "description": "[Article Description — same as meta description]",
  "image": {
    "@type": "ImageObject",
    "url": "[Featured image URL]",
    "width": 1200,
    "height": 630
  },
  "datePublished": "[ISO 8601 with +08:00 timezone]",
  "dateModified": "[ISO 8601 with +08:00 timezone]",
  "author": {
    "@type": "Organization",
    "name": "01tech",
    "@id": "https://01codetech.com/#organization"
  },
  "publisher": {
    "@type": "Organization",
    "name": "01tech",
    "@id": "https://01codetech.com/#organization",
    "logo": {
      "@type": "ImageObject",
      "url": "https://01codetech.com/images/logo.png",
      "width": 200,
      "height": 60
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "[Article URL]"
  }
}
</script>
```

When named authors are added to the team/about page, update `author` to `@type: "Person"` with `name`, `url`, and `jobTitle`.

---

### 🟠 11. Enable SSR/SSG for News Articles

**File:** `app/[lang]/news/[slug]/page.tsx`  
**Effort:** 4–8 hours (developer time)  
**Impact:** Critical for GEO — Perplexity and other AI crawlers cannot read CSR-rendered content

Convert news article pages from client-side rendering to static generation:

```tsx
// app/[lang]/news/[slug]/page.tsx
export async function generateStaticParams() {
  const articles = await getAllArticles()
  return articles.map(a => ({ lang: a.lang, slug: a.slug }))
}

export async function generateMetadata({ params }) {
  const article = await getArticle(params.slug, params.lang)
  return {
    title: article.title,
    description: article.excerpt,
    // ... canonical, OG, etc.
  }
}
```

For the news listing, use ISR with `revalidate = 3600`.

---

### 🟠 12. Fix Broken Font CDN (3 WOFF2 404s)

**File:** CSS or font import config  
**Effort:** 1–2 hours  
**Impact:** Medium — fixes icon rendering and eliminates CLS from font fallback

The webfont kit at `at.alicdn.com/wf/webfont/exMpJIukiCms/` has stale URLs. Options:

1. **Regenerate** the iconfont project at [iconfont.cn](https://iconfont.cn) and update the import URL
2. **Self-host** the font files: download the kit, place WOFF2 files in `/public/fonts/`, update CSS `@font-face` to point to self-hosted files (faster + more reliable than third-party CDN)

Self-hosting is recommended for performance (eliminates third-party DNS lookup) and reliability.

---

### 🟠 13. Add Privacy Policy and Terms of Service Pages

**Effort:** 4–8 hours (legal content)  
**Impact:** High — required for GDPR (EU market), PIPL (China); critical E-E-A-T trust signal

Minimum privacy policy content:
- What data is collected (email from homepage form)
- How it's used and stored
- Data subject rights (access, deletion) under GDPR
- Contact for data requests
- Cookie policy

Add links to footer: 隐私政策 | Privacy Policy | 服务条款 | Terms of Service

---

### 🟠 14. Add BreadcrumbList Schema to All Interior Pages

**File:** Page component or layout for interior pages  
**Effort:** 2 hours  
**Impact:** Medium — improves SERP URL display; reinforces site structure

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "首页", "item": "https://01codetech.com/zh"},
    {"@type": "ListItem", "position": 2, "name": "SEO 优化", "item": "https://01codetech.com/zh/seo-service"}
  ]
}
</script>
```

---

### 🟠 15. Add Security Headers

**File:** `next.config.js`  
**Effort:** 1 hour  
**Impact:** Medium — security posture; some ranking signal for security-conscious crawlers

```js
// next.config.js
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'X-XSS-Protection', value: '1; mode=block' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
]

module.exports = {
  async headers() {
    return [{ source: '/(.*)', headers: securityHeaders }]
  }
}
```

---

## Sprint 3 — E-E-A-T and Content (2–4 weeks) — Estimated score gain: +15 pts

### 🟠 16. Create About/Team Page with Named Individuals

**Effort:** 1 day (content + design)  
**Impact:** High — single most impactful E-E-A-T improvement available

Minimum content:
- Team founder photo + bio (name, years of experience, specific expertise)
- Each team member: photo, name, title, background sentence
- Company founding story and mission
- Link to LinkedIn profiles (establishes sameAs for Organization schema)

Then link `author` fields in Article schema back to individual `Person` schema on the About page.

---

### 🟠 17. Add Author Bylines to All News Articles

**Effort:** 2 hours (template change) + ongoing  
**Impact:** High — direct E-E-A-T expertise signal; required for `Person` author schema

Every article needs:
- Author name (linked to their About page section or author profile)
- Publication date (visible on page)
- Last updated date (if different)

---

### 🟡 18. Expand Case Studies to Detail Pages

**Effort:** 2–3 days (writing + design)  
**Impact:** High — converts unverifiable % claims into credible evidence

Each case study needs:
- Client background (industry, company size, challenge)
- 01tech's specific interventions (what tactics, what tools, what timeline)
- Verified outcome with methodology note
- Client testimonial quote (with permission and attribution, or anonymized with industry label)
- Add `CaseStudy` or `Article` schema

---

### 🟡 19. Add FAQPage Schema to GEO and SEO Service Pages

**Effort:** 2 hours  
**Impact:** Medium — AI Overview citation opportunity; no Google rich result (restricted)

The GEO service page already has question-format H2s. Convert to FAQPage JSON-LD:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "什么是 GEO 优化？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "GEO（Generative Engine Optimization，生成式引擎优化）是针对 AI 搜索引擎（如 ChatGPT、Perplexity、Google AI Overviews）的优化策略。与传统 SEO 不同，GEO 的目标不是在链接列表中排名，而是让 AI 在生成答案时引用和推荐你的品牌。"
      }
    },
    {
      "@type": "Question",
      "name": "为什么外贸企业现在需要 GEO？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "越来越多的 B2B 买家开始用 ChatGPT 和 Perplexity 寻找供应商，而不是直接用 Google。据研究，超过 40% 的 B2B 采购决策者现在使用 AI 工具进行供应商调研。没有 GEO 布局的品牌，在 AI 搜索时代将完全不可见。"
      }
    }
  ]
}
</script>
```

---

### 🟡 20. Expand Content Passages to AI Citation Standard (134–167 words)

**Effort:** 1–2 weeks (content rewrite)  
**Impact:** High for GEO — current passage lengths (25–95 words) are below AI citation threshold

Rewrite principle: Every content block should answer its heading question completely as a self-contained passage of 134–167 words. The answer to the question must appear in the first 40–60 words.

---

### 🟡 21. Fix html lang Attribute

**File:** Layout root element  
**Effort:** 30 minutes  
**Impact:** Low — accuracy for assistive technologies and language processing

Change `<html lang="zh">` → `<html lang="zh-Hans">` on Chinese pages.
Ensure lang attribute is dynamically set per language route (en, ja, ko, etc.).

---

## Sprint 4 — Brand Authority and GEO Signals (Ongoing)

### 🟡 22. Launch YouTube Channel

**Effort:** Ongoing content creation  
**Impact:** Critical for GEO — 0.737 citation correlation

Content strategy:
- "How GEO works for Chinese B2B manufacturers" (English, for Western AI training data)
- "01tech SEO case study walkthroughs" (shows methodology, builds credibility)
- "AI search for foreign trade: what buyers are actually asking"
- Monthly: "GEO trends update" (leverages news section content)

---

### 🟡 23. Establish Reddit Presence

**Effort:** 2–3 hours/week ongoing  
**Impact:** High for GEO — Reddit content heavily represented in LLM training data

Target communities:
- r/SEO, r/bigseo (English-language SEO community)
- r/chinabusiness (Chinese export topics)
- r/digitalnomad (location-independent business)
- Industry-specific subreddits for target client industries (manufacturing, electronics, etc.)

Approach: authentic participation, not promotion. Answer questions about GEO and international SEO.

---

### 🟡 24. Register on Clutch and Agency Directories

**Effort:** 4 hours one-time  
**Impact:** Medium — third-party authority; Perplexity frequently cites Clutch for agency queries

- [Clutch.co](https://clutch.co) — request client reviews from case study clients
- [DesignRush](https://www.designrush.com) — digital agency directory
- [G2](https://g2.com) — for any SaaS tools the agency offers

---

### 🟢 25. Add Phone Country Code

**Effort:** 30 minutes  
**Impact:** Low — entity disambiguation improvement

Change `17630827576` → `+86-176-3082-7576` everywhere (footer, schema, llms.txt).

---

## Score Projection After Each Sprint

| Sprint | Actions | Estimated Score |
|---|---|---|
| Baseline | Current state | 42/100 |
| Sprint 1 (48 hrs) | Items 1–7 | ~52/100 |
| Sprint 2 (2 weeks) | Items 8–15 | ~64/100 |
| Sprint 3 (1 month) | Items 16–21 | ~72/100 |
| Sprint 4 (ongoing) | Items 22–25 | ~80/100 |

---

## Validation After Implementation

After Sprint 1, verify each fix:

```bash
# robots.txt
curl -I https://01codetech.com/robots.txt
# Expected: HTTP/2 200

# favicon
curl -I https://01codetech.com/favicon.ico
# Expected: HTTP/2 200

# Canonical (check in browser DevTools > Elements > <head>)
# Open Graph (check with https://opengraph.xyz)
# Schema validation: https://search.google.com/test/rich-results
# Hreflang: https://www.hreflang.org/checker/
```

After Sprint 2, submit sitemap to Google Search Console:
1. Verify site ownership
2. Submit `https://01codetech.com/sitemap.xml`
3. Monitor Coverage report for indexed URLs

---

*Full audit findings: see FULL-AUDIT-REPORT.md*  
*Generate PDF report: `/seo google report`*
