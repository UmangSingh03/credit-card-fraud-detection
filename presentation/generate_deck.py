"""
AegisGuard Academic & Professional PowerPoint Generator
Generates AegisGuard_Research_Presentation.pptx (16:9 widescreen, dark cybersecurity theme)
"""
from __future__ import annotations

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# Color Palette Constants
BG_DARK = RGBColor(10, 14, 26)         # #0A0E1A
SURFACE_DARK = RGBColor(19, 27, 46)    # #131B2E
SURFACE_CARD = RGBColor(24, 34, 58)    # #18223A
BORDER_COLOR = RGBColor(38, 52, 84)    # #263454
CYAN_ACCENT = RGBColor(0, 229, 255)    # #00E5FF
TEAL_ACCENT = RGBColor(45, 212, 191)   # #2DD4BF
EMERALD_ACCENT = RGBColor(16, 185, 129)# #10B981
ROSE_ACCENT = RGBColor(244, 63, 94)    # #F43F5E
AMBER_ACCENT = RGBColor(245, 158, 11)  # #F59E0B
TEXT_WHITE = RGBColor(248, 250, 252)   # #F8FAFC
TEXT_SLATE = RGBColor(148, 163, 184)   # #94A3B8
TEXT_MUTED = RGBColor(100, 116, 139)   # #64748B

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "backend" / "reports"
OUTPUT_PPTX = BASE_DIR / "presentation" / "AegisGuard_Research_Presentation.pptx"
OUTPUT_PDF = BASE_DIR / "presentation" / "AegisGuard_Research_Presentation.pdf"


def set_solid_background(slide, color=BG_DARK):
    """Set uniform dark background color for slide."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_header(slide, category_tag: str, title: str, subtitle: str, slide_num: int, total_slides: int = 14):
    """Standard professional header on top of content slides."""
    # Category Tag / Badge
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(6.0), Inches(0.3))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = category_tag.upper()
    p_tag.font.size = Pt(9.5)
    p_tag.font.bold = True
    p_tag.font.color.rgb = CYAN_ACCENT

    # Main Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(11.733), Inches(0.6))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE

    # Subtitle / Context Lead
    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.22), Inches(11.733), Inches(0.4))
    tf_sub = sub_box.text_frame
    tf_sub.word_wrap = True
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = subtitle
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = TEXT_SLATE

    # Top right badge
    stat_box = slide.shapes.add_textbox(Inches(9.5), Inches(0.38), Inches(3.0), Inches(0.3))
    tf_stat = stat_box.text_frame
    p_stat = tf_stat.paragraphs[0]
    p_stat.alignment = PP_ALIGN.RIGHT
    p_stat.text = "AEGISGUARD AI"
    p_stat.font.size = Pt(9)
    p_stat.font.bold = True
    p_stat.font.color.rgb = TEXT_MUTED

    # Footer
    footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.08), Inches(10.0), Inches(0.3))
    tf_footer = footer_box.text_frame
    p_foot = tf_footer.paragraphs[0]
    p_foot.text = "AegisGuard: Real-Time AI Credit Card Fraud Detection System | Academic Review"
    p_foot.font.size = Pt(8.5)
    p_foot.font.color.rgb = TEXT_MUTED

    # Slide Number
    num_box = slide.shapes.add_textbox(Inches(11.3), Inches(7.08), Inches(1.2), Inches(0.3))
    tf_num = num_box.text_frame
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.text = f"{slide_num} / {total_slides}"
    p_num.font.size = Pt(8.5)
    p_num.font.bold = True
    p_num.font.color.rgb = CYAN_ACCENT


def add_card(slide, left, top, width, height, bg_color=SURFACE_CARD, border_color=BORDER_COLOR):
    """Adds a dark card surface shape."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
    else:
        shape.line.fill.background()
    return shape


def add_table_custom(slide, left, top, width, height, headers: list[str], rows: list[list[str]], col_widths: list[float] = None):
    """Draws a cleanly formatted dark-theme table."""
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
    table = table_shape.table

    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = Inches(w)

    # Header Row
    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(28, 41, 70)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = header
        p.font.bold = True
        p.font.size = Pt(10.5)
        p.font.color.rgb = CYAN_ACCENT
        p.alignment = PP_ALIGN.LEFT

    # Data Rows
    for row_idx, row_data in enumerate(rows):
        row_bg = SURFACE_CARD if row_idx % 2 == 0 else RGBColor(16, 23, 40)
        for col_idx, cell_value in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = str(cell_value)
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_WHITE
            p.alignment = PP_ALIGN.LEFT

    return table_shape


# =========================================================================
# SLIDE BUILDERS
# =========================================================================

def build_slide_1_title(prs):
    """Slide 1: Title Slide with academic metadata and cybersecurity aesthetic."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide, BG_DARK)

    # Top Glowing Brand Strip
    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.7), Inches(11.733), Inches(0.06))
    strip.fill.solid()
    strip.fill.fore_color.rgb = CYAN_ACCENT
    strip.line.fill.background()

    # Category Pill
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.0), Inches(4.5), Inches(0.35))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(0, 45, 75)
    pill.line.color.rgb = CYAN_ACCENT
    pill.line.width = Pt(1)
    tf_p = pill.text_frame
    p_p = tf_p.paragraphs[0]
    p_p.alignment = PP_ALIGN.CENTER
    p_p.text = "ACADEMIC CAPSTONE / THESIS PRESENTATION"
    p_p.font.size = Pt(9.5)
    p_p.font.bold = True
    p_p.font.color.rgb = CYAN_ACCENT

    # Main Project Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.733), Inches(1.3))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = "AegisGuard: Real-Time AI Credit Card\nFraud Detection System"
    p_t.font.size = Pt(32)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_WHITE

    # Subtitle / Scope
    sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.9), Inches(11.733), Inches(0.6))
    tf_s = sub_box.text_frame
    tf_s.word_wrap = True
    p_s = tf_s.paragraphs[0]
    p_s.text = "A Hybrid Supervised Ensemble & Unsupervised Anomaly Architecture with Local SHAP Explainability"
    p_s.font.size = Pt(14)
    p_s.font.color.rgb = TEAL_ACCENT

    # Left Card: Candidate & Guide Metadata
    add_card(slide, Inches(0.8), Inches(3.7), Inches(5.7), Inches(3.0), SURFACE_CARD, BORDER_COLOR)
    card_l = slide.shapes.add_textbox(Inches(1.1), Inches(3.85), Inches(5.1), Inches(2.7))
    tf_cl = card_l.text_frame
    tf_cl.word_wrap = True

    lines_l = [
        ("PROJECT METADATA", Pt(11), CYAN_ACCENT, True),
        ("Student Name:", Pt(10), TEXT_SLATE, False),
        ("[Student Name / Presenter Name]", Pt(12), TEXT_WHITE, True),
        ("Registration / Roll No:", Pt(10), TEXT_SLATE, False),
        ("[Registration / Roll Number]", Pt(12), TEXT_WHITE, True),
        ("Department:", Pt(10), TEXT_SLATE, False),
        ("Department of Computer Science & Engineering / Data Science", Pt(11), TEXT_WHITE, False),
        ("Institution / University:", Pt(10), TEXT_SLATE, False),
        ("[College / University Name]", Pt(11), TEXT_WHITE, False),
    ]
    for idx, (txt, sz, col, bld) in enumerate(lines_l):
        p = tf_cl.paragraphs[0] if idx == 0 else tf_cl.add_paragraph()
        p.text = txt
        p.font.size = sz
        p.font.color.rgb = col
        p.font.bold = bld
        if idx % 2 == 0 and idx > 0:
            p.space_before = Pt(4)

    # Right Card: Project Guide & Session Details
    add_card(slide, Inches(6.8), Inches(3.7), Inches(5.733), Inches(3.0), SURFACE_CARD, BORDER_COLOR)
    card_r = slide.shapes.add_textbox(Inches(7.1), Inches(3.85), Inches(5.1), Inches(2.7))
    tf_cr = card_r.text_frame
    tf_cr.word_wrap = True

    lines_r = [
        ("FACULTY GUIDANCE & EVALUATION", Pt(11), CYAN_ACCENT, True),
        ("Project Supervisor / Guide:", Pt(10), TEXT_SLATE, False),
        ("[Faculty Mentor Name & Designation]", Pt(12), TEXT_WHITE, True),
        ("Specialization / Research Group:", Pt(10), TEXT_SLATE, False),
        ("Machine Learning & Cyber-Financial Security Lab", Pt(11), TEXT_WHITE, False),
        ("Academic Year:", Pt(10), TEXT_SLATE, False),
        ("2025 – 2026", Pt(12), TEXT_WHITE, True),
        ("Evaluation Stage:", Pt(10), TEXT_SLATE, False),
        ("Final Project Defense / Capstone Review", Pt(11), EMERALD_ACCENT, True),
    ]
    for idx, (txt, sz, col, bld) in enumerate(lines_r):
        p = tf_cr.paragraphs[0] if idx == 0 else tf_cr.add_paragraph()
        p.text = txt
        p.font.size = sz
        p.font.color.rgb = col
        p.font.bold = bld
        if idx % 2 == 0 and idx > 0:
            p.space_before = Pt(4)


def build_slide_2_intro(prs):
    """Slide 2: Introduction to Financial Fraud & AI Defense."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "1.0 INTRODUCTION & CONTEXT", "Digital Payment Security & The Need for AI Defense",
               "Understanding the global financial impact of fraudulent transactions and modern automated detection paradigms.", 2)

    # Left Column: 3 Structured Conceptual Blocks
    add_card(slide, Inches(0.8), Inches(1.8), Inches(7.2), Inches(1.5), SURFACE_CARD, BORDER_COLOR)
    tb1 = slide.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(6.8), Inches(1.3))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "1. Proliferation of Digital Payment Channels"
    p1.font.bold = True
    p1.font.size = Pt(12)
    p1.font.color.rgb = CYAN_ACCENT
    p2 = tf1.add_paragraph()
    p2.text = "• Rapid growth in e-commerce, contactless POS, and mobile payments processes over 25 million transactions/hour globally.\n• Global card fraud losses exceeded $32.1 billion annually (Nilson Report, 2024), driven by card-not-present (CNP) scams, account takeovers, and synthetic identities."
    p2.font.size = Pt(10)
    p2.font.color.rgb = TEXT_WHITE

    add_card(slide, Inches(0.8), Inches(3.45), Inches(7.2), Inches(1.5), SURFACE_CARD, BORDER_COLOR)
    tb2 = slide.shapes.add_textbox(Inches(1.0), Inches(3.55), Inches(6.8), Inches(1.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p3 = tf2.paragraphs[0]
    p3.text = "2. Why Fraudulent Transactions Are Difficult to Detect"
    p3.font.bold = True
    p3.font.size = Pt(12)
    p3.font.color.rgb = AMBER_ACCENT
    p4 = tf2.add_paragraph()
    p4.text = "• Extreme Subtlety: Fraudsters mimic legitimate user purchase distributions, timing, and geographic locations.\n• Non-Stationary Dynamics: Fraud patterns evolve dynamically to evade legacy rule-based heuristics.\n• Masked Features: Financial privacy standards mandate PCA transformations (V1–V28), obscuring raw merchant and cardholder features."
    p4.font.size = Pt(10)
    p4.font.color.rgb = TEXT_WHITE

    add_card(slide, Inches(0.8), Inches(5.1), Inches(7.2), Inches(1.7), SURFACE_CARD, BORDER_COLOR)
    tb3 = slide.shapes.add_textbox(Inches(1.0), Inches(5.2), Inches(6.8), Inches(1.5))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    p5 = tf3.paragraphs[0]
    p5.text = "3. The Case for AegisGuard's Integrated AI Architecture"
    p5.font.bold = True
    p5.font.size = Pt(12)
    p5.font.color.rgb = EMERALD_ACCENT
    p6 = tf3.add_paragraph()
    p6.text = "• Pure supervised models miss novel, uncataloged zero-day fraud variants.\n• Pure anomaly detectors trigger excessive false positives on legitimate outlier spending.\n• AegisGuard unifies Supervised Classification (Random Forest), Unsupervised Anomaly Detection (Isolation Forest), Local SHAP Explainability, and Human-in-the-Loop Triage in real time."
    p6.font.size = Pt(10)
    p6.font.color.rgb = TEXT_WHITE

    # Right Column: 3 Key Metric / Fact Highlights
    add_card(slide, Inches(8.3), Inches(1.8), Inches(4.233), Inches(1.5), SURFACE_CARD, BORDER_COLOR)
    rb1 = slide.shapes.add_textbox(Inches(8.5), Inches(1.9), Inches(3.833), Inches(1.3))
    tf_rb1 = rb1.text_frame
    tf_rb1.word_wrap = True
    pr1 = tf_rb1.paragraphs[0]
    pr1.text = "$32.1B+"
    pr1.font.size = Pt(28)
    pr1.font.bold = True
    pr1.font.color.rgb = ROSE_ACCENT
    pr2 = tf_rb1.add_paragraph()
    pr2.text = "Annual worldwide payment card fraud losses, growing at 133% over recent decades (Aite-Novarica, 2022)."
    pr2.font.size = Pt(10)
    pr2.font.color.rgb = TEXT_SLATE

    add_card(slide, Inches(8.3), Inches(3.45), Inches(4.233), Inches(1.5), SURFACE_CARD, BORDER_COLOR)
    rb2 = slide.shapes.add_textbox(Inches(8.5), Inches(3.55), Inches(3.833), Inches(1.3))
    tf_rb2 = rb2.text_frame
    tf_rb2.word_wrap = True
    pr3 = tf_rb2.paragraphs[0]
    pr3.text = "< 10 ms"
    pr3.font.size = Pt(28)
    pr3.font.bold = True
    pr3.font.color.rgb = CYAN_ACCENT
    pr4 = tf_rb2.add_paragraph()
    pr4.text = "Stringent real-time decisioning SLA for payment authorization gateways without deteriorating checkout UX."
    pr4.font.size = Pt(10)
    pr4.font.color.rgb = TEXT_SLATE

    add_card(slide, Inches(8.3), Inches(5.1), Inches(4.233), Inches(1.7), SURFACE_CARD, BORDER_COLOR)
    rb3 = slide.shapes.add_textbox(Inches(8.5), Inches(5.2), Inches(3.833), Inches(1.5))
    tf_rb3 = rb3.text_frame
    tf_rb3.word_wrap = True
    pr5 = tf_rb3.paragraphs[0]
    pr5.text = "0.17% Base Rate"
    pr5.font.size = Pt(22)
    pr5.font.bold = True
    pr5.font.color.rgb = AMBER_ACCENT
    pr6 = tf_rb3.add_paragraph()
    pr6.text = "Severe benchmark class imbalance (only 492 fraud cases in 284,807 transactions), requiring minority-focused PR-AUC evaluation."
    pr6.font.size = Pt(10)
    pr6.font.color.rgb = TEXT_SLATE


def build_slide_3_problem_statement(prs):
    """Slide 3: Problem Statement with Class Imbalance Visual."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "2.0 PROBLEM FORMULATION", "Core Challenges in Automated Credit Card Fraud Detection",
               "Identifying the five fundamental research and operational bottlenecks in contemporary fraud prevention systems.", 3)

    # 5 Challenge Cards Grid (Left 2, Center 2, Right 1)
    challenges = [
        ("1. Extreme Class Imbalance",
         "Genuine transactions represent 99.83% of volume, while fraud accounts for only 0.17% (577:1 ratio). Conventional classifiers easily achieve 99.8% raw accuracy by predicting all transactions as genuine, completely failing minority fraud recovery.",
         ROSE_ACCENT),
        ("2. False-Positive Alert Fatigue",
         "A false-positive rate of even 1% on 25 million daily transactions generates 250,000 false alarms, choking compliance teams, incurring massive operational costs, and causing customer dissatisfaction from legitimate card declines.",
         AMBER_ACCENT),
        ("3. Concept Drift & Zero-Day Vectors",
         "Fraudsters constantly adapt tactics (e.g. distributed micro-transactions, merchant category hops). Supervised models trained strictly on historical labels cannot generalize to unseen, emerging fraud typologies without anomaly awareness.",
         CYAN_ACCENT),
        ("4. The 'Black-Box' Regulatory Dilemma",
         "Complex ensembles (Random Forest, XGBoost) lack natural interpretability. Global regulations (GDPR Art. 22, US Fair Credit Reporting Act) mandate clear explanations when financial transactions or accounts are blocked.",
         TEAL_ACCENT),
    ]

    card_coords = [
        (Inches(0.8), Inches(1.8), Inches(3.7), Inches(2.4)),
        (Inches(4.8), Inches(1.8), Inches(3.7), Inches(2.4)),
        (Inches(0.8), Inches(4.4), Inches(3.7), Inches(2.4)),
        (Inches(4.8), Inches(4.4), Inches(3.7), Inches(2.4)),
    ]

    for (title, desc, col), (x, y, w, h) in zip(challenges, card_coords):
        add_card(slide, x, y, w, h, SURFACE_CARD, BORDER_COLOR)
        tb = slide.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), w - Inches(0.4), h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.bold = True
        pt.font.size = Pt(12)
        pt.font.color.rgb = col
        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.size = Pt(9.5)
        pd.font.color.rgb = TEXT_WHITE
        pd.space_before = Pt(4)

    # Right Card: Visual Demonstration of Class Imbalance
    add_card(slide, Inches(8.8), Inches(1.8), Inches(3.733), Inches(5.0), SURFACE_CARD, BORDER_COLOR)
    tb_r = slide.shapes.add_textbox(Inches(9.0), Inches(2.0), Inches(3.333), Inches(4.6))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p_rt = tf_r.paragraphs[0]
    p_rt.text = "DATASET SKEWNESS PROFILE"
    p_rt.font.bold = True
    p_rt.font.size = Pt(11)
    p_rt.font.color.rgb = CYAN_ACCENT

    p_rd = tf_r.add_paragraph()
    p_rd.text = "European Credit Card Benchmark (Kaggle/ULB):\n• Total Records: 284,807 transactions\n• Genuine (Class 0): 284,315 (99.827%)\n• Fraudulent (Class 1): 492 (0.173%)\n• Severe Imbalance Ratio: 577 : 1"
    p_rd.font.size = Pt(10)
    p_rd.font.color.rgb = TEXT_WHITE
    p_rd.space_before = Pt(6)

    # Visual Bar 1: Legitimate
    bar1 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.0), Inches(3.8), Inches(3.2), Inches(0.45))
    bar1.fill.solid()
    bar1.fill.fore_color.rgb = RGBColor(16, 185, 129)
    bar1.line.fill.background()
    bar1.text_frame.paragraphs[0].text = "Legitimate: 284,315 (99.83%)"
    bar1.text_frame.paragraphs[0].font.size = Pt(9)
    bar1.text_frame.paragraphs[0].font.bold = True
    bar1.text_frame.paragraphs[0].font.color.rgb = RGBColor(10, 14, 26)

    # Visual Bar 2: Fraudulent
    bar2 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.0), Inches(4.35), Inches(0.5), Inches(0.45))
    bar2.fill.solid()
    bar2.fill.fore_color.rgb = ROSE_ACCENT
    bar2.line.fill.background()

    lbl_f = slide.shapes.add_textbox(Inches(9.55), Inches(4.35), Inches(2.6), Inches(0.45))
    lbl_f.text_frame.paragraphs[0].text = "Fraud: 492 (0.17%)"
    lbl_f.text_frame.paragraphs[0].font.size = Pt(9)
    lbl_f.text_frame.paragraphs[0].font.bold = True
    lbl_f.text_frame.paragraphs[0].font.color.rgb = ROSE_ACCENT

    # Technical takeaway box inside right card
    p_sum = tf_r.add_paragraph()
    p_sum.space_before = Pt(110)
    p_sum.text = "CRITICAL IMPLICATION:\nEvaluating solely on ROC-AUC yields artificially high scores (>0.97) for mediocre models. Precision-Recall AUC (PR-AUC) must be adopted as the primary optimization metric (Borketey, 2024)."
    p_sum.font.size = Pt(9)
    p_sum.font.bold = True
    p_sum.font.color.rgb = TEAL_ACCENT


def build_slide_4_objectives(prs):
    """Slide 4: Project Objectives."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "3.0 PROJECT OBJECTIVES", "System Engineering & Machine Learning Research Goals",
               "Seven measurable, verified objectives implemented in the AegisGuard production architecture.", 4)

    objectives = [
        ("Obj 1: Leakage-Free Preprocessing Pipeline",
         "Implement a strict train/val/test data partitioning strategy that isolates StandardScaler transformations and SMOTE synthetic oversampling exclusively to the training partition, eliminating validation and test set contamination."),
        ("Obj 2: Multi-Model Benchmark & Champion Selection",
         "Train, evaluate, and benchmark 5 candidate supervised learning algorithms (Random Forest, XGBoost, HistGradientBoosting, Decision Tree, Logistic Regression) using minority-focused PR-AUC as the primary selection criterion."),
        ("Obj 3: Unsupervised Zero-Day Anomaly Detection",
         "Integrate an Isolation Forest model trained solely on legitimate spending habits to provide an orthogonal anomaly score, detecting unseen spending variations without relying on historical fraud labels."),
        ("Obj 4: Real-Time Local SHAP Explainability",
         "Incorporate a dynamic SHAP TreeExplainer service that computes additive feature attribution waterfalls for flagged transactions, exposing positive and negative risk contributors for compliance auditing."),
        ("Obj 5: High-Performance FastAPI Ingress & Persistence",
         "Develop an asynchronous FastAPI backend delivering sub-10ms inference latencies, full request validation via Pydantic schemas, and structured SQLite audit logging of transactions, predictions, and alerts."),
        ("Obj 6: Full-Featured Operational Dashboard & Live Streaming",
         "Construct a modern React 19 / Vite analyst interface with live WebSocket event streaming, risk-stratified live transaction tickers, interactive transaction inspectors, and human-in-the-loop triage management."),
        ("Obj 7: End-to-End Simulation & Batch CSV Scoring",
         "Engineer an automated transaction replay simulator and batch CSV evaluation module allowing analysts to test synthetic transaction streams and bulk audit historical ledgers."),
    ]

    # Two-column layout of objective cards
    left_objs = objectives[:4]
    right_objs = objectives[4:]

    for idx, (title, body) in enumerate(left_objs):
        top_pos = Inches(1.8 + idx * 1.25)
        add_card(slide, Inches(0.8), top_pos, Inches(5.7), Inches(1.15), SURFACE_CARD, BORDER_COLOR)
        tb = slide.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.08), Inches(5.3), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.bold = True
        p_t.font.size = Pt(11)
        p_t.font.color.rgb = CYAN_ACCENT
        p_b = tf.add_paragraph()
        p_b.text = body
        p_b.font.size = Pt(8.8)
        p_b.font.color.rgb = TEXT_WHITE

    for idx, (title, body) in enumerate(right_objs):
        top_pos = Inches(1.8 + idx * 1.68)
        add_card(slide, Inches(6.8), top_pos, Inches(5.733), Inches(1.55), SURFACE_CARD, BORDER_COLOR)
        tb = slide.shapes.add_textbox(Inches(7.0), top_pos + Inches(0.1), Inches(5.333), Inches(1.35))
        tf = tb.text_frame
        tf.word_wrap = True
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.bold = True
        p_t.font.size = Pt(11)
        p_t.font.color.rgb = TEAL_ACCENT
        p_b = tf.add_paragraph()
        p_b.text = body
        p_b.font.size = Pt(9.2)
        p_b.font.color.rgb = TEXT_WHITE


def build_slide_5_lit_paper1(prs):
    """Slide 5: Literature Survey - Paper 1 (Borketey, 2024) with all 7 fields."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "4.1 LITERATURE SURVEY — PRIMARY FOUNDATION [1]",
               "Paper 1: Real-Time Fraud Detection Using Machine Learning (Borketey, 2024)",
               "Comprehensive breakdown across all seven required academic evaluation criteria.", 5)

    headers = ["Evaluation Field", "Extracted Verified Academic Information"]
    rows = [
        ["1. Author Name(s)", "Benjamin Borketey (Department of Economics, The University of Akron, Akron, Ohio, USA)"],
        ["2. Publication Year", "2024 (Published May 17, 2024; JDAIP, Vol. 12, No. 2, pp. 189–209; DOI: 10.4236/jdaip.2024.122011)"],
        ["3. Exact Paper Title", "Real-Time Fraud Detection Using Machine Learning"],
        ["4. Dataset Used", "Kaggle European Credit Card Fraud Dataset (284,807 transactions, 492 frauds, 0.172% fraud rate; features Time, Amount, V1–V28 PCA components)"],
        ["5. Technology / Algorithm", "Logistic Regression, Linear Discriminant Analysis (LDA), K-Nearest Neighbors (KNN), CART Decision Tree, Naive Bayes, Support Vector Machine (SVM), Random Forest (RF), XGBoost, LightGBM; SMOTE Oversampling; SHAP explainability"],
        ["6. Reported Experimental Results", "Random Forest achieved best overall performance on test set: KS = 0.9090, AUC = 0.9191, F1-Score = 0.8352, Recall = 0.8385, PR-AUC = 0.8354, Precision = 0.8321, Accuracy = 0.9995. Successfully identified 92% of transactions in top decile [90–100] as fraud."],
        ["7. Advantages / Main Contribution", "1) Empirically established Random Forest superiority for imbalanced fraud data; 2) Proved PR-AUC is superior to ROC-AUC for evaluation; 3) Formulated 0–100 score decile binning following Visa's Provisioning Intelligence; 4) Pioneered SHAP summary & force plots for V14/V12 local interpretability."],
    ]

    col_widths = [2.6, 9.133]
    add_table_custom(slide, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.9), headers, rows, col_widths)


def build_slide_6_lit_papers2_3(prs):
    """Slide 6: Literature Survey - Papers 2 and 3 Comparative Table."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "4.2 LITERATURE SURVEY — ADVANCED STREAMING & ENSEMBLES [2, 3]",
               "Comparative Review: Charizanos et al. (2024) & Talukder et al. (2024)",
               "Rigorous analysis of streaming fuzzy classification and multistage hierarchical ensemble frameworks.", 6)

    headers = [
        "Evaluation Field",
        "Paper 2: Charizanos et al. (2024) [2]",
        "Paper 3: Talukder et al. (2024) [3]"
    ]

    rows = [
        ["1. Author Name(s)",
         "Georgios Charizanos, Haydar Demirhan, Duygu Icen (RMIT University, Australia & Hacettepe University, Turkiye)",
         "Md. Alamin Talukder, Majdi Khalid, Md Ashraf Uddin (IUBAT Bangladesh, Umm Al-Qura Univ. Saudi Arabia, Deakin Univ. Australia)"],
        ["2. Publication Year",
         "2024 (Expert Systems with Applications, Vol. 252, Part A, Art. 124127, Elsevier; DOI: 10.1016/j.eswa.2024.124127)",
         "2024 (Journal of Big Data, Vol. 11, Art. 168, Springer; DOI: 10.1186/s40537-024-00996-5)"],
        ["3. Exact Paper Title",
         "An online fuzzy fraud detection framework for credit card transactions",
         "An integrated multistage ensemble machine learning model for fraudulent transaction detection"],
        ["4. Dataset Used",
         "European credit card fraud benchmark dataset (284,807 transactions, 0.17% fraud prevalence) & simulated transaction stream",
         "Public Kaggle Credit Card Fraud Detection dataset (284,807 transactions, 492 fraud cases)"],
        ["5. Technology / Algorithm",
         "Online Fuzzy Logistic Regression (FLR) with Triangular Fuzzy Numbers (TFN), probabilistic sampling for non-stationary streams, benchmarked vs. crisp ML",
         "Integrated Multistage Ensemble ML (IMEML / EIBMC): Independent (EIC), Bagging (EBC), and Meta-Classifiers (EMC) with Instance Hardness Threshold (IHT)"],
        ["6. Reported Results",
         "Online streaming (5,000 tx): Specificity = 0.995, Sensitivity = 0.909, F1-Score = 0.526, MCC = 0.809. Latency = 5.6 ms/transaction. Crisp ML failed (sens. < 0.50).",
         "Proposed EIBMC model with IHT achieved: Accuracy = 99.94%, Precision = 99.91%, Recall = 99.14%, F1-Score = 99.52%, AUC = 100%."],
        ["7. Advantages / Contribution",
         "Overcomes class imbalance and complete separation in transaction streams; achieves 5.6 ms latency and defuzzified odds ratios for feature impact.",
         "Demonstrates that hierarchical multistage ensembling with boundary-aware undersampling (IHT) removes noisy majority samples and eliminates false alarms."],
    ]

    col_widths = [2.2, 4.75, 4.75]
    add_table_custom(slide, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.9), headers, rows, col_widths)


def build_slide_7_research_gap(prs):
    """Slide 7: Research Gap Analysis Table."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "5.0 RESEARCH GAP ANALYSIS", "Identified Academic Gaps & AegisGuard's Concrete Contributions",
               "Synthesizing the limitations of reviewed literature and delineating engineering vs. algorithmic contributions.", 7)

    headers = [
        "Research Dimension",
        "Findings in Reviewed Literature [1, 2, 3]",
        "Identified Limitation / Practical Gap",
        "AegisGuard Proposed System Contribution"
    ]

    rows = [
        ["Class Imbalance & Evaluation Metrics",
         "Borketey [1] & Talukder [3] note that 99.8% raw accuracy is deceptive and adopt PR-AUC / MCC.",
         "Many systems still rely on static 0.5 probability thresholds, causing severe false alarm cascades in production.",
         "Implements configurable operational risk tiers (Low <0.30, Medium 0.30–0.70, High ≥0.70) tuned to business risk appetite."],
        ["Zero-Day / Novel Fraud Detection",
         "Existing papers focus purely on supervised classifiers trained on historical labeled fraud patterns.",
         "Supervised models are inherently blind to uncataloged, emerging transaction vectors never seen in training.",
         "Pairs supervised Random Forest with unsupervised Isolation Forest trained on normal transactions to flag behavioral anomalies."],
        ["Model Interpretability & Auditability",
         "Borketey [1] applied offline SHAP plots; Charizanos [2] derived defuzzified odds ratios.",
         "Explanations are computed post-hoc on static notebooks rather than generated live during transaction ingestion.",
         "Integrates real-time SHAP TreeExplainer generating immediate directional feature waterfalls (e.g. V14, V4) for each flagged alert."],
        ["End-to-End System Integration",
         "All 3 papers evaluate models purely as offline mathematical experiments without software deployment.",
         "Lacks operational integration: no live REST API, WebSocket event broadcasting, or human-in-the-loop triage UI.",
         "Delivers a complete enterprise full-stack platform: FastAPI backend (<10ms SLA), SQLite persistence, and React 19 triage dashboard."],
    ]

    col_widths = [1.8, 3.2, 3.2, 3.533]
    add_table_custom(slide, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.9), headers, rows, col_widths)


def build_slide_8_methodology(prs):
    """Slide 8: Proposed Methodology & Pipeline Workflow."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "6.0 PROPOSED WORK & METHODOLOGY", "AegisGuard 14-Stage Detection & Triage Pipeline",
               "Rigorous academic data isolation, dual-engine inference, dynamic explainability, and analyst triage lifecycle.", 8)

    # 4 Macro Phase Cards
    phases = [
        ("PHASE 1: DATA ENGINEERING & ISOLATION", CYAN_ACCENT, [
            "1. Dataset Ingestion: Kaggle European credit card benchmark (284,807 transactions, 30 features).",
            "2. Data Integrity Checks: Verified 0 missing values; identified 1,081 duplicate transactions.",
            "3. Stratified Partitioning: Split BEFORE transformation into Train (70%), Validation (10%), Test (20%).",
            "4. Train-Only Preprocessing: StandardScaler fitted solely on training split (Time, Amount).",
            "5. Strict Train-Only SMOTE: Synthetically balanced minority fraud from 345 to 199,019 samples on train only.",
        ]),
        ("PHASE 2: DUAL-ENGINE MODEL TRAINING", EMERALD_ACCENT, [
            "6. Supervised Benchmark: Trained RF, XGBoost, HistGradientBoosting, Decision Tree, Logistic Regression.",
            "7. Unsupervised Isolation Forest: Trained strictly on genuine (Class 0) transactions (contamination=0.002).",
            "8. Validation Selection: Random Forest selected champion (highest validation PR-AUC = 0.749, recall ≥ 70%).",
            "9. Held-Out Evaluation: Evaluated champion strictly on untouched 56,962 test transactions (PR-AUC: 0.8212).",
        ]),
        ("PHASE 3: REAL-TIME INFERENCE & XAI", AMBER_ACCENT, [
            "10. FastAPI Service Ingress: High-speed endpoint validating input vectors via Pydantic schemas.",
            "11. Dual-Engine Scoring: Concurrently derives fraud probability P(Fraud) and Isolation Forest anomaly score.",
            "12. Dynamic SHAP Explainer: TreeExplainer extracts additive feature attributions for elevated-risk transactions.",
        ]),
        ("PHASE 4: PERSISTENCE & ANALYST TRIAGE", ROSE_ACCENT, [
            "13. SQLite Audit Store: Fully logs transaction vectors, model versions, probabilities, and triage state.",
            "14. WebSocket Broadcast & Dashboard: Emits live events to React UI; analysts acknowledge, confirm, or dismiss alerts.",
        ]),
    ]

    card_positions = [
        (Inches(0.8), Inches(1.8), Inches(5.7), Inches(2.4)),
        (Inches(6.8), Inches(1.8), Inches(5.733), Inches(2.4)),
        (Inches(0.8), Inches(4.4), Inches(5.7), Inches(2.4)),
        (Inches(6.8), Inches(4.4), Inches(5.733), Inches(2.4)),
    ]

    for (p_title, p_col, items), (x, y, w, h) in zip(phases, card_positions):
        add_card(slide, x, y, w, h, SURFACE_CARD, BORDER_COLOR)
        tb = slide.shapes.add_textbox(x + Inches(0.2), y + Inches(0.12), w - Inches(0.4), h - Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = p_title
        pt.font.bold = True
        pt.font.size = Pt(11)
        pt.font.color.rgb = p_col

        for item in items:
            pi = tf.add_paragraph()
            pi.text = item
            pi.font.size = Pt(8.8)
            pi.font.color.rgb = TEXT_WHITE
            pi.space_before = Pt(2.5)


def build_slide_9_flowchart(prs):
    """Slide 9: Editable PowerPoint Flowchart of Detection & Triage."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "7.0 PROPOSED WORK FLOWCHART", "Real-Time Transaction Scoring & Triage Decision Logic",
               "Fully editable flowchart illustrating end-to-end data transformation, dual-engine scoring, and triage loops.", 9)

    # Row 1: START -> Ingress -> Validation -> Scaling
    r1_boxes = [
        ("START", Inches(0.8), Inches(2.0), Inches(1.5), Inches(0.7), MSO_SHAPE.ROUNDED_RECTANGLE, CYAN_ACCENT, BG_DARK, True),
        ("Transaction Ingress\n(Stream / CSV / API)", Inches(2.8), Inches(1.95), Inches(2.4), Inches(0.8), MSO_SHAPE.RECTANGLE, SURFACE_CARD, TEXT_WHITE, False),
        ("Pydantic Schema\nValidation", Inches(5.7), Inches(1.95), Inches(2.1), Inches(0.8), MSO_SHAPE.RECTANGLE, SURFACE_CARD, TEXT_WHITE, False),
        ("StandardScaler\n(Time & Amount)", Inches(8.3), Inches(1.95), Inches(2.2), Inches(0.8), MSO_SHAPE.RECTANGLE, SURFACE_CARD, TEXT_WHITE, False),
    ]

    for text, x, y, w, h, shape_type, fill_c, text_c, is_bold in r1_boxes:
        s = slide.shapes.add_shape(shape_type, x, y, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = fill_c
        s.line.color.rgb = CYAN_ACCENT
        s.line.width = Pt(1)
        p = s.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = text
        p.font.size = Pt(9.5)
        p.font.bold = is_bold
        p.font.color.rgb = text_c

    # Arrows Row 1
    arrow_pairs = [
        (Inches(2.3), Inches(2.35), Inches(0.5), Inches(0)),
        (Inches(5.2), Inches(2.35), Inches(0.5), Inches(0)),
        (Inches(7.8), Inches(2.35), Inches(0.5), Inches(0)),
    ]
    for ax, ay, aw, ah in arrow_pairs:
        arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, ax, ay - Inches(0.06), aw, Inches(0.12))
        arr.fill.solid()
        arr.fill.fore_color.rgb = CYAN_ACCENT
        arr.line.fill.background()

    # Split to Dual Engines (Row 2)
    # Fork down arrow
    fork = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(9.3), Inches(2.8), Inches(0.15), Inches(0.45))
    fork.fill.solid()
    fork.fill.fore_color.rgb = CYAN_ACCENT
    fork.line.fill.background()

    # Engine A: Random Forest (Supervised)
    s_rf = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.4), Inches(3.4), Inches(2.8), Inches(0.85))
    s_rf.fill.solid()
    s_rf.fill.fore_color.rgb = SURFACE_CARD
    s_rf.line.color.rgb = EMERALD_ACCENT
    s_rf.line.width = Pt(1.5)
    p_rf = s_rf.text_frame.paragraphs[0]
    p_rf.alignment = PP_ALIGN.CENTER
    p_rf.text = "Random Forest Champion\nFraud Probability: P(Fraud) ∈ [0, 1]"
    p_rf.font.size = Pt(9.5)
    p_rf.font.bold = True
    p_rf.font.color.rgb = EMERALD_ACCENT

    # Engine B: Isolation Forest (Unsupervised)
    s_if = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.6), Inches(3.4), Inches(2.9), Inches(0.85))
    s_if.fill.solid()
    s_if.fill.fore_color.rgb = SURFACE_CARD
    s_if.line.color.rgb = TEAL_ACCENT
    s_if.line.width = Pt(1.5)
    p_if = s_if.text_frame.paragraphs[0]
    p_if.alignment = PP_ALIGN.CENTER
    p_if.text = "Isolation Forest Detector\nAnomaly Score (Unusualness Flag)"
    p_if.font.size = Pt(9.5)
    p_if.font.bold = True
    p_if.font.color.rgb = TEAL_ACCENT

    # Decision Diamond (Row 3)
    diamond = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(8.3), Inches(4.55), Inches(2.3), Inches(1.2))
    diamond.fill.solid()
    diamond.fill.fore_color.rgb = RGBColor(40, 25, 45)
    diamond.line.color.rgb = ROSE_ACCENT
    diamond.line.width = Pt(1.5)
    p_d = diamond.text_frame.paragraphs[0]
    p_d.alignment = PP_ALIGN.CENTER
    p_d.text = "P(Fraud) ≥ 0.70\nOR Anomaly?"
    p_d.font.size = Pt(9)
    p_d.font.bold = True
    p_d.font.color.rgb = ROSE_ACCENT

    # Left Branch: Low Risk / Approved
    s_low = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.5), Inches(4.75), Inches(2.6), Inches(0.8))
    s_low.fill.solid()
    s_low.fill.fore_color.rgb = RGBColor(15, 35, 30)
    s_low.line.color.rgb = EMERALD_ACCENT
    p_low = s_low.text_frame.paragraphs[0]
    p_low.alignment = PP_ALIGN.CENTER
    p_low.text = "LOW RISK (Approved)\nLog & Stream to Live Feed"
    p_low.font.size = Pt(9)
    p_low.font.color.rgb = EMERALD_ACCENT

    # Right Branch: High/Medium Risk -> SHAP -> Alert
    s_shap = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(11.0), Inches(4.75), Inches(1.8), Inches(0.8))
    s_shap.fill.solid()
    s_shap.fill.fore_color.rgb = RGBColor(35, 20, 30)
    s_shap.line.color.rgb = ROSE_ACCENT
    p_shap = s_shap.text_frame.paragraphs[0]
    p_shap.alignment = PP_ALIGN.CENTER
    p_shap.text = "SHAP Explainer\nFeature Waterfall"
    p_shap.font.size = Pt(9)
    p_shap.font.color.rgb = ROSE_ACCENT

    # Bottom Row: Persistent DB -> Triage Queue -> Review -> END
    b_row = [
        ("SQLite Audit Store\n& WebSocket Broadcast", Inches(0.8), Inches(6.0), Inches(2.6), Inches(0.75), MSO_SHAPE.ROUNDED_RECTANGLE, SURFACE_CARD, TEXT_WHITE, False),
        ("Analyst Triage Queue\n(PENDING)", Inches(3.8), Inches(6.0), Inches(2.4), Inches(0.75), MSO_SHAPE.ROUNDED_RECTANGLE, SURFACE_CARD, AMBER_ACCENT, True),
        ("Investigator Review\n(Acknowledge / Notes)", Inches(6.6), Inches(6.0), Inches(2.6), Inches(0.75), MSO_SHAPE.ROUNDED_RECTANGLE, SURFACE_CARD, TEXT_WHITE, False),
        ("RESOLVED\n(Confirmed / False Alarm)", Inches(9.6), Inches(6.0), Inches(2.9), Inches(0.75), MSO_SHAPE.ROUNDED_RECTANGLE, EMERALD_ACCENT, BG_DARK, True),
    ]

    for text, x, y, w, h, shape_type, fill_c, text_c, is_bold in b_row:
        s = slide.shapes.add_shape(shape_type, x, y, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = fill_c
        s.line.color.rgb = CYAN_ACCENT
        s.line.width = Pt(1)
        p = s.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = text
        p.font.size = Pt(9.5)
        p.font.bold = is_bold
        p.font.color.rgb = text_c

    # Connecting bottom arrows
    b_arrows = [
        (Inches(3.4), Inches(6.32), Inches(0.4), Inches(0)),
        (Inches(6.2), Inches(6.32), Inches(0.4), Inches(0)),
        (Inches(9.2), Inches(6.32), Inches(0.4), Inches(0)),
    ]
    for ax, ay, aw, ah in b_arrows:
        arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, ax, ay - Inches(0.05), aw, Inches(0.1))
        arr.fill.solid()
        arr.fill.fore_color.rgb = CYAN_ACCENT
        arr.line.fill.background()


def build_slide_10_architecture(prs):
    """Slide 10: Layered System Architecture."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "8.0 SYSTEM ARCHITECTURE", "Three-Tier Enterprise Architecture Diagram",
               "Layered separation of ingress channels, ML intelligence services, persistence, and analyst dashboards.", 10)

    # 3 Layer Horizontal Bands
    layers = [
        ("TIER 1: TRANSACTION INGRESS & REPLAY LAYER", CYAN_ACCENT, Inches(1.8), Inches(1.4), [
            ("Transaction Stream Simulator", "Background worker replaying Kaggle creditcard.csv rows at 1–20+ tx/sec with configurable interval/batch size."),
            ("Batch CSV Uploader", "Direct multipart file endpoint scoring bulk transaction files (up to 500 rows/batch interactive)."),
            ("Client REST Ingress", "Synchronous HTTP POST /api/transactions for point-of-sale and merchant checkout integration."),
        ]),
        ("TIER 2: BACKEND CORE & DUAL-ENGINE ML SERVICES (FastAPI + Scikit-Learn)", EMERALD_ACCENT, Inches(3.35), Inches(2.0), [
            ("Schema Validation & Preprocessing", "Pydantic models ensuring 30-feature vector integrity; StandardScaler scales Time/Amount."),
            ("Random Forest Supervised Classifier", "50-tree ensemble producing calibrated fraud probability P(Fraud); PR-AUC 0.8212 champion."),
            ("Isolation Forest Anomaly Detector", "Unsupervised tree estimator measuring isolation path length on normal spending patterns."),
            ("SHAP Dynamic Explainer", "TreeExplainer calculating exact local feature pushes (V14, V4, V12) on flagged events."),
            ("SQLite DB & WebSocket Broadcaster", "Persistent tables (transactions, predictions, alerts) and pub/sub WebSocket manager (<5ms)."),
        ]),
        ("TIER 3: OPERATIONAL ANALYST PRESENTATION LAYER (React 19 + Vite)", AMBER_ACCENT, Inches(5.5), Inches(1.4), [
            ("Live Transaction Monitor", "Real-time ticker table with color-coded risk pills (LOW/MED/HIGH) and anomaly indicators."),
            ("Transaction Inspector Modal", "Full 30-feature explorer with visual SHAP feature contribution bar chart."),
            ("Alert Triage Center", "Audited review queue supporting ACKNOWLEDGE, CONFIRM FRAUD, and MARK LEGITIMATE actions."),
            ("Model Diagnostics Studio", "Interactive multi-model comparison matrix, ROC/PR curve galleries, and one-click retraining."),
        ]),
    ]

    for l_title, l_col, top_pos, h_pos, components in layers:
        add_card(slide, Inches(0.8), top_pos, Inches(11.733), h_pos, SURFACE_CARD, BORDER_COLOR)

        # Title bar on left
        t_box = slide.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.08), Inches(11.3), Inches(0.3))
        p_t = t_box.text_frame.paragraphs[0]
        p_t.text = l_title
        p_t.font.bold = True
        p_t.font.size = Pt(10.5)
        p_t.font.color.rgb = l_col

        # Sub-boxes for components
        num_comp = len(components)
        comp_w = (11.333 - (num_comp - 1) * 0.15) / num_comp

        for c_idx, (c_name, c_desc) in enumerate(components):
            c_left = Inches(1.0 + c_idx * (comp_w + 0.15))
            c_top = top_pos + Inches(0.38)
            c_height = h_pos - Inches(0.48)

            c_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, c_top, Inches(comp_w), c_height)
            c_shape.fill.solid()
            c_shape.fill.fore_color.rgb = RGBColor(14, 20, 36)
            c_shape.line.color.rgb = BORDER_COLOR
            c_shape.line.width = Pt(1)

            tb_c = slide.shapes.add_textbox(c_left + Inches(0.08), c_top + Inches(0.05), Inches(comp_w - 0.16), c_height - Inches(0.1))
            tf_c = tb_c.text_frame
            tf_c.word_wrap = True
            p_cn = tf_c.paragraphs[0]
            p_cn.text = c_name
            p_cn.font.bold = True
            p_cn.font.size = Pt(9)
            p_cn.font.color.rgb = TEXT_WHITE
            p_cd = tf_c.add_paragraph()
            p_cd.text = c_desc
            p_cd.font.size = Pt(8)
            p_cd.font.color.rgb = TEXT_SLATE
            p_cd.space_before = Pt(2)


def build_slide_11_results(prs):
    """Slide 11: Experimental Results & Benchmark Discussion."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "9.0 EXPERIMENTAL RESULTS & DISCUSSION", "Model Evaluation on Held-Out Test Set (56,962 Transactions)",
               "Rigorous empirical benchmark confirming Random Forest superiority in alignment with Borketey (2024).", 11)

    # Left: Benchmark Metrics Table
    headers = ["Model Algorithm", "PR-AUC", "ROC-AUC", "F1", "Recall", "Precision", "Latency", "Outcome"]
    rows = [
        ["Random Forest [Champion]", "0.8212", "0.9798", "0.7642", "82.65%", "71.05%", "1.25 ms", "CHAMPION"],
        ["XGBoost Classifier", "0.8172", "0.9721", "0.3085", "88.78%", "18.67%", "0.81 ms", "Evaluated"],
        ["HistGradientBoosting", "0.7858", "0.9732", "0.2355", "86.73%", "13.62%", "2.58 ms", "Evaluated"],
        ["Logistic Regression", "0.7297", "0.9731", "0.1098", "90.82%", "5.84%", "0.15 ms", "Baseline"],
        ["Decision Tree (CART)", "0.4664", "0.9028", "0.1995", "83.67%", "11.33%", "0.11 ms", "Baseline"],
    ]
    col_widths = [2.2, 0.9, 0.9, 0.8, 0.9, 0.9, 0.9, 1.1]
    add_table_custom(slide, Inches(0.8), Inches(1.8), Inches(8.6), Inches(2.4), headers, rows, col_widths)

    # Right: Confusion Matrix Stat Card
    add_card(slide, Inches(9.6), Inches(1.8), Inches(2.933), Inches(2.4), SURFACE_CARD, BORDER_COLOR)
    cm_tb = slide.shapes.add_textbox(Inches(9.75), Inches(1.9), Inches(2.6), Inches(2.2))
    tf_cm = cm_tb.text_frame
    tf_cm.word_wrap = True

    p_cmt = tf_cm.paragraphs[0]
    p_cmt.text = "TEST CONFUSION MATRIX"
    p_cmt.font.bold = True
    p_cmt.font.size = Pt(10.5)
    p_cmt.font.color.rgb = CYAN_ACCENT

    p_cmd = tf_cm.add_paragraph()
    p_cmd.text = "Held-Out Test Set (n = 56,962):\n• True Positives (TP): 81 frauds caught\n• False Negatives (FN): 17 missed\n• False Positives (FP): 33 false alarms\n• True Negatives (TN): 56,831 genuine\n\nFalse Alarm Rate: 0.058%\n(Only 33 false alarms / 56,864 genuine)"
    p_cmd.font.size = Pt(8.8)
    p_cmd.font.color.rgb = TEXT_WHITE
    p_cmd.space_before = Pt(4)

    # Bottom Area: Embed Actual Generated Curves Image or Structured Analysis
    # Let's check if pr_curves.png or confusion_matrix.png exist
    pr_img_path = REPORTS_DIR / "pr_curves.png"
    cm_img_path = REPORTS_DIR / "confusion_matrix.png"

    if pr_img_path.exists():
        add_card(slide, Inches(0.8), Inches(4.35), Inches(5.7), Inches(2.55), SURFACE_CARD, BORDER_COLOR)
        # Header for image card
        tb_img = slide.shapes.add_textbox(Inches(0.9), Inches(4.4), Inches(5.5), Inches(0.3))
        tb_img.text_frame.paragraphs[0].text = "DIAGNOSTIC PR CURVES (GENERATED IN PIPELINE)"
        tb_img.text_frame.paragraphs[0].font.size = Pt(9.5)
        tb_img.text_frame.paragraphs[0].font.bold = True
        tb_img.text_frame.paragraphs[0].font.color.rgb = CYAN_ACCENT
        slide.shapes.add_picture(str(pr_img_path), Inches(1.0), Inches(4.75), width=Inches(5.3), height=Inches(2.05))

    # Bottom Right: Academic Findings Discussion
    add_card(slide, Inches(6.8), Inches(4.35), Inches(5.733), Inches(2.55), SURFACE_CARD, BORDER_COLOR)
    tb_disc = slide.shapes.add_textbox(Inches(7.0), Inches(4.4), Inches(5.333), Inches(2.45))
    tf_disc = tb_disc.text_frame
    tf_disc.word_wrap = True

    pd1 = tf_disc.paragraphs[0]
    pd1.text = "EMPIRICAL FINDINGS & BENCHMARK DISCUSSION"
    pd1.font.bold = True
    pd1.font.size = Pt(10.5)
    pd1.font.color.rgb = EMERALD_ACCENT

    insights = [
        "1. Random Forest Wins on PR-AUC: Random Forest achieved the highest PR-AUC (0.8212), capturing 82.65% of all frauds with 71.05% precision, matching Borketey's (2024) conclusions.",
        "2. XGBoost Precision Trade-off: While XGBoost achieved high recall (88.78%), its precision dropped to 18.67% (higher false alarms), yielding an inferior F1-score (0.3085 vs 0.7642).",
        "3. Deceptive ROC-AUC: All top 4 models achieved ROC-AUC > 0.97, proving ROC-AUC is insensitive to false alarm explosions in imbalanced credit fraud data.",
        "4. Sub-Millisecond Speed: Both Random Forest (1.25 ms) and XGBoost (0.81 ms) easily satisfy the <10ms real-time point-of-sale SLA.",
    ]
    for insight in insights:
        p = tf_disc.add_paragraph()
        p.text = insight
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(3)


def build_slide_12_explainability(prs):
    """Slide 12: Explainability & Alert Triage Workflow."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "10.0 EXPLAINABILITY & TRIAGE WORKFLOW", "SHAP Feature Attribution & Operational Investigation",
               "Deconstructing black-box predictions into compliant feature attributions and audited triage states.", 12)

    # Left: Embed feature_importance.png
    feat_img_path = REPORTS_DIR / "feature_importance.png"
    add_card(slide, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0), SURFACE_CARD, BORDER_COLOR)

    tb_f = slide.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(5.3), Inches(0.35))
    tb_f.text_frame.paragraphs[0].text = "GLOBAL FEATURE IMPORTANCE (RANDOM FOREST)"
    tb_f.text_frame.paragraphs[0].font.bold = True
    tb_f.text_frame.paragraphs[0].font.size = Pt(11)
    tb_f.text_frame.paragraphs[0].font.color.rgb = CYAN_ACCENT

    if feat_img_path.exists():
        slide.shapes.add_picture(str(feat_img_path), Inches(1.0), Inches(2.3), width=Inches(5.3), height=Inches(3.0))

    tb_note = slide.shapes.add_textbox(Inches(1.0), Inches(5.4), Inches(5.3), Inches(1.3))
    tf_note = tb_note.text_frame
    tf_note.word_wrap = True
    pn1 = tf_note.paragraphs[0]
    pn1.text = "Key Discriminative Features:"
    pn1.font.bold = True
    pn1.font.size = Pt(9.5)
    pn1.font.color.rgb = TEAL_ACCENT
    pn2 = tf_note.add_paragraph()
    pn2.text = "• V14, V4, V12, V10, and Amount dominate the ensemble's decision trees.\n• Negative spikes in V14 & V12 combined with high positive V4 values strongly correlate with fraudulent card takeovers (matching Paper 1 findings)."
    pn2.font.size = Pt(8.5)
    pn2.font.color.rgb = TEXT_WHITE

    # Right Card: Human-in-the-Loop Triage Workflow
    add_card(slide, Inches(6.8), Inches(1.8), Inches(5.733), Inches(5.0), SURFACE_CARD, BORDER_COLOR)
    tb_triage = slide.shapes.add_textbox(Inches(7.0), Inches(1.9), Inches(5.333), Inches(4.7))
    tf_triage = tb_triage.text_frame
    tf_triage.word_wrap = True

    pt1 = tf_triage.paragraphs[0]
    pt1.text = "HUMAN-IN-THE-LOOP ALERT TRIAGE LIFECYCLE"
    pt1.font.bold = True
    pt1.font.size = Pt(11)
    pt1.font.color.rgb = EMERALD_ACCENT

    triage_stages = [
        ("1. Dynamic Alert Emission",
         "When P(Fraud) ≥ 0.70 or anomaly detector fires on medium risk, the system generates a structured alert ticket with severity 'HIGH' or 'CRITICAL'."),
        ("2. Real-Time WebSocket Delivery",
         "Alert is pushed instantly to the React 19 triage dashboard, displaying risk probability, anomaly score, and transaction details without page refreshes."),
        ("3. Local SHAP Attribution Waterfall",
         "Investigators open the Transaction Inspector to examine additive local feature pushes (e.g. +0.42 risk from V14 spike, -0.10 dampening from normal Amount)."),
        ("4. Analyst State Transitions",
         "• PENDING: New alert awaiting analyst claim.\n• ACKNOWLEDGED: Analyst actively reviewing audit trail.\n• RESOLVED (Confirmed Fraud): Confirmed malicious activity; card frozen.\n• RESOLVED (False Alarm): Legitimate purchase; feedback logged for retraining."),
        ("5. Continuous Feedback Audit Loop",
         "Analyst review notes and confirmed fraud flags are permanently stored in SQLite, establishing ground truth labels for future model retraining cycles."),
    ]

    for st_title, st_body in triage_stages:
        p_st = tf_triage.add_paragraph()
        p_st.text = st_title
        p_st.font.bold = True
        p_st.font.size = Pt(9.5)
        p_st.font.color.rgb = AMBER_ACCENT
        p_st.space_before = Pt(5)

        p_sb = tf_triage.add_paragraph()
        p_sb.text = st_body
        p_sb.font.size = Pt(8.5)
        p_sb.font.color.rgb = TEXT_WHITE


def build_slide_13_conclusion(prs):
    """Slide 13: Conclusion and Future Scope."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "11.0 CONCLUSION & FUTURE SCOPE", "Summary of Deliverables & Planned Future Research",
               "Consolidating project contributions and establishing future directions for production scaling.", 13)

    # Left Card: Summary of Project Achievements
    add_card(slide, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.0), SURFACE_CARD, BORDER_COLOR)
    tb_l = slide.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(5.3), Inches(4.7))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True

    pl1 = tf_l.paragraphs[0]
    pl1.text = "CORE PROJECT CONTRIBUTIONS"
    pl1.font.bold = True
    pl1.font.size = Pt(12)
    pl1.font.color.rgb = CYAN_ACCENT

    achievements = [
        ("Champion ML Accuracy (PR-AUC 0.8212)",
         "Proved Random Forest superiority over XGBoost and Gradient Boosting on severely imbalanced test data (82.65% fraud catch rate with only 0.058% false alarms)."),
        ("Strict Leakage-Free Preprocessing",
         "Eliminated data contamination by strictly fitting StandardScaler and SMOTE within training folds prior to validation/test scoring."),
        ("Dual-Engine Zero-Day Anomaly Detection",
         "Successfully integrated an unsupervised Isolation Forest model operating orthogonally to catch novel spending anomalies."),
        ("Sub-10ms Inference with SHAP XAI",
         "Delivered real-time sub-millisecond model scoring with dynamic local feature attribution waterfalls for regulatory compliance."),
        ("Production Full-Stack Platform",
         "Developed an enterprise-ready architecture connecting a FastAPI backend, SQLite audit store, and React 19 / Vite triage dashboard."),
    ]
    for a_t, a_b in achievements:
        p = tf_l.add_paragraph()
        p.text = a_t
        p.font.bold = True
        p.font.size = Pt(10)
        p.font.color.rgb = EMERALD_ACCENT
        p.space_before = Pt(6)

        pb = tf_l.add_paragraph()
        pb.text = a_b
        pb.font.size = Pt(8.8)
        pb.font.color.rgb = TEXT_WHITE

    # Right Card: Future Scope & Roadmap
    add_card(slide, Inches(6.8), Inches(1.8), Inches(5.733), Inches(5.0), SURFACE_CARD, BORDER_COLOR)
    tb_r = slide.shapes.add_textbox(Inches(7.0), Inches(1.95), Inches(5.333), Inches(4.7))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    pr1 = tf_r.paragraphs[0]
    pr1.text = "PLANNED FUTURE SCOPE & ROADMAP"
    pr1.font.bold = True
    pr1.font.size = Pt(12)
    pr1.font.color.rgb = AMBER_ACCENT

    future_items = [
        ("1. Automated Concept Drift Monitoring",
         "Incorporate Population Stability Index (PSI) and Kolmogorov-Smirnov tracking to trigger automated model retraining when transaction distributions drift."),
        ("2. Hardware Security Module (HSM) Integration",
         "Bridge the FastAPI service with ISO 8583 / ISO 20022 banking message specifications and HSM cryptographic PIN block decryption."),
        ("3. Distributed Streaming Architecture",
         "Deploy Apache Kafka message brokers and Redis caching clusters to scale transaction throughput beyond 100,000 transactions/second."),
        ("4. Graph Neural Networks (GNNs)",
         "Construct bipartite cardholder-merchant transaction graphs to detect coordinated syndicates and distributed mule account networks."),
        ("5. Continuous Active Learning",
         "Automate the feedback loop from resolved investigator alerts directly into weekly retraining pipelines with active learning sample selection."),
    ]
    for f_t, f_b in future_items:
        p = tf_r.add_paragraph()
        p.text = f_t
        p.font.bold = True
        p.font.size = Pt(10)
        p.font.color.rgb = TEAL_ACCENT
        p.space_before = Pt(6)

        pb = tf_r.add_paragraph()
        pb.text = f_b
        pb.font.size = Pt(8.8)
        pb.font.color.rgb = TEXT_WHITE


def build_slide_14_references(prs):
    """Slide 14: Academic References in strict IEEE format."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_solid_background(slide)
    add_header(slide, "12.0 REFERENCES", "Academic Literature & Dataset Citations",
               "Peer-reviewed journal publications and canonical benchmark citations in strict IEEE format.", 14)

    references = [
        ("[1]",
         "B. Borketey, \"Real-Time Fraud Detection Using Machine Learning,\" Journal of Data Analysis and Information Processing, vol. 12, no. 2, pp. 189–209, May 2024. DOI: 10.4236/jdaip.2024.122011."),
        ("[2]",
         "G. Charizanos, H. Demirhan, and D. Icen, \"An online fuzzy fraud detection framework for credit card transactions,\" Expert Systems with Applications, vol. 252, Part A, art. 124127, Oct. 2024. DOI: 10.1016/j.eswa.2024.124127."),
        ("[3]",
         "M. A. Talukder, M. Khalid, and M. A. Uddin, \"An integrated multistage ensemble machine learning model for fraudulent transaction detection,\" Journal of Big Data, vol. 11, art. 168, Oct. 2024. DOI: 10.1186/s40537-024-00996-5."),
        ("[4]",
         "A. Dal Pozzolo, O. Caelen, R. A. Johnson, and G. Bontempi, \"Calibrating Probability with Undersampling for Unbalanced Classification,\" in Proc. IEEE Symposium Series on Computational Intelligence (SSCI), Cape Town, South Africa, 2015, pp. 159–166. DOI: 10.1109/SSCI.2015.33."),
        ("[5]",
         "S. M. Lundberg and S.-I. Lee, \"A Unified Approach to Interpreting Model Predictions,\" in Advances in Neural Information Processing Systems (NeurIPS 30), Long Beach, CA, USA, 2017, pp. 4765–4774."),
        ("[6]",
         "F. T. Liu, K. M. Ting, and Z.-H. Zhou, \"Isolation Forest,\" in Proc. 8th IEEE International Conference on Data Mining (ICDM), Pisa, Italy, 2008, pp. 413–422. DOI: 10.1109/ICDM.2008.17."),
    ]

    add_card(slide, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.0), SURFACE_CARD, BORDER_COLOR)
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(11.333), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    for idx, (label, citation) in enumerate(references):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = f"{label}  {citation}"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_WHITE
        if idx > 0:
            p.space_before = Pt(10)


def generate_presentation() -> Path:
    """Generate the complete 14-slide master PowerPoint file."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    print("Building Slide 1: Title Slide...")
    build_slide_1_title(prs)

    print("Building Slide 2: Introduction...")
    build_slide_2_intro(prs)

    print("Building Slide 3: Problem Statement...")
    build_slide_3_problem_statement(prs)

    print("Building Slide 4: Project Objectives...")
    build_slide_4_objectives(prs)

    print("Building Slide 5: Literature Survey - Paper 1 (Borketey, 2024)...")
    build_slide_5_lit_paper1(prs)

    print("Building Slide 6: Literature Survey - Papers 2 & 3...")
    build_slide_6_lit_papers2_3(prs)

    print("Building Slide 7: Research Gap...")
    build_slide_7_research_gap(prs)

    print("Building Slide 8: Proposed Methodology...")
    build_slide_8_methodology(prs)

    print("Building Slide 9: Proposed Work Flowchart...")
    build_slide_9_flowchart(prs)

    print("Building Slide 10: System Architecture...")
    build_slide_10_architecture(prs)

    print("Building Slide 11: Experimental Results & Benchmark Discussion...")
    build_slide_11_results(prs)

    print("Building Slide 12: Explainability & Alert Triage Workflow...")
    build_slide_12_explainability(prs)

    print("Building Slide 13: Conclusion and Future Scope...")
    build_slide_13_conclusion(prs)

    print("Building Slide 14: References...")
    build_slide_14_references(prs)

    OUTPUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_PPTX))
    print(f"Presentation saved successfully to: {OUTPUT_PPTX}")
    return OUTPUT_PPTX


if __name__ == "__main__":
    pptx_path = generate_presentation()
