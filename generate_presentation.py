import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Clean Professional Light/White Theme Colors
    BG_WHITE = RGBColor(255, 255, 255)       # Pure White background
    CARD_BG = RGBColor(248, 250, 252)        # Very light clean gray (#f8fafc)
    CARD_BORDER = RGBColor(226, 232, 240)    # Soft slate border (#e2e8f0)
    PRIMARY_BLUE = RGBColor(30, 58, 138)     # Deep Navy / Academic Blue (#1e3a8a)
    ACCENT_CYAN = RGBColor(2, 132, 199)      # Bright Professional Blue/Cyan (#0284c7)
    TEXT_MAIN = RGBColor(15, 23, 42)         # Near Black for high readability (#0f172a)
    TEXT_MUTED = RGBColor(71, 85, 105)       # Charcoal / Muted gray (#475569)
    GREEN = RGBColor(22, 163, 74)            # Emerald Success (#16a34a)
    RED = RGBColor(220, 38, 38)              # Crimson Alert (#dc2626)

    blank_layout = prs.slide_layouts[6]
    assets_dir = r"E:\DS-CP\AdvGuard\report_assets"

    def set_slide_background(slide, color=BG_WHITE):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category="ADVGUARD · FODS COURSE PROJECT"):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p0 = tf.paragraphs[0]
        p0.text = category.upper()
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = ACCENT_CYAN
        
        p1 = tf.add_paragraph()
        p1.text = title_text
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = PRIMARY_BLUE

    # ==========================================
    # SLIDE 1: TITLE SLIDE (WHITE THEME)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    tb1 = s1.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(11.7), Inches(2.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "🛡️ ADVGUARD"
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    p = tf1.add_paragraph()
    p.text = "Geometric Adversarial Evasion Defense for Financial ML using C++ Spatial KD-Trees & LSH"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = TEXT_MAIN

    p = tf1.add_paragraph()
    p.text = "Fundamentals of Data Structures (FODS) Course Project | Academic Year 2025–2026"
    p.font.size = Pt(14)
    p.font.color.rgb = TEXT_MUTED

    # Member Grid Card
    card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.6), Inches(11.7), Inches(3.2))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = ACCENT_CYAN
    card.line.width = Pt(1.5)

    tb_team = s1.shapes.add_textbox(Inches(1.1), Inches(3.8), Inches(11.1), Inches(2.8))
    tf_team = tb_team.text_frame
    tf_team.word_wrap = True

    p = tf_team.paragraphs[0]
    p.text = "PROJECT TEAM (GROUP 09 · CSE-AIML-D):"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    team_members = [
        ("Medhansh Desai", "Roll No: 08", "PRN: 1251030262", "Spatial KD-Tree & Max-Heap Algorithms"),
        ("Harsh Parande", "Roll No: 48", "PRN: 1251030373", "Locality-Sensitive Hashing & LRU Cache"),
        ("Parth Jadhav", "Roll No: 54", "PRN: 125030285", "Adversarial Attacks (FGSM/JSMA) & ML Classifier"),
        ("Swapnil Pawar", "Roll No: 67", "PRN: 1251030103", "FastAPI Orchestration & UI Dashboard/Alerts")
    ]

    for name, rno, prn, role in team_members:
        p = tf_team.add_paragraph()
        p.text = f"• {name} ({rno} | {prn}) — Focus: {role}"
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_MAIN

    p_guide = tf_team.add_paragraph()
    p_guide.text = "\nProject Guide: Prof. Jyoti Kanjalkar"
    p_guide.font.size = Pt(13)
    p_guide.font.bold = True
    p_guide.font.color.rgb = GREEN

    # ==========================================
    # SLIDE 2: INTRODUCTION & PROBLEM STATEMENT
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Introduction & Problem Statement")

    tb2 = s2.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(6.0), Inches(5.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    intro_points = [
        ("The AI Vulnerability in Banking:", "Modern banks rely heavily on Machine Learning (Random Forests, Gradient Boosting) for automated fraud detection. However, ML models evaluate transactions in isolated feature space without spatial memory."),
        ("Adversarial Evasion Attacks:", "Attackers can introduce minute, imperceptible perturbations (epsilon ε) to transaction attributes. This gently pushes a fraudulent transaction across the ML decision boundary into the 'Safe' zone."),
        ("Catastrophic Financial Loss:", "When an evasion attack succeeds, fraudulent transfers bypass automated controls completely, resulting in millions of dollars in unflagged zero-day financial theft."),
        ("The Core Dilemma:", "How can a financial institution detect adversarial evasion in real time (sub-millisecond) without retraining massive neural networks?")
    ]

    for title, desc in intro_points:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"• {title} "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = PRIMARY_BLUE
        
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = TEXT_MAIN

    img_path = os.path.join(assets_dir, "fig3_decision_boundary_kd_override.png")
    if os.path.exists(img_path):
        s2.shapes.add_picture(img_path, Inches(7.0), Inches(1.8), width=Inches(5.5))

    # ==========================================
    # SLIDE 3: NEED & MOTIVATION
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Need & Motivation")

    col_data = [
        ("1. ML Models are Blind to Context", "A mathematical classifier calculates f(x) locally. It cannot discern whether an input vector is physically surrounded by historical fraudulent behavior in multidimensional space.", RED),
        ("2. Real-Time Latency Imperative", "Payment gateways (Visa, SWIFT, UPI) mandate sub-10ms decision times. Heavy deep learning defenses cause prohibitive latency spikes and dropped transactions.", ACCENT_CYAN),
        ("3. The Power of Classical DSA", "Spatial Data Structures (KD-Trees) offer deterministic, un-gameable geometric proofs. Even if an attacker fools the decision hyperplane, spatial proximity cannot be spoofed.", GREEN)
    ]

    for i, (title, desc, color) in enumerate(col_data):
        x = Inches(0.8 + i * 4.0)
        card = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.8), Inches(3.7), Inches(4.9))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = color
        card.line.width = Pt(1.5)

        tb = s3.shapes.add_textbox(x + Inches(0.2), Inches(2.0), Inches(3.3), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = color

        p2 = tf.add_paragraph()
        p2.text = f"\n{desc}"
        p2.font.size = Pt(13)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 4: OBJECTIVES & SCOPE
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Project Objectives & Scope")

    tb4_l = s4.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.3))
    tf4_l = tb4_l.text_frame
    tf4_l.word_wrap = True

    p = tf4_l.paragraphs[0]
    p.text = "🎯 PRIMARY OBJECTIVES"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    objs = [
        ("High-Dimensional Spatial Safety Net:", "Implement a custom C++ KD-Tree across 29 continuous features to perform O(log N) nearest neighbor search."),
        ("Geometric Discrepancy Engine:", "Detect adversarial bypass by analyzing the Fraud Neighbor Ratio (threshold ≥ 60%) among the k=10 spatial neighbors."),
        ("Multi-Tier Hybrid Architecture:", "Integrate Locality-Sensitive Hashing (LSH) for O(1) attack template filtering and an LRU Cache for microsecond replay protection."),
        ("Full-Stack Attack & Defense Studio:", "Demonstrate live evasion using FGSM, JSMA, and Boundary attacks with real-time multi-channel alerts (SMS, ntfy, Discord).")
    ]
    for o_title, o_desc in objs:
        p = tf4_l.add_paragraph()
        p.text = f"• {o_title} "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = PRIMARY_BLUE
        run = p.add_run()
        run.text = o_desc
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    tb4_r = s4.shapes.add_textbox(Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.3))
    tf4_r = tb4_r.text_frame
    tf4_r.word_wrap = True

    p = tf4_r.paragraphs[0]
    p.text = "🔍 SCOPE & CONSTRAINTS"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = GREEN

    scopes = [
        ("Academic Pure C++ Engine:", "All spatial structures (KD-Tree, Max-Heap, LSH, BST, LRU Cache) are written from scratch in standard C++17 with zero third-party ML/spatial libraries."),
        ("Financial Vector Space:", "Tested on real-world European credit card transaction dataset compressed via PCA into 29 continuous numerical dimensions."),
        ("Enterprise Defense Scope:", "Designed as an inline sidecar proxy intercepting transaction requests before financial settlement.")
    ]
    for s_title, s_desc in scopes:
        p = tf4_r.add_paragraph()
        p.text = f"• {s_title} "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = GREEN
        run = p.add_run()
        run.text = s_desc
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 5: LITERATURE SURVEY
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Literature Survey & Existing Approaches")

    survey_data = [
        ("Adversarial Machine Learning", "Goodfellow et al. (2014) introduced FGSM showing that linear behavior in high dimensions makes neural networks vulnerable to tiny input gradients. Papernot et al. (2016) extended this to sparse perturbations (JSMA)."),
        ("Adversarial Retraining (Limitations)", "Madry et al. (2018) proposed robust optimization by injecting adversarial examples during training. While effective, it degrades clean accuracy, demands massive compute, and fails against unseen attack geometries."),
        ("Spatial Nearest Neighbors in Security", "Bentley (1975) formalized the KD-Tree for O(log N) associative search. Indyk & Motwani (1998) introduced LSH for sublinear high-dimensional similarity search. AdvGuard uniquely unites these DSA primitives to guard ML fraud models.")
    ]

    for i, (title, desc) in enumerate(survey_data):
        y = Inches(1.7 + i * 1.8)
        card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(11.7), Inches(1.5))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1.5)

        tb = s5.shapes.add_textbox(Inches(1.0), y + Inches(0.15), Inches(11.3), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = f"📖 {title}"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_BLUE

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 6: FUNCTIONS & OPERATIONS (BLOCK DIAGRAM)
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Functions & Operations (Block Diagram)")

    tb6 = s6.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.4))
    tf6 = tb6.text_frame
    tf6.word_wrap = True

    ops = [
        ("Step 1: Ingestion & Feature Hashing", "The transaction vector X is received. The LRU Cache checks for instant repeat verdicts in O(1)."),
        ("Step 2: ML Baseline Inference", "The Random Forest classifies X. If an evasion attack occurred, ML outputs 'Safe' (fooled)."),
        ("Step 3: LSH Fast-Path Filter", "X is hashed via random Gaussian projections to check against known attack signatures in O(1)."),
        ("Step 4: Spatial KD-Tree Search", "X traverses the 29D KD-Tree to retrieve the k=10 nearest neighbors in O(log N)."),
        ("Step 5: Discrepancy Resolution", "If ML = Safe but KD-Tree Fraud Ratio ≥ 60%, status = BLOCKED (Adversarial Evasion Caught!)."),
        ("Step 6: Real-Time SOC Dispatch", "Multi-channel notifications trigger push alerts to phone, email, and Discord.")
    ]
    for o_name, o_detail in ops:
        p = tf6.add_paragraph() if tf6.paragraphs[0].text else tf6.paragraphs[0]
        p.text = f"▶ {o_name}: "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = PRIMARY_BLUE
        run = p.add_run()
        run.text = o_detail
        run.font.bold = False
        run.font.color.rgb = TEXT_MAIN

    img_path = os.path.join(assets_dir, "image3.png")
    if os.path.exists(img_path):
        s6.shapes.add_picture(img_path, Inches(6.8), Inches(1.6), width=Inches(5.7))

    # ==========================================
    # SLIDE 7: DATA STRUCTURES & ALGORITHMS USED
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Data Structures & Algorithms Used")

    ds_items = [
        ("🌲 K-Dimensional Tree (KD-Tree)", "Cycles dimensions: axis = depth mod 29. Recursively splits space. Uses hyperplane bounding pruning: if |x - split| > r_max, opposite subtree is pruned. Bounded to O(log N)."),
        ("⚡ Binary Max-Heap (k=10)", "Array-backed complete binary tree. Stores current closest 10 neighbors. Root holds the furthest neighbor (r_max) in O(1). Heapify updates take O(log k)."),
        ("🛡️ Locality-Sensitive Hashing (LSH)", "Hashes 29D continuous vectors into integer buckets using random Gaussian projections: h(x) = floor((a·x + b)/w). Detects similar attack vectors in O(1)."),
        ("💾 LRU Cache (Hash Map + DLL)", "Combines std::unordered_map with a Doubly Linked List for strict O(1) read/write caching of repeat adversarial payloads.")
    ]

    for i, (title, desc) in enumerate(ds_items):
        row = i // 2
        col = i % 2
        x = Inches(0.8 + col * 5.9)
        y = Inches(1.6 + row * 2.7)

        card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(5.6), Inches(2.4))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1.5)

        tb = s7.shapes.add_textbox(x + Inches(0.2), y + Inches(0.15), Inches(5.2), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_BLUE

        p2 = tf.add_paragraph()
        p2.text = f"\n{desc}"
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_MAIN

    # ==========================================
    # SLIDE 8: INPUT DATA SOURCES & PERTURBATION
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Input Data Sources & Adversarial Perturbation")

    tb8 = s8.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.4))
    tf8 = tb8.text_frame
    tf8.word_wrap = True

    data_points = [
        ("Credit Card Transaction Dataset:", "Real-world European financial transaction dataset containing 284,807 transactions. Anonymized into 28 continuous PCA components (V1–V28) + Time + Amount."),
        ("Severe Class Imbalance:", "Only 492 fraud cases (0.172%). Normalized and balanced historical partition (~1,200 transactions) used for KD-Tree indexing."),
        ("Adversarial Evasion Techniques:", "• FGSM: Steps along -sign(grad) to reduce fraud probability.\n• JSMA: Selectively alters only top 8 sensitive features.\n• Boundary: Binary line searches decision boundary."),
        ("Perturbation Analysis:", "Calculates L1 (Manhattan), L2 (Euclidean), and Linf (Chebyshev) metrics to quantify attack imperceptibility.")
    ]
    for d_title, d_desc in data_points:
        p = tf8.add_paragraph() if tf8.paragraphs[0].text else tf8.paragraphs[0]
        p.text = f"• {d_title} "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = PRIMARY_BLUE
        run = p.add_run()
        run.text = d_desc
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = TEXT_MAIN

    img_path = os.path.join(assets_dir, "fig2_attack_perturbation.png")
    if os.path.exists(img_path):
        s8.shapes.add_picture(img_path, Inches(6.8), Inches(1.6), width=Inches(5.7))

    # ==========================================
    # SLIDE 9: SYSTEM ARCHITECTURE & FLOW DIAGRAM
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "System Architecture & Flow Diagram")

    img_path = os.path.join(assets_dir, "image4.png")
    if os.path.exists(img_path):
        s9.shapes.add_picture(img_path, Inches(0.8), Inches(1.5), width=Inches(6.8))

    tb9 = s9.shapes.add_textbox(Inches(7.8), Inches(1.5), Inches(4.7), Inches(5.4))
    tf9 = tb9.text_frame
    tf9.word_wrap = True

    p = tf9.paragraphs[0]
    p.text = "🏛️ THREE-TIER PIPELINE"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    arch_points = [
        ("1. Presentation Tier (React 18 / Vite):", "Interactive attack simulator, DSA benchmark curves, and real-time SMS / Push notification hub."),
        ("2. Application Tier (FastAPI):", "Python orchestration layer executing ML models, adversarial attacks, and C++ subprocess wrappers."),
        ("3. C++ Spatial Defense Engine:", "Pure native C++ executable performing LSH hash checks, LRU caching, and KD-Tree spatial verification."),
        ("4. SOC Notification Bridge:", "Async threads broadcasting instant alerts to ntfy.sh (mobile push), SMTP email, and Discord webhooks.")
    ]
    for a_title, a_desc in arch_points:
        p = tf9.add_paragraph()
        p.text = f"• {a_title} "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = PRIMARY_BLUE
        run = p.add_run()
        run.text = a_desc
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 10: COMPLEXITY ANALYSIS OF DATA STRUCTURES
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Complexity of Data Structures & Performance Benchmark")

    img_path = os.path.join(assets_dir, "fig1_complexity_benchmark.png")
    if os.path.exists(img_path):
        s10.shapes.add_picture(img_path, Inches(0.8), Inches(1.5), width=Inches(6.2))

    tb10 = s10.shapes.add_textbox(Inches(7.2), Inches(1.5), Inches(5.3), Inches(5.4))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    p = tf10.paragraphs[0]
    p.text = "⚡ EMPIRICAL & ASYMPTOTIC COMPLEXITY"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE

    comp_data = [
        ("KD-Tree Spatial Search", "O(log N)", "O(N·d)", "Prunes 90%+ of subtrees; delivers 14.9x speedup at N=10k"),
        ("Max-Heap Neighbor Tracking", "O(log k)", "O(log k)", "Bounded heap of k=10; root access r_max in O(1)"),
        ("LSH Attack Signature Filter", "O(1)", "O(N)", "Random projection hash lookup; sub-millisecond pre-filter"),
        ("LRU Replay Defense Cache", "O(1)", "O(N)", "Doubly linked list + hash map for immediate replay intercepts"),
        ("BST Transaction ID Lookup", "O(log N)", "O(N)", "Fast alphanumeric index lookup without disk I/O")
    ]
    for name, avg_c, wst_c, note in comp_data:
        p = tf10.add_paragraph()
        p.text = f"• {name}: "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = PRIMARY_BLUE
        
        run = p.add_run()
        run.text = f"Avg: {avg_c} | Worst: {wst_c}\n  ↳ {note}"
        run.font.bold = False
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 11: CONCLUSION, SCREENSHOTS & FUTURE SCOPE
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "Conclusion, Dashboard Demo & Future Scope")

    tb11_l = s11.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.4))
    tf11_l = tb11_l.text_frame
    tf11_l.word_wrap = True

    p = tf11_l.paragraphs[0]
    p.text = "🏁 PROJECT CONCLUSIONS"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = GREEN

    concls = [
        ("ML Models Alone are Insufficient:", "Adversarial evasion attacks (FGSM/JSMA) routinely bypass Random Forest classifiers with slight, imperceptible feature perturbations."),
        ("Spatial Context Defeats Evasion:", "AdvGuard's C++ KD-Tree successfully caught 100% of adversarial attacks by exposing that the transactions remained inside historical fraud clusters."),
        ("Sub-Millisecond Overhead:", "The hybrid LSH + KD-Tree + LRU Cache pipeline evaluated transactions in under 100 microseconds, easily fitting standard banking SLAs.")
    ]
    for c_title, c_desc in concls:
        p = tf11_l.add_paragraph()
        p.text = f"• {c_title} "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_MAIN
        run = p.add_run()
        run.text = c_desc
        run.font.bold = False
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_MUTED

    p_f = tf11_l.add_paragraph()
    p_f.text = "\n🚀 FUTURE SCOPE & ENHANCEMENTS:"
    p_f.font.size = Pt(14)
    p_f.font.bold = True
    p_f.font.color.rgb = PRIMARY_BLUE

    futures = [
        ("Dynamic Tree Rebalancing:", "Implement scapegoat or AVL-style spatial balancing during live streaming ingestion."),
        ("Distributed KD-Tree Sharding:", "Scale to millions of transactions via distributed in-memory clusters."),
        ("Hardware Acceleration:", "Port distance metrics and LSH projections to SIMD AVX-512 / GPU CUDA kernels.")
    ]
    for f_title, f_desc in futures:
        p = tf11_l.add_paragraph()
        p.text = f"• {f_title} "
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_MAIN
        run = p.add_run()
        run.text = f_desc
        run.font.bold = False
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_MUTED

    img_path = os.path.join(assets_dir, "fig4_security_matrix.png")
    if os.path.exists(img_path):
        s11.shapes.add_picture(img_path, Inches(6.8), Inches(1.6), width=Inches(5.7))

    # Save presentation
    output_path = r"E:\DS-CP\AdvGuard\AdvGuard_FODS_CP_White_Theme.pptx"
    prs.save(output_path)
    # Also attempt to overwrite the original if not locked
    try:
        prs.save(r"E:\DS-CP\AdvGuard\AdvGuard_FODS_CP_Presentation.pptx")
    except Exception:
        pass
    print(f"Presentation successfully created with CLEAN WHITE THEME at: {output_path}")

if __name__ == "__main__":
    create_presentation()
