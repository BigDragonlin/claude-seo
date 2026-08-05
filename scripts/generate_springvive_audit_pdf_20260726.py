#!/usr/bin/env python3
"""Generate the illustrated Springvive SEO audit PDF.

The report uses the current crawl JSON, PageSpeed summary, and screenshots.
Layout is intentionally self-contained in ReportLab so it can be reproduced
without a browser, a web font, or a presentation template.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image as PILImage
from reportlab.graphics.shapes import Circle, Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# ---------------------------------------------------------------------------
# Paths and brand colors
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "tmp" / "springvive-audit-2026-07-26"
SCREENSHOT_DIR = AUDIT_DIR / "screenshots"
CRAWL_JSON = AUDIT_DIR / "json" / "crawl-summary.json"
PAGESPEED_JSON = AUDIT_DIR / "json" / "pagespeed-summary.json"
OUTPUT_PDF = ROOT / "output" / "pdf" / "springvive-seo-audit-2026-07-26.pdf"

NAVY = colors.HexColor("#0B1F3A")
BLUE = colors.HexColor("#1F6FBA")
CYAN = colors.HexColor("#43A7D8")
GREEN = colors.HexColor("#2BAA78")
AMBER = colors.HexColor("#EFA23A")
RED = colors.HexColor("#D95866")
INK = colors.HexColor("#1E2E43")
MUTED = colors.HexColor("#66758A")
PALE_BLUE = colors.HexColor("#EAF3FB")
PALE_GREEN = colors.HexColor("#E9F7F1")
PALE_AMBER = colors.HexColor("#FFF5E6")
PALE_RED = colors.HexColor("#FDEDEF")
PAPER = colors.HexColor("#F6F9FC")
WHITE = colors.white


# ---------------------------------------------------------------------------
# Font and paragraph styles
# ---------------------------------------------------------------------------

FONT_PATH = Path("/Library/Fonts/Arial Unicode.ttf")
pdfmetrics.registerFont(TTFont("AuditSans", str(FONT_PATH)))

BASE_STYLES = getSampleStyleSheet()
STYLES = {
    "cover_kicker": ParagraphStyle(
        "cover_kicker",
        fontName="AuditSans",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#A8D8F4"),
        spaceAfter=6,
    ),
    "cover_title": ParagraphStyle(
        "cover_title",
        fontName="AuditSans",
        fontSize=28,
        leading=34,
        textColor=WHITE,
        spaceAfter=8,
    ),
    "cover_subtitle": ParagraphStyle(
        "cover_subtitle",
        fontName="AuditSans",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#D8E8F5"),
    ),
    "h1": ParagraphStyle(
        "h1",
        fontName="AuditSans",
        fontSize=22,
        leading=28,
        textColor=NAVY,
        spaceAfter=12,
    ),
    "h2": ParagraphStyle(
        "h2",
        fontName="AuditSans",
        fontSize=15,
        leading=20,
        textColor=BLUE,
        spaceBefore=8,
        spaceAfter=8,
    ),
    "h3": ParagraphStyle(
        "h3",
        fontName="AuditSans",
        fontSize=11,
        leading=15,
        textColor=INK,
        spaceBefore=6,
        spaceAfter=4,
    ),
    "body": ParagraphStyle(
        "body",
        fontName="AuditSans",
        fontSize=9.2,
        leading=14.2,
        textColor=INK,
        spaceAfter=6,
    ),
    "small": ParagraphStyle(
        "small",
        fontName="AuditSans",
        fontSize=7.7,
        leading=11,
        textColor=MUTED,
    ),
    "caption": ParagraphStyle(
        "caption",
        fontName="AuditSans",
        fontSize=7.5,
        leading=10.5,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceBefore=4,
    ),
    "callout": ParagraphStyle(
        "callout",
        fontName="AuditSans",
        fontSize=11,
        leading=17,
        textColor=NAVY,
    ),
    "metric": ParagraphStyle(
        "metric",
        fontName="AuditSans",
        fontSize=18,
        leading=22,
        textColor=NAVY,
        alignment=TA_CENTER,
    ),
    "metric_label": ParagraphStyle(
        "metric_label",
        fontName="AuditSans",
        fontSize=7.5,
        leading=10,
        textColor=MUTED,
        alignment=TA_CENTER,
    ),
    "table_header": ParagraphStyle(
        "table_header",
        fontName="AuditSans",
        fontSize=7.8,
        leading=10,
        textColor=WHITE,
        alignment=TA_LEFT,
    ),
    "table_body": ParagraphStyle(
        "table_body",
        fontName="AuditSans",
        fontSize=7.5,
        leading=10.5,
        textColor=INK,
    ),
    "white_small": ParagraphStyle(
        "white_small",
        fontName="AuditSans",
        fontSize=8,
        leading=11,
        textColor=WHITE,
    ),
}


# ---------------------------------------------------------------------------
# Reusable visual components
# ---------------------------------------------------------------------------

class SectionRule(Flowable):
    """Short blue rule used under major section titles."""

    def __init__(self, width: float = 38 * mm):
        super().__init__()
        self.width = width
        self.height = 4 * mm

    def draw(self) -> None:
        self.canv.setStrokeColor(CYAN)
        self.canv.setLineWidth(2.5)
        self.canv.line(0, 2 * mm, self.width, 2 * mm)


def score_badge(score: int, label: str, diameter: float = 34 * mm) -> Drawing:
    """Create a compact circular score badge."""

    drawing = Drawing(diameter, diameter)
    center = diameter / 2
    ring = GREEN if score >= 85 else AMBER if score >= 70 else RED
    drawing.add(Circle(center, center, center - 2, fillColor=WHITE, strokeColor=PALE_BLUE, strokeWidth=6))
    drawing.add(Circle(center, center, center - 2, fillColor=None, strokeColor=ring, strokeWidth=4))
    drawing.add(
        String(
            center,
            center + 2,
            str(score),
            textAnchor="middle",
            fontName="AuditSans",
            fontSize=22,
            fillColor=NAVY,
        )
    )
    drawing.add(
        String(
            center,
            center - 12,
            label,
            textAnchor="middle",
            fontName="AuditSans",
            fontSize=6.8,
            fillColor=MUTED,
        )
    )
    return drawing


def horizontal_bar_chart(rows: list[tuple[str, int]], width: float, height: float) -> Drawing:
    """Draw a labeled 0–100 score chart without external chart libraries."""

    drawing = Drawing(width, height)
    left = 34 * mm
    top = height - 7 * mm
    row_height = (height - 10 * mm) / max(len(rows), 1)
    bar_width = width - left - 8 * mm

    for index, (label, value) in enumerate(rows):
        y = top - index * row_height
        drawing.add(
            String(
                0,
                y + 1,
                label,
                fontName="AuditSans",
                fontSize=7.2,
                fillColor=INK,
            )
        )
        drawing.add(Rect(left, y - 1, bar_width, 5, fillColor=PALE_BLUE, strokeColor=None))
        fill = GREEN if value >= 85 else BLUE if value >= 75 else AMBER if value >= 65 else RED
        drawing.add(
            Rect(left, y - 1, bar_width * value / 100, 5, fillColor=fill, strokeColor=None)
        )
        drawing.add(
            String(
                left + bar_width + 3,
                y,
                str(value),
                fontName="AuditSans",
                fontSize=7,
                fillColor=MUTED,
            )
        )
    return drawing


def metric_cards(items: list[tuple[str, str, colors.Color]]) -> Table:
    """Create a row of soft-background metric cards."""

    cells = []
    for value, label, background in items:
        cells.append(
            Table(
                [
                    [Paragraph(value, STYLES["metric"])],
                    [Paragraph(label, STYLES["metric_label"])],
                ],
                colWidths=[42 * mm],
                rowHeights=[12 * mm, 10 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), background),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E5EF")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            )
        )
    return Table([cells], colWidths=[44 * mm] * len(cells), hAlign="LEFT")


def bullet(text: str, color: colors.Color = BLUE) -> Table:
    """A readable bullet with a colored dot."""

    return Table(
        [
            [
                Paragraph("●", ParagraphStyle("dot", parent=STYLES["body"], textColor=color)),
                Paragraph(text, STYLES["body"]),
            ]
        ],
        colWidths=[5 * mm, 166 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        ),
    )


def callout(text: str, background: colors.Color = PALE_BLUE) -> Table:
    """Highlight one high-level conclusion."""

    table = Table(
        [[Paragraph(text, STYLES["callout"])]],
        colWidths=[170 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C8DDEB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        ),
    )
    return table


def short_url(url: str, limit: int = 62) -> str:
    """Shorten a URL to a readable path for tables."""

    path = urlparse(url).path
    return path if len(path) <= limit else path[: limit - 1] + "…"


def screenshot(path: Path, width: float, max_height: float) -> Image:
    """Scale a screenshot to fit the report without distortion."""

    with PILImage.open(path) as image:
        image_width, image_height = image.size
    scale = min(width / image_width, max_height / image_height)
    return Image(str(path), width=image_width * scale, height=image_height * scale)


def screenshot_card(path: Path, caption: str, width: float, max_height: float) -> Table:
    """Frame a screenshot with a short evidence caption."""

    image = screenshot(path, width - 8 * mm, max_height)
    return Table(
        [[image], [Paragraph(caption, STYLES["caption"])]],
        colWidths=[width],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D6E2EC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, 0), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2 * mm),
                ("TOPPADDING", (0, 1), (-1, 1), 2 * mm),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 3 * mm),
            ]
        ),
    )


def audit_table(headers: list[str], rows: list[list[str]], widths: list[float]) -> Table:
    """Standard report table with compact typography."""

    data = [[Paragraph(header, STYLES["table_header"]) for header in headers]]
    for row in rows:
        data.append([Paragraph(str(value), STYLES["table_body"]) for value in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E3EC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PAPER]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def section_title(title: str, subtitle: str | None = None) -> list[Flowable]:
    """Return a consistent major-section heading block."""

    output: list[Flowable] = [Paragraph(title, STYLES["h1"]), SectionRule()]
    if subtitle:
        output.extend([Spacer(1, 2 * mm), Paragraph(subtitle, STYLES["body"])])
    output.append(Spacer(1, 4 * mm))
    return output


# ---------------------------------------------------------------------------
# Page decorations
# ---------------------------------------------------------------------------

def draw_cover(canvas, doc) -> None:
    """Dark cover with a wide site screenshot as the visual anchor."""

    page_width, page_height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    hero_path = SCREENSHOT_DIR / "01-home-desktop.png"
    canvas.drawImage(
        str(hero_path),
        0,
        page_height * 0.43,
        width=page_width,
        height=page_height * 0.57,
        preserveAspectRatio=False,
        mask="auto",
    )
    canvas.setFillColor(colors.Color(0.02, 0.08, 0.16, alpha=0.22))
    canvas.rect(0, page_height * 0.43, page_width, page_height * 0.57, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.rect(0, page_height * 0.415, page_width, 5, fill=1, stroke=0)
    canvas.restoreState()


def draw_body(canvas, doc) -> None:
    """Page number, section label, and restrained brand line."""

    page_width, page_height = A4
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9E4ED"))
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, page_height - 15 * mm, page_width - 20 * mm, page_height - 15 * mm)
    canvas.setFont("AuditSans", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, page_height - 11 * mm, "SPRINGVIVE · SEO & PRODUCT EXPERIENCE AUDIT")
    canvas.drawRightString(page_width - 20 * mm, 10 * mm, f"{doc.page:02d}")
    canvas.setFillColor(BLUE)
    canvas.circle(20 * mm, 10.7 * mm, 1.3, fill=1, stroke=0)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def build_story(crawl: dict, pagespeed: dict) -> list[Flowable]:
    """Build every report page in order."""

    story: list[Flowable] = []

    # Cover
    story.extend(
        [
            Spacer(1, 141 * mm),
            Paragraph("SEO + PRODUCT EXPERIENCE AUDIT", STYLES["cover_kicker"]),
            Paragraph("Springvive 全站审计报告", STYLES["cover_title"]),
            Paragraph(
                "实时抓取、Google PageSpeed、桌面与手机实测<br/>"
                "2026 年 7 月 26 日 · springvivechiller.com",
                STYLES["cover_subtitle"],
            ),
            Spacer(1, 8 * mm),
            Table(
                [
                    [
                        score_badge(76, "SEO HEALTH", 33 * mm),
                        Paragraph(
                            "<font color='#A8D8F4'>结论</font><br/>"
                            "技术基础已明显改善；当前优先修 sitemap 中的 404、"
                            "资源文章缺失与移动端首屏性能。",
                            ParagraphStyle(
                                "cover_summary",
                                parent=STYLES["cover_subtitle"],
                                fontSize=10,
                                leading=15,
                            ),
                        ),
                    ]
                ],
                colWidths=[38 * mm, 116 * mm],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]
                ),
            ),
            NextPageTemplate("Body"),
            PageBreak(),
        ]
    )

    # Executive summary
    story += section_title(
        "01  执行摘要",
        "这是一次实时审计，不是旧报告的复述。当前数据来自 253 条 sitemap、"
        "28 个深度页面、11 个语言首页、Google PageSpeed 和真实浏览器截图。",
    )
    story.append(
        callout(
            "网站已经从“基础技术问题”进入“清理错误页面、补内容深度、优化移动体验”的阶段。"
            "本轮没有发现整站阻止收录的 Critical 问题，但有 4 个 High 问题会直接影响抓取效率、"
            "内容可见性或询价体验。"
        )
    )
    story += [Spacer(1, 5 * mm)]
    story.append(
        metric_cards(
            [
                ("253", "sitemap URL", PALE_BLUE),
                ("2", "sitemap 内 404", PALE_RED),
                ("5", "未进 sitemap 的文章", PALE_AMBER),
                ("4.8s", "手机 LCP", PALE_RED),
            ]
        )
    )
    story += [Spacer(1, 7 * mm)]
    category_scores = [
        ("技术 SEO", 78),
        ("内容质量", 62),
        ("页面 SEO", 84),
        ("结构化数据", 80),
        ("性能", 68),
        ("AI 搜索准备度", 78),
        ("图片", 95),
    ]
    story.append(horizontal_bar_chart(category_scores, 170 * mm, 72 * mm))
    story += [Spacer(1, 4 * mm), Paragraph("最优先的 4 件事", STYLES["h2"])]
    for item, color in [
        ("修复两个多了一层 /products/products/ 的产品地址，并清理 sitemap。", RED),
        ("把 5 篇资源文章加入 sitemap，并重写为真正能回答问题的文章。", AMBER),
        ("把手机 LCP 从 4.8 秒降到 2.5 秒以内。", AMBER),
        ("合并固定联系按钮，避免遮挡规格、统计数字和表单。", BLUE),
    ]:
        story.append(bullet(item, color))
    story.append(PageBreak())

    # Baseline comparison
    story += section_title(
        "02  与 6 月基线相比：哪些真的修好了",
        "下表把 2026-06-25 的公开审计基线与本轮实时结果并排比较。",
    )
    comparison_rows = [
        ["域名与 HTTPS", "入口未完全统一", "HTTP 与非 www 均 308 到 HTTPS www", "已修复"],
        ["安全响应头", "多项缺失", "HSTS / CSP / 防嵌入等主要头已齐", "已修复"],
        ["多语言元数据", "11 语言重复英文", "11 语言标题与描述均本地化", "已修复"],
        ["产品详情 sitemap", "大量产品未进入", "列表发现的 17 个产品均已进入", "已改善"],
        ["Product 占位内容", "出现 Specification a / Value a", "本轮未检测到", "已修复"],
        ["sitemap 规模", "627（每语言 57）", "253（每语言 23）", "需解释"],
        ["sitemap 状态", "英文 57 页均 200", "当前含 2 个英文 404", "新回归"],
        ["资源文章", "5 篇未进 sitemap 且很薄", "仍未解决", "持续问题"],
        ["手机 LCP", "约 4.5 秒", "约 4.8 秒", "未改善"],
    ]
    story.append(
        audit_table(
            ["项目", "旧基线", "本轮", "判断"],
            comparison_rows,
            [33 * mm, 47 * mm, 65 * mm, 25 * mm],
        )
    )
    story += [Spacer(1, 8 * mm)]
    story.append(
        callout(
            "好消息：网站主要基础设施已经稳住。需要注意：sitemap 从 627 缩到 253，"
            "如果这是有意删除旧/重复产品，方向可能正确；但 sitemap 里仍出现 404，说明生成规则还不够干净。",
            PALE_GREEN,
        )
    )
    story.append(PageBreak())

    # Technical SEO
    story += section_title(
        "03  技术 SEO 与可抓取性",
        "正式域名、canonical、hreflang 与安全头健康；当前技术优先级集中在 sitemap 清洁度。",
    )
    story.append(
        metric_cards(
            [
                ("308", "HTTP → HTTPS www", PALE_GREEN),
                ("308", "非 www → www", PALE_GREEN),
                ("11", "语言首页全部 200", PALE_GREEN),
                ("12", "典型页 hreflang 数", PALE_BLUE),
            ]
        )
    )
    story += [Spacer(1, 6 * mm), Paragraph("High · sitemap 中的 2 个错误产品地址", STYLES["h2"])]
    error_rows = [
        [
            short_url(item["url"], 72),
            str(item["status"]),
            "多一层 /products/products/；页面 noindex、无 canonical",
        ]
        for item in crawl["crawl"]["non_200"]
    ]
    story.append(
        audit_table(
            ["错误 URL", "状态", "说明"],
            error_rows,
            [94 * mm, 18 * mm, 58 * mm],
        )
    )
    story += [Spacer(1, 6 * mm), Paragraph("已经验证的技术强项", STYLES["h2"])]
    for text in [
        "robots.txt 允许 Google、Bing、GPTBot、OAI-SearchBot、ClaudeBot、PerplexityBot 等访问。",
        "sitemap 与 llms.txt 均返回 200，并使用 HTTPS。",
        "正常英文样本页 canonical 指向自身，没有发现 accidental noindex。",
        "主要安全头齐全，静态页面使用边缘缓存。",
        "Agent-UX 语义检查 100 分：19 个真实按钮、40 个真实链接、14 个语义区域。",
    ]:
        story.append(bullet(text, GREEN))
    story += [Spacer(1, 6 * mm)]
    story.append(
        callout(
            "验收口径：sitemap 中的每个 URL 必须是 200、index、canonical 指向自身；"
            "任何 404、重定向或 noindex 都应该从 sitemap 中移除。",
            PALE_AMBER,
        )
    )
    story.append(PageBreak())

    # International SEO
    story += section_title(
        "04  国际 SEO：11 个语言版本",
        "本轮逐一抓取了 11 个语言首页。所有页面返回 200，标题与描述已经本地化。",
    )
    locale_rows = []
    for item in crawl["multilingual"]["titles"]:
        locale_rows.append(
            [
                item["locale"].upper(),
                item["title"],
                str(item["status"]),
                "独立" if item["locale"] != "en" else "英文基准",
            ]
        )
    story.append(
        audit_table(
            ["语言", "首页标题", "状态", "元数据"],
            locale_rows,
            [18 * mm, 105 * mm, 18 * mm, 29 * mm],
        )
    )
    story += [Spacer(1, 5 * mm)]
    story.append(
        callout(
            "旧问题已经修复：11 个语言首页没有重复标题，也没有重复 meta description。"
            "下一步应保持内容同步，而不是只翻译标题。",
            PALE_GREEN,
        )
    )
    story.append(PageBreak())

    # Content
    story += section_title(
        "05  内容质量与 E-E-A-T",
        "产品详情页已经变得更像真实采购页面；资源文章和分类页仍是最明显的内容短板。",
    )
    story.append(
        metric_cards(
            [
                ("488–722", "有效产品页词数（样本）", PALE_GREEN),
                ("39–54", "资源文章词数", PALE_RED),
                ("27", "All-In-One 分类页词数", PALE_RED),
                ("214", "Chillers 分类页词数", PALE_AMBER),
            ]
        )
    )
    story += [Spacer(1, 7 * mm), Paragraph("High · 5 篇文章没有进入 sitemap", STYLES["h2"])]
    article_rows = []
    for item in crawl["content"]["resource_articles_under_800"]:
        article_rows.append(
            [
                short_url(item["url"], 66),
                str(item["word_count"]),
                "无 Article / BlogPosting",
                "未进 sitemap",
            ]
        )
    story.append(
        audit_table(
            ["文章", "词数", "结构化数据", "发现状态"],
            article_rows,
            [92 * mm, 15 * mm, 37 * mm, 27 * mm],
        )
    )
    story += [Spacer(1, 6 * mm), Paragraph("建议的重写顺序", STYLES["h2"])]
    for text in [
        "1. How to Choose the Right Chiller Size：加入水量、环境温度、目标温度、功率与降温时间计算。",
        "2. The Science Behind Cold Plunge Therapy：引用可靠研究，区分健康建议与产品说明。",
        "3. Factory Expansion：加入真实产线、产能、质量控制、认证与现场照片。",
        "4. Wellness Expo：加入展会名称、时间、展位、展品、客户反馈与后续成果。",
        "5. Industry Trends：给出来源、时间范围、数据与买家影响，不写泛泛趋势。",
    ]:
        story.append(bullet(text, AMBER))
    story.append(PageBreak())

    # Schema and GEO
    story += section_title(
        "06  结构化数据与 AI 搜索准备度",
        "产品数据已经比较完整，但内容中心没有相应的文章身份与来源信号。",
    )
    schema_rows = [
        ["Product", "11 页", "已实现", "保留真实 name / image / brand / offer"],
        ["Offer", "11 页", "已实现", "继续确保价格/询价信息真实"],
        ["BreadcrumbList", "16 页", "已实现", "路径清晰"],
        ["FAQPage", "11 页", "信息用途", "商业站不要期待 Google FAQ 富结果"],
        ["Article / BlogPosting", "0 页", "缺失", "为 5 篇文章补齐"],
        ["ContactPage", "0 页", "可补", "明确联系页身份"],
    ]
    story.append(
        audit_table(
            ["类型", "覆盖", "状态", "建议"],
            schema_rows,
            [37 * mm, 22 * mm, 25 * mm, 86 * mm],
        )
    )
    story += [Spacer(1, 7 * mm), Paragraph("AI 搜索强项", STYLES["h2"])]
    for text in [
        "主流 AI 爬虫均允许访问，llms.txt 给出品牌、核心页面和联系入口。",
        "首页、产品列表与产品详情均为服务器可读 HTML，不是空白 JavaScript 外壳。",
        "产品规格、FAQ 与买家指南已经形成可提取结构。",
    ]:
        story.append(bullet(text, GREEN))
    story += [Spacer(1, 4 * mm), Paragraph("AI 搜索短板", STYLES["h2"])]
    for text in [
        "资源文章缺少作者、来源、日期、原创数据和完整答案块，很难成为引用来源。",
        "目前没有足够的真实用户 CrUX 数据，也没有纳入品牌外部提及与反链质量。",
        "llms.txt 是辅助说明，不会替代页面内容质量和传统 SEO。",
    ]:
        story.append(bullet(text, AMBER))
    story.append(PageBreak())

    # Performance
    mobile = pagespeed["psi"]["mobile"]
    desktop = pagespeed["psi"]["desktop"]
    story += section_title(
        "07  性能与 Core Web Vitals",
        "Google 没有足够 CrUX 真实用户样本，因此以下为本轮实验室数据；重点看相对问题，不把单次分数当绝对值。",
    )
    story.append(
        Table(
            [
                [
                    score_badge(mobile["scores"]["performance"], "MOBILE", 34 * mm),
                    score_badge(desktop["scores"]["performance"], "DESKTOP", 34 * mm),
                    Paragraph(
                        "<b>移动端瓶颈</b><br/>"
                        "LCP 4.8 秒，首屏最大元素发现较晚；渲染阻塞约 1.21 秒，"
                        "图片可节省约 223KiB。",
                        STYLES["body"],
                    ),
                ]
            ],
            colWidths=[42 * mm, 42 * mm, 86 * mm],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (2, 0), (2, 0), PALE_AMBER),
                    ("BOX", (2, 0), (2, 0), 0.5, colors.HexColor("#ECD8B7")),
                    ("LEFTPADDING", (2, 0), (2, 0), 8),
                    ("RIGHTPADDING", (2, 0), (2, 0), 8),
                    ("TOPPADDING", (2, 0), (2, 0), 8),
                    ("BOTTOMPADDING", (2, 0), (2, 0), 8),
                ]
            ),
        )
    )
    story += [Spacer(1, 7 * mm)]
    perf_rows = [
        [
            "FCP",
            mobile["metrics"]["first-contentful-paint"]["display"],
            desktop["metrics"]["first-contentful-paint"]["display"],
            "手机需改善",
        ],
        [
            "LCP",
            mobile["metrics"]["largest-contentful-paint"]["display"],
            desktop["metrics"]["largest-contentful-paint"]["display"],
            "手机 >4s，差",
        ],
        [
            "TBT",
            mobile["metrics"]["total-blocking-time"]["display"],
            desktop["metrics"]["total-blocking-time"]["display"],
            "桌面脚本较重",
        ],
        [
            "CLS",
            mobile["metrics"]["cumulative-layout-shift"]["display"],
            desktop["metrics"]["cumulative-layout-shift"]["display"],
            "好",
        ],
    ]
    story.append(
        audit_table(
            ["指标", "手机", "桌面", "判断"],
            perf_rows,
            [28 * mm, 38 * mm, 38 * mm, 66 * mm],
        )
    )
    story += [Spacer(1, 6 * mm), Paragraph("按收益排序的优化动作", STYLES["h2"])]
    for text in [
        "首屏图在初始 HTML 中直接可发现，并设置 fetchpriority=high；不要懒加载 LCP 图。",
        "YouTube 改为点击封面后再加载，减少约 1MB 第三方传输和大量未使用脚本。",
        "本地托管字体或减少字重，降低 Google Fonts 的渲染阻塞。",
        "延后聊天组件与非必要脚本；优化图片交付和缓存。",
    ]:
        story.append(bullet(text, BLUE))
    story.append(PageBreak())

    # UX step 1
    story += section_title(
        "08  真实体验审计 · Step 1 首页",
        "用户目标：快速理解 Springvive 做什么，并找到合适的产品或询价入口。",
    )
    story.append(
        screenshot_card(
            SCREENSHOT_DIR / "01-home-desktop.png",
            "当前桌面首页：品牌清晰，工业制造现场建立真实感；右侧三个固定联系按钮始终占据较大面积。",
            170 * mm,
            88 * mm,
        )
    )
    story += [Spacer(1, 5 * mm)]
    for text in [
        "<b>优点：</b>顶部导航简洁，品牌色一致，产品与工厂视觉可信。",
        "<b>风险：</b>自动轮播状态并不稳定；部分画面只剩大图，价值主张和 CTA 可能消失。",
        "<b>可访问性：</b>Lighthouse 发现一处颜色对比不足；页面语义结构总体良好。",
        "<b>建议：</b>固定一张最强首屏，或确保每张轮播都保留 H1、价值主张和主要按钮。",
    ]:
        story.append(bullet(text, GREEN if "优点" in text else AMBER))
    story.append(PageBreak())

    # UX step 2
    story += section_title(
        "09  真实体验审计 · Step 2 产品列表",
        "用户目标：比较产品，快速缩小选择范围。",
    )
    story.append(
        screenshot_card(
            SCREENSHOT_DIR / "02-chillers-desktop.png",
            "Chillers 分类页：卡片和侧栏分类清楚，但两个错误产品链接也出现在这一列表中。",
            170 * mm,
            88 * mm,
        )
    )
    story += [Spacer(1, 5 * mm)]
    for text in [
        "<b>优点：</b>产品卡片整齐，图片一致，分类侧栏能帮助用户建立产品层级。",
        "<b>风险：</b>标题较长并被截断，用户很难在列表里比较功率、温度和适用场景。",
        "<b>SEO：</b>页面只有约 214 个英文词，分类意图与选型逻辑不够完整。",
        "<b>建议：</b>卡片增加 3 个统一对比字段；分类页增加选型表与适用场景。",
    ]:
        story.append(bullet(text, GREEN if "优点" in text else AMBER))
    story.append(PageBreak())

    # UX step 3
    story += section_title(
        "10  真实体验审计 · Step 3 产品详情",
        "用户目标：确认规格、可信度与采购条件，然后发起询价。",
    )
    story.append(
        screenshot_card(
            SCREENSHOT_DIR / "03-product-detail-desktop.png",
            "产品详情首屏：大图、关键规格、Send Inquiry 与 WhatsApp 的层级清晰。",
            170 * mm,
            91 * mm,
        )
    )
    story += [Spacer(1, 4 * mm)]
    for text in [
        "<b>优点：</b>真实产品图、型号、核心参数和两个询价入口都在首屏；内容约 722 词。",
        "<b>优点：</b>Product / Offer / Breadcrumb / FAQ 数据完整，旧占位符已清理。",
        "<b>风险：</b>固定联系按钮覆盖右侧规格卡，可能遮挡 Cooling Time 等值。",
        "<b>建议：</b>固定联系按钮收起为单个入口；把 MOQ、交期、保修与认证靠近询价按钮。",
    ]:
        story.append(bullet(text, GREEN if "优点" in text else AMBER))
    story.append(PageBreak())

    # UX step 4 and mobile
    story += section_title(
        "11  真实体验审计 · Step 4 联系与手机首屏",
        "用户目标：在不受遮挡的情况下完成询价；手机用户应在首屏看到价值与下一步。",
    )
    contact_card = screenshot_card(
        SCREENSHOT_DIR / "04-contact-desktop.png",
        "联系页：表单结构清楚，但固定按钮覆盖右侧联系卡。",
        108 * mm,
        67 * mm,
    )
    mobile_card = screenshot_card(
        SCREENSHOT_DIR / "05-home-mobile.png",
        "手机首页：第三张轮播只有产品氛围图，缺少标题与 CTA；联系按钮覆盖数字。",
        56 * mm,
        100 * mm,
    )
    story.append(
        Table(
            [[contact_card, mobile_card]],
            colWidths=[112 * mm, 58 * mm],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )
    story += [Spacer(1, 5 * mm)]
    for text in [
        "<b>优点：</b>表单字段少、联系方式完整，提交路径直观。",
        "<b>风险：</b>固定按钮在桌面与手机都覆盖信息；移动轮播让核心文案和 CTA 消失。",
        "<b>建议：</b>手机端合并成一个联系按钮；桌面端在滚动后出现并避开表单。",
        "<b>证据限制：</b>本轮没有提交表单，避免产生真实销售线索；因此未验证提交成功页与邮件通知。",
    ]:
        story.append(bullet(text, GREEN if "优点" in text else AMBER))
    story.append(PageBreak())

    # Roadmap
    story += section_title(
        "12  优先行动路线图",
        "先修会让搜索引擎和用户走错路的问题，再补内容和性能。",
    )
    roadmap_rows = [
        [
            "0–7 天",
            "抓取与成交",
            "修 2 个错误产品 URL；301/308；重建 sitemap；加入 5 篇文章；合并联系按钮",
            "High",
        ],
        [
            "2–4 周",
            "内容与结构",
            "重写两篇买家型文章；补作者/来源/日期；Article/ContactPage；分类选型指南",
            "High / Medium",
        ],
        [
            "1–3 个月",
            "速度与体验",
            "LCP 图优先；YouTube 点击后加载；字体本地化；延后聊天；固定首屏信息",
            "Medium",
        ],
    ]
    story.append(
        audit_table(
            ["时间", "目标", "动作", "优先级"],
            roadmap_rows,
            [25 * mm, 33 * mm, 90 * mm, 22 * mm],
        )
    )
    story += [Spacer(1, 8 * mm), Paragraph("每次上线后的验证清单", STYLES["h2"])]
    checklist = [
        "sitemap non-200 = 0；没有 noindex、重定向或非 canonical URL。",
        "两个错误路径不再出现在产品列表 HTML；正确产品页为 200。",
        "5 篇文章在 sitemap 中，并且 Article/BlogPosting 验证通过。",
        "手机 PageSpeed 连跑 3 次，LCP 中位数 <2.5 秒。",
        "首页 → 产品列表 → 产品详情 → 联系页，桌面与手机都不被固定组件遮挡。",
        "11 个语言首页继续保持独立 title、description 与 self hreflang。",
    ]
    for item in checklist:
        story.append(bullet(item, GREEN))
    story += [Spacer(1, 8 * mm)]
    story.append(
        callout(
            "最推荐的下一步：先单独修复两个错误产品路由和 sitemap。"
            "这是成本最低、验收最明确、也最能快速消除抓取浪费的一组改动。",
            PALE_GREEN,
        )
    )
    story.append(PageBreak())

    # Evidence and limits
    story += section_title(
        "13  证据、方法与限制",
        "报告中的判断均对应本轮实时抓取、浏览器截图或 Google 实验室数据。",
    )
    evidence_rows = [
        ["全站结构", "sitemap.xml", "253 URL；11 语言 × 23 URL"],
        ["深度抓取", "crawl-summary.json", "23 个英文 sitemap 页 + 5 篇发现文章"],
        ["国际 SEO", "11 个语言首页", "全部 200；title / description 无重复"],
        ["性能", "PageSpeed Insights", "手机 78 / LCP 4.8s；桌面 83 / LCP 1.1s"],
        ["体验", "5 张当前截图", "首页、列表、详情、联系、手机首页"],
        ["语义结构", "agent_ux_check.py", "100 分；表单标签与真实控件基础良好"],
    ]
    story.append(
        audit_table(
            ["模块", "证据", "结果"],
            evidence_rows,
            [32 * mm, 52 * mm, 86 * mm],
        )
    )
    story += [Spacer(1, 8 * mm), Paragraph("本轮没有覆盖", STYLES["h2"])]
    for text in [
        "CrUX 真实用户数据：站点没有达到足够的 Chrome 流量样本。",
        "GSC / GA4 / URL Inspection：当前运行环境缺少 Google 客户端库。",
        "Moz / Bing 反链质量：没有对应 API 凭据。",
        "完整 WCAG 人工测试：截图和 Lighthouse 只能指出可见风险。",
        "表单真实提交：为避免创建真实销售线索，本轮未提交。",
    ]:
        story.append(bullet(text, MUTED))
    story += [Spacer(1, 10 * mm)]
    story.append(
        Paragraph(
            "报告文件：springvive-seo-audit-2026-07-26.pdf<br/>"
            "审计源数据：tmp/springvive-audit-2026-07-26/",
            STYLES["small"],
        )
    )

    return story


def main() -> int:
    crawl = json.loads(CRAWL_JSON.read_text(encoding="utf-8"))
    pagespeed = json.loads(PAGESPEED_JSON.read_text(encoding="utf-8"))

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    page_width, page_height = A4

    document = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title="Springvive SEO 全站审计报告",
        author="OpenAI Codex",
        subject="springvivechiller.com SEO and product experience audit",
    )

    cover_frame = Frame(
        22 * mm,
        22 * mm,
        page_width - 44 * mm,
        page_height - 34 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="cover-frame",
    )
    body_frame = Frame(
        20 * mm,
        17 * mm,
        page_width - 40 * mm,
        page_height - 37 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="body-frame",
    )
    document.addPageTemplates(
        [
            PageTemplate(id="Cover", frames=[cover_frame], onPage=draw_cover),
            PageTemplate(id="Body", frames=[body_frame], onPage=draw_body),
        ]
    )
    document.build(build_story(crawl, pagespeed))
    print(OUTPUT_PDF)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
