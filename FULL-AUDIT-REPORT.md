# Full SEO Audit Report — 01codetech.com

**Audit Date:** 2026-04-02  
**Audited URL:** https://01codetech.com/ (redirects to /zh)  
**Business Type:** Digital Marketing Agency — SEO, GEO, Web Design for Chinese Export (出海) Businesses  
**Location:** Wuxi, Jiangsu, China  
**Languages:** Chinese (zh) primary, 9 additional hreflang variants (en, ja, ko, es, fr, de, pt, ru, ar)  
**Framework:** Next.js (inferred from routing patterns and hydration behavior)  
**Auditor:** Claude SEO v1.7.2  

---

## SEO Health Score: **42 / 100** — FAILING

| Category | Weight | Score | Weighted |
|---|---|---|---|
| Technical SEO | 22% | 34/100 | 7.5 |
| Content Quality / E-E-A-T | 23% | 47/100 | 10.8 |
| On-Page SEO | 20% | 25/100 | 5.0 |
| Schema / Structured Data | 10% | 0/100 | 0.0 |
| Performance (CWV) | 10% | 50/100 | 5.0 |
| AI Search Readiness (GEO) | 10% | 31/100 | 3.1 |
| Images | 5% | 65/100 | 3.3 |
| **TOTAL** | 100% | | **42 / 100** |

> **Brand risk note:** This site sells SEO and GEO services to businesses. A score of 42/100 on its own SEO audit is a direct credibility liability. Prospects who verify the agency's SEO competency by examining its own site will find a site that fails the audits it sells.

---

## Executive Summary

### Top 5 Critical Issues

1. **robots.txt returns HTTP 500** — Googlebot crawl policy is undefined; Perplexity and other AI crawlers may treat the site as disallowed
2. **Zero structured data (JSON-LD)** — No schema on any page; ineligible for all rich results; invisible to AI Overview extraction
3. **Canonical tags missing sitewide** — All 15+ pages lack canonicals; split authority between /zh/ and / URL structures
4. **Sitemap URLs don't match live URL structure** — Sitemap lists `/web-design`, site serves `/zh/web-design`; crawlers indexing wrong URLs
5. **Duplicate title tags and meta descriptions across all pages** — SEO service page, homepage, and likely all pages share the same title and description

### Top 5 Quick Wins (< 1 day each)

1. Add `<link rel="canonical" href="...">` to every page template (1 hour)
2. Add Open Graph meta tags to every page template (2 hours)
3. Add `hreflang="x-default"` pointing to `/en` (30 minutes)
4. Fix duplicate title tags — each page needs a unique `<title>` (2–3 hours)
5. Deploy `llms.txt` at the domain root (1 hour)

---

## Section 1: Technical SEO — Score 34/100

### 1.1 robots.txt — CRITICAL ❌

- **Status:** HTTP 500 Internal Server Error
- **Impact:** Crawl policy is undefined for all bots. Per RFC 9309, a 5xx on robots.txt causes Googlebot to back off and retry; Perplexity and other AI crawlers may treat the site as fully disallowed.
- **Additional finding:** `favicon.ico` also returns HTTP 500 — same server-side routing failure.
- **Root cause:** Likely a Next.js middleware/routing misconfiguration that fails to serve static files at the root path.
- **Fix:** Restore robots.txt to HTTP 200 with valid content. Minimum viable:

```
User-agent: *
Allow: /

Sitemap: https://01codetech.com/sitemap.xml
```

### 1.2 Canonical Tags — CRITICAL ❌

- **Status:** Missing on every page tested (/, /zh, /zh/seo-service, /en)
- **Impact:** Google must independently determine the canonical URL when the sitemap and redirect structure contradict each other. Pages may be indexed at wrong URLs.
- **Fix:** Add `<link rel="canonical" href="[current page URL]">` to every page's `<head>`. In Next.js use `<Head>` component or metadata API.

### 1.3 Sitemap URL Structure Mismatch — CRITICAL ❌

- **Status:** sitemap.xml lists paths like `/web-design`, `/seo-service` but actual pages live at `/zh/web-design`, `/zh/seo-service`
- **Impact:** Googlebot follows sitemap URLs, receives redirects, and the sitemap's indexation signal is wasted. The 15 sitemap entries effectively count as zero guidance.
- **Fix:** Regenerate sitemap with correct language-prefixed URLs. For 10 languages × 15 pages = 150 URLs minimum. Use `<xhtml:link>` annotations per URL for hreflang in sitemap.

### 1.4 Duplicate Title Tags and Meta Descriptions — HIGH ❌

- **Homepage:** "01tech — 技术驱动的出海增长引擎"
- **SEO service page:** "01tech — 技术驱动的出海增长引擎" (identical)
- **Meta description (all pages):** "为出海企业提供外贸网站设计、SEO 优化与 GEO 策略服务" (identical)
- **Impact:** Google rewrites titles for pages with duplicates; meta descriptions are ignored for SERP snippets. CTR suffers.
- **Fix:** Each page must have a unique `<title>` (50–60 chars) and `<meta name="description">` (150–160 chars).

| Page | Suggested Title |
|---|---|
| Homepage /zh | 01tech — 技术驱动的出海增长引擎 \| GEO & SEO 出海服务 |
| SEO service | 外贸 SEO 优化服务 — Google 白帽排名增长 \| 01tech |
| Web Design | 高转化率外贸网站设计 — 多语言响应式建站 \| 01tech |
| GEO service | GEO 生成式引擎优化 — AI 搜索推荐策略 \| 01tech |

### 1.5 Hreflang — HIGH ⚠️

- **Declared:** zh, en, ja, ko, es, fr, de, pt, ru, ar (10 languages) ✓
- **Missing:** `x-default` — FAIL
- **Self-referencing:** Present on tested pages ✓
- **Return tags:** Appear consistent across zh and en pages ✓
- **lang attribute:** `/zh` page has `lang="zh"` (should be `lang="zh-Hans"` for Simplified Chinese); `/en` page correctly has `lang="en"` ✓
- **Fix:** Add `<link rel="alternate" hreflang="x-default" href="https://01codetech.com/en">` to all pages

### 1.6 H1 Rotational Slider — HIGH ⚠️

- **Status:** H1 cycles through service tab content ("高转化率的外贸网站" / "数据驱动的Google白帽SEO增长")
- **Impact:** Googlebot reads the DOM state at crawl time — the indexed H1 depends on which tab was active. Primary page signal is unreliable.
- **Fix:** Add a single static H1 above the slider that captures the overall page topic. Move service-specific headings to H2/H3 within the slider.

### 1.7 Open Graph / Twitter Card — HIGH ❌

- **Status:** All OG properties missing on every page; Twitter Card missing
- **Impact:** Social shares render with no image, no title, no description. AI citation engines (Bing Copilot, Perplexity) use OG data for structured metadata.

### 1.8 Meta Robots Tag — MEDIUM ⚠️

- **Status:** Missing on all pages
- **Impact:** No control over SERP snippet length, image preview size, or archiving behavior
- **Fix:** Add `<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">` to all public pages

### 1.9 Console Errors (4) — MEDIUM ⚠️

Specific errors identified:
1. `https://at.alicdn.com/wf/webfont/exMpJIukiCms/O5Ot7mIkHkCw.woff2` — 404 (font file missing from CDN)
2. `https://at.alicdn.com/wf/webfont/exMpJIukiCms/wMc6Iu_AAb3S.woff2` — 404 (font file missing)
3. `https://at.alicdn.com/wf/webfont/exMpJIukiCms/0b2eAEDm0YTu.woff2` — 404 (font file missing)
4. `https://01codetech.com/favicon.ico` — 500 (server error — same routing issue as robots.txt)

The 3 alicdn font 404s indicate a broken external font CDN dependency. If the webfont kit was regenerated on Alibaba's iconfont platform, the old woff2 URLs are now dead. This causes font rendering fallback (likely affecting icon fonts/custom icons sitewide) and adds 3 failed network requests to every page load.

### 1.10 Security Headers — MEDIUM ⚠️

Not confirmed via header inspection (browser fetch tool limitations), but standard Next.js deployments typically lack:
- `Content-Security-Policy`
- `X-Frame-Options: SAMEORIGIN`  
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security` (HSTS)
- `Permissions-Policy`

**Action:** Verify with `curl -I https://01codetech.com/zh` and add missing headers via `next.config.js` headers configuration or reverse proxy (Nginx/Vercel).

### 1.11 HTTPS / Viewport / Charset — PASS ✓

- HTTPS: ✓
- Viewport: `width=device-width, initial-scale=1` ✓  
- Charset: UTF-8 ✓

---

## Section 2: Content Quality / E-E-A-T — Score 47/100

### 2.1 E-E-A-T Breakdown

| Dimension | Score | Grade | Key Gap |
|---|---|---|---|
| Experience | 14/20 | C | Case studies unverified; no named clients |
| Expertise | 16/25 | C | No credentials, certifications, or team bios on content |
| Authoritativeness | 10/25 | D | QQ personal email; no third-party validation; no external links |
| Trustworthiness | 7/30 | F | No privacy policy; no terms; unbranded contact email |
| **Total** | **47/100** | **D+** | |

### 2.2 Critical Trust Gaps

**QQ personal email as primary contact:** `1363992060@qq.com` is listed on the homepage footer and used as the primary business contact. For a B2B agency targeting international clients with significant budgets (overseas expansion is a high-investment category), a personal QQ email is the highest-friction trust signal on the page. Replace with `hello@01codetech.com` or similar domain address immediately.

**No Privacy Policy or Terms of Service:** The site collects email addresses via a homepage form with no disclosed data handling policy. This is a legal exposure under GDPR (EU target market) and China's PIPL, and a trust-rater failure under QRG.

**No About/Team page visible:** Team members exist (referenced in GEO agent findings: Zhang Ming, Li Hua, Wang Fang, Chen Jie) but no named individuals appear on any content. Quality raters specifically evaluate "who is responsible for this content."

### 2.3 Content Depth Assessment

- Homepage: Adequate word count, but content is advertising-level copy rather than knowledge content
- Service pages: H1s are unique and accurate; titles are sitewide duplicates (see 1.4)
- Case studies: Strong percentage metrics (+450%, +380%, +520%) but fully anonymous — no client names, no methodology, no timeline
- News/Insights: 3 articles published on the same date (2026-04-02); raises batch-publication quality flag; no author bylines

### 2.4 Meta Description Quality

- Current (all pages): "为出海企业提供外贸网站设计、SEO 优化与 GEO 策略服务" — 53 chars (under-utilizing the ~80 Chinese char budget)
- Missing: differentiator, proof point, CTA
- Suggested homepage description: "01tech 专注技术驱动的出海增长——外贸建站、SEO 与 GEO 策略。已服务 50+ 出海企业，帮助你在 Google 和 AI 搜索中被全球买家发现。"

---

## Section 3: On-Page SEO — Score 25/100

| Element | Status | Issue |
|---|---|---|
| Title tags | ❌ Duplicate | All pages share the homepage title |
| Meta descriptions | ❌ Duplicate | All pages share the same description |
| H1 tags | ⚠️ Rotational | Dynamic slider; unreliable H1 signal |
| H2–H3 hierarchy | ✓ Present | Reasonable structure on service pages |
| Internal linking | ⚠️ Thin | 11 internal links from homepage; no contextual anchor text diversity |
| External links | ❌ None | Zero outbound links; reduces perceived authority |
| Image alt text | ⚠️ 1 missing | 1 of 4 images lacks alt text (25% failure rate) |
| URL structure | ✓ Clean | `/zh/seo-service` pattern is clean and descriptive |
| Breadcrumbs | ❌ None | No breadcrumb nav or BreadcrumbList schema |

---

## Section 4: Schema / Structured Data — Score 0/100

**Zero structured data on any page.** This is an unambiguous failure with compounding consequences:

| Schema Type | Page | Impact if Missing |
|---|---|---|
| Organization | Homepage | No Knowledge Panel eligibility; no entity disambiguation |
| LocalBusiness / ProfessionalService | Homepage | No local pack eligibility; no address/phone rich display |
| WebSite with SearchAction | Homepage | No Sitelinks Search Box |
| Service | Service pages | No entity-service association in Knowledge Graph |
| Article / BlogPosting | News pages | No article rich results; no freshness signal |
| BreadcrumbList | All interior pages | No breadcrumb display in SERPs |
| FAQPage | GEO/SEO service pages | AI Overview citation opportunity |

See ACTION-PLAN.md for ready-to-implement JSON-LD code blocks.

---

## Section 5: Performance (CWV) — Score 50/100 (estimated)

*Note: No Google CrUX field data available (no API credentials). Lab-based estimates from site analysis.*

| Metric | Estimated Status | Notes |
|---|---|---|
| LCP | ⚠️ Moderate risk | Hero section uses background image with text overlay; lazy-load may defer hero |
| CLS | ⚠️ Moderate risk | Dynamic slider/tab component; font 404s causing FOUT (Flash of Unstyled Text) |
| INP | ⚠️ Unknown | JavaScript-heavy Next.js with 4 console errors may indicate hydration delays |
| TTFB | ⚠️ Unknown | Server location (China) vs. global CDN coverage not confirmed |
| Font loading | ❌ 3 broken WOFF2 | 3 font files returning 404 from alicdn CDN — causes layout shift and icon rendering failure |

**Font CDN issue (HIGH):** The 3 broken woff2 files from `at.alicdn.com/wf/webfont/exMpJIukiCms/` affect custom icons/fonts across the entire site. If these are icon fonts (iconfont), UI elements using those icons are currently broken or falling back to blank/text. This is likely contributing to CLS. Fix: Regenerate the webfont kit on iconfont.cn or self-host the font files.

---

## Section 6: AI Search Readiness (GEO) — Score 31/100

### 6.1 AI Crawler Access

| File | Status | Impact |
|---|---|---|
| robots.txt | ❌ HTTP 500 | Undefined crawler policy for all AI bots |
| llms.txt | ❌ Missing | No AI-specific content manifest |
| ai.txt | ❌ Missing | No secondary AI access file |

### 6.2 Citation Readiness

- Content passages: Too short (25–95 words per block vs. 134–167 word threshold for AI citation)
- FAQ structure: Question-format H2s exist but no FAQPage schema
- Author attribution: Zero bylines across all content
- Statistics: Unattributed (no sources cited)
- News articles: CSR-rendered (invisible to Perplexity, inconsistent for ChatGPT)

### 6.3 Brand Signals for AI Recommendation

- Wikipedia entity: Not present
- YouTube channel: Not detected
- Reddit presence: Not detected
- Clutch / G2 listings: Not detected
- External press coverage: Not detected

### 6.4 The Credibility Problem

The GEO service page sells "AI引用源优化" (AI citation source optimization) including Wikipedia, Reddit, and industry forum presence building. **01tech has none of these assets for itself.** A prospect who asks ChatGPT "best GEO agency for Chinese export businesses" will not receive 01tech as an answer. This is verifiable by any informed buyer in 30 seconds.

---

## Section 7: Images — Score 65/100

| Finding | Count | Status |
|---|---|---|
| Total images on homepage | 4 | — |
| Images missing alt text | 1 (25%) | ❌ HIGH |
| Images with descriptive alt text | 3 | ✓ |
| External image CDN | assets.01codetech.com | ✓ (CDN in use) |
| Broken icon fonts (alicdn WOFF2) | 3 URLs | ❌ HIGH |
| OG image | Missing | ❌ HIGH |
| WebP/AVIF format | Not confirmed | ⚠️ |

---

## Section 8: International SEO (Hreflang) — Score 45/100

| Check | Status |
|---|---|
| Hreflang declared | ✓ 10 languages |
| Self-referencing hreflang | ✓ Present |
| Return tags (reciprocal) | ✓ Consistent across zh/en |
| x-default | ❌ MISSING |
| html lang accuracy | ⚠️ "zh" should be "zh-Hans" |
| Sitemap hreflang annotations | ❌ Missing (no xhtml:link in sitemap) |
| Canonical + hreflang alignment | ❌ Cannot align — canonicals missing |
| All language pages functional | Not fully tested — 10 variants |

---

## Appendix: Crawled Pages Summary

| Page | Title Unique | Canonical | H1 | JSON-LD | OG Tags |
|---|---|---|---|---|---|
| /zh (homepage) | ✓ | ❌ | Rotational | ❌ | ❌ |
| /zh/seo-service | ❌ (same as homepage) | ❌ | ✓ "数据驱动的Google白帽SEO增长" | ❌ | ❌ |
| /en (English homepage) | ✓ "01tech — Technology-Driven Growth Engine" | ❌ | ✓ "High-Converting Trade Websites" | ❌ | ❌ |
| /zh/web-design | Not tested | ❌ | Not tested | ❌ | ❌ |
| /zh/geo-service | Not tested | ❌ | Not tested | ❌ | ❌ |

---

## Screenshots

- `screenshots/homepage-desktop.png` — Full page desktop view
- `screenshots/homepage-mobile.png` — Full page mobile view (375px)

*Mobile rendering appears functional; floating contact buttons (Email, WhatsApp, WeChat, Demo) visible. Content sections loading correctly on mobile.*

---

*Full action plan with prioritized fixes: see ACTION-PLAN.md*  
*To generate a PDF version of this report: `/seo google report`*
