import streamlit as st
import math
import json
import re
import os

# ─── HANDBOOK LOADER ────────────────────────────────────────────────
@st.cache_data
def load_handbook():
    path = os.path.join(os.path.dirname(__file__), "handbook_chunks.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def search_handbook(query, chunks, top_k=10):
    """Keyword-based retrieval — score each chunk by query term overlap."""
    query_lower = query.lower()
    query_words = set(re.findall(r'\b\w{3,}\b', query_lower))
    stop = {"the","and","for","are","you","that","this","with","have","from",
            "they","will","what","when","how","can","our","your","was","not",
            "but","all","its","been","their","has","more","also","any","into"}
    query_words -= stop

    # Also add common synonyms/expansions
    expansions = {
        "5-step": ["step","five","flow","chart","sales","process"],
        "five step": ["step","five","flow","chart","sales","process"],
        "commission": ["pay","chart","gpm","gross","percent"],
        "pay": ["commission","chart","gpm","gross","percent","salary"],
        "insurance": ["claim","adjuster","storm","damage","hail"],
        "warranty": ["workmanship","material","gaf","year","coverage"],
        "sop": ["procedure","operating","standard","process"],
        "repair": ["labor","rate","fix","patch","leak"],
        "bid": ["quote","calculate","price","cost","estimate"],
    }
    for key, synonyms in expansions.items():
        if key in query_lower:
            query_words.update(synonyms)

    if not query_words:
        return chunks[:top_k]

    scored = []
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        # Count term frequency
        score = sum(text_lower.count(w) for w in query_words)
        # Boost heading matches (first 150 chars)
        heading = text_lower[:150]
        score += sum(heading.count(w) * 4 for w in query_words)
        # Boost chapter matches
        chapter_lower = chunk["chapter"].lower()
        score += sum(chapter_lower.count(w) * 3 for w in query_words)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:top_k]] or chunks[:top_k]

def ask_handbook(question, chunks):
    """Pure local search — no API, instant results."""
    return search_handbook(question, chunks, top_k=5)

# ═══════════════════════════════════════════════════════════════════════════════
# THUNDERBIRD HUB - NEW BRANDING & COLOR SCHEME
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Thunderbird Hub",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Barlow Condensed', sans-serif;
    }
    
    html, body, [class*="css"] { 
        background: #ecf0f3; 
        color: #1e3158;
    }
    
    .stApp {
        background-color: #ecf0f3;
    }
    
    /* Navy Header & Tabs */
    .hdr { 
        background: linear-gradient(135deg, #1e3158 0%, #0d1a2f 100%);
        border-bottom: 4px solid #b92227;
        padding: 24px 32px;
        margin: -80px -80px 24px -80px;
        display: flex;
        align-items: center;
        gap: 20px;
        flex-wrap: wrap;
    }
    
    .hdr h1 { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #fff;
        letter-spacing: 0.04em;
        margin: 0;
        text-transform: uppercase;
    }
    
    .hdr .acc { 
        color: #b92227;
    }
    
    .hdr .sub { 
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.85);
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-top: 8px;
    }
    
    .logo-img {
        width: 80px;
        height: 80px;
        object-fit: contain;
    }
    
    /* Labels */
    .lbl { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #b92227;
        margin-bottom: 5px;
    }
    
    /* Cards */
    .card { 
        background: #fff;
        border: 1px solid #e0e5eb;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(30, 49, 88, 0.08);
    }
    
    .cardb { 
        background: #fff;
        border: 2px solid #b92227;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(185, 34, 39, 0.1);
    }
    
    /* Tables */
    .ptbl { 
        width: 100%;
        border-collapse: collapse;
    }
    
    .ptbl th { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #1e3158;
        padding: 7px 10px;
        text-align: left;
        border-bottom: 1px solid #d0d5e0;
    }
    
    .ptbl td { 
        padding: 9px 10px;
        border-bottom: 1px solid #e8edf5;
        font-size: 0.9rem;
        color: #2c3e50;
    }
    
    .ptbl tr:last-child td { 
        border-bottom: none;
    }
    
    .ptbl tr:hover td { 
        background: #f5f8fc;
    }
    
    .ptbl .hlr td { 
        background: #f0f5e8;
        color: #2d5a1a;
        font-weight: 600;
    }
    
    .ptbl .finr td { 
        color: #1e4d7b;
    }
    
    .ptbl .big { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e3158;
    }
    
    .hlr .big { 
        color: #2d5a1a !important;
    }
    
    .finr .big { 
        color: #1e4d7b !important;
    }
    
    /* Metric Boxes */
    .mbox { 
        background: #fff;
        border: 1px solid #d0d5e0;
        border-radius: 8px;
        padding: 12px 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(30, 49, 88, 0.06);
    }
    
    .mval { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #b92227;
        line-height: 1;
    }
    
    .mlbl { 
        font-size: 0.62rem;
        color: #1e3158;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 3px;
    }
    
    /* Chips */
    .chip { 
        display: inline-block;
        background: #e8edf5;
        border: 1px solid #d0d5e0;
        border-radius: 20px;
        padding: 3px 11px;
        font-size: 0.8rem;
        color: #4a5f8f;
        margin: 3px 3px 3px 0;
    }
    
    .chip strong { 
        color: #1e3158;
    }
    
    /* Alert Boxes */
    .note { 
        background: #e8f0ff;
        border-left: 3px solid #1e4d7b;
        border-radius: 0 6px 6px 0;
        padding: 8px 12px;
        font-size: 0.8rem;
        color: #2c3e50;
        margin: 6px 0;
    }
    
    .warn { 
        background: #fff5f0;
        border-left: 3px solid #b92227;
        border-radius: 0 6px 6px 0;
        padding: 8px 12px;
        font-size: 0.8rem;
        color: #8b3a1f;
        margin: 6px 0;
    }
    
    .info { 
        background: #f0f9f0;
        border-left: 3px solid #2d5a1a;
        border-radius: 0 6px 6px 0;
        padding: 8px 12px;
        font-size: 0.8rem;
        color: #2d5a1a;
        margin: 6px 0;
    }
    
    /* Divider */
    .hr { 
        border: none;
        border-top: 1px solid #d0d5e0;
        margin: 14px 0;
    }
    
    /* Form Elements */
    .stSelectbox>div>div, 
    .stNumberInput>div>div>input, 
    .stTextInput>div>div>input {
        background: #fff !important;
        border: 1px solid #d0d5e0 !important;
        color: #2c3e50 !important;
        border-radius: 6px !important;
    }
    
    label { 
        color: #1e3158 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { 
        background: #1e3158;
        border-radius: 8px 8px 0 0;
        border-bottom: 0;
        gap: 0;
    }
    
    .stTabs [data-baseweb="tab"] { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: rgba(255, 255, 255, 0.7) !important;
        padding: 12px 20px;
    }
    
    .stTabs [aria-selected="true"] { 
        background: #b92227 !important;
        color: #fff !important;
        border-radius: 0;
    }
    
    .stTabs [data-baseweb="tab-panel"] { 
        background: transparent;
        padding: 16px 0 0;
    }
    
    /* Empty State */
    .empty { 
        text-align: center;
        padding: 44px 24px;
    }
    
    .empty .ei { 
        font-size: 2.2rem;
        margin-bottom: 8px;
    }
    
    .empty .et { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 0.95rem;
        color: #667799;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    
    /* Warranty Table */
    .wtbl { 
        width: 100%;
        border-collapse: collapse;
        margin-top: 6px;
    }
    
    .wtbl th { 
        background: #1e3158;
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #fff;
        padding: 8px 10px;
        text-align: left;
        border: 1px solid #d0d5e0;
    }
    
    .wtbl td { 
        padding: 8px 10px;
        font-size: 0.82rem;
        border: 1px solid #e8edf5;
        color: #2c3e50;
        background: #fff;
    }
    
    .wtbl tr:nth-child(even) td { 
        background: #f5f8fc;
    }
    
    /* Tier Colors */
    .tier-sig { 
        color: #b99f2a !important;
        font-weight: 700 !important;
    }
    
    .tier-gld { 
        color: #b92227 !important;
        font-weight: 700 !important;
    }
    
    .tier-sil { 
        color: #7a8fa3 !important;
        font-weight: 700 !important;
    }
    
    .tier-brz { 
        color: #8b5a3c !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e3158;
    }
    
    [data-testid="stSidebar"] * {
        color: #fff !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #b92227 !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 4px !important;
    }
    
    .stButton > button:hover {
        background-color: #9b1820 !important;
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .hdr {
            padding: 16px 16px;
            margin: -1rem -1rem 1.5rem -1rem;
        }
        
        .logo-img {
            width: 60px;
            height: 60px;
        }
        
        .hdr h1 {
            font-size: 1.4rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 10px 12px;
            font-size: 0.75rem;
        }
    }
    
    @media (max-width: 480px) {
        .hdr h1 {
            font-size: 1.1rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 8px 8px;
            font-size: 0.65rem;
        }
    }
    
    </style>
""", unsafe_allow_html=True)

# Custom Header with Logo
col_logo, col_header = st.columns([1, 3], gap="medium")
with col_logo:
    st.image("Copy_of_AccentRoofing-Logo.png", width=80)

with col_header:
    st.markdown("""
        <div style="padding-top: 8px;">
            <div style="font-family: 'Barlow Condensed', sans-serif; font-size: 42px; font-weight: 800; color: #1e3158; margin: 0; line-height: 1.1; letter-spacing: -0.5px;">
                THUNDERBIRD <span style="color: #b92227;">HUB</span>
            </div>
            <div style="color: #666; font-size: 13px; margin-top: 8px; letter-spacing: 0.5px;">
                Powered by Accent Roofing Service
            </div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# APP TABS & CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

from tab6_installed_jobs import render_tab6

# Define tabs
tab_large, tab_small, tab_repair, tab_cpo, tab_handbook, tab_jobs = st.tabs([
    "Full Roof (20+ SQ)",
    "Small Job (< 20 SQ)",
    "Repair Calculator",
    "CPO & Rate Guide",
    "Handbook Q&A",
    "Installed Jobs"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FULL ROOF CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_large:
    st.markdown('<div class="lbl">Shingle Product & Pitch</div>', unsafe_allow_html=True)

    col_prod, col_pitch = st.columns(2, gap="large")

    with col_prod:
        product = st.selectbox(
            "Product",
            ["GAF Timberline HDZ", "GAF Timberline UHDZ", "GAF Camelot II / Slateline", "CertainTeed Landmark", "CertainTeed Landmark Pro"],
            index=0,
            key="full_product"
        )

    with col_pitch:
        pitch_range = st.selectbox(
            "Pitch Range",
            ["4–7 (Low)", "8–10 (Moderate)", "11–13+ (Steep)"],
            index=0,
            key="full_pitch"
        )

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown('<div class="lbl">Roofing Squares</div>', unsafe_allow_html=True)
        sq_input = st.number_input("SQ", value=25, min_value=20, step=1, key="full_sq")

    with col2:
        st.markdown('<div class="lbl">Pitch Multiplier (Waste)</div>', unsafe_allow_html=True)
        pitch_mult = {"4–7 (Low)": 1.1, "8–10 (Moderate)": 1.15, "11–13+ (Steep)": 1.2}[pitch_range]
        st.metric("Waste Factor", f"{pitch_mult}x")

    with col3:
        st.markdown('<div class="lbl">Adjusted SQ (with waste)</div>', unsafe_allow_html=True)
        adj_sq = sq_input * pitch_mult
        st.metric("Adj. SQ", f"{adj_sq:.1f}")

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    st.markdown('<div class="lbl">Low Slope Add-On (1/12–3/12)</div>', unsafe_allow_html=True)
    col_ls1, col_ls2 = st.columns(2)
    with col_ls1:
        has_low_slope = st.checkbox("Add Low Slope Section", value=False, key="full_low_slope")
    with col_ls2:
        if has_low_slope:
            low_slope_sq = st.number_input("Low Slope SQ", value=5, min_value=1, step=1, key="full_ls_sq")
        else:
            low_slope_sq = 0

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    st.markdown('<div class="lbl">Deck Over</div>', unsafe_allow_html=True)
    col_deck1, col_deck2 = st.columns(2)
    with col_deck1:
        deck_over = st.checkbox("Deck Over Job", value=False, key="full_deck")
    with col_deck2:
        if deck_over:
            deck_sq = st.number_input("Deck Over SQ", value=5, min_value=1, step=1, key="full_deck_sq")
        else:
            deck_sq = 0

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    st.markdown('<div class="lbl">Gross Profit Margin (GPM) — Select Tier or Custom</div>', unsafe_allow_html=True)
    gpm_tier = st.select_slider(
        "GPM Tier",
        options=[
            "39% (Base)",
            "37% (Tier 2)",
            "35% (Financing)",
            "35% (Tier 4)",
            "32% (Tier 5)",
            "26% (Tier 6)",
            "18% (Lowest Fin)",
            "18% (Tier 8)",
            "Custom"
        ],
        value="39% (Base)",
        key="full_gpm_tier"
    )

    gpm_values = {
        "39% (Base)": 0.39,
        "37% (Tier 2)": 0.37,
        "35% (Financing)": 0.35,
        "35% (Tier 4)": 0.35,
        "32% (Tier 5)": 0.32,
        "26% (Tier 6)": 0.26,
        "18% (Lowest Fin)": 0.18,
        "18% (Tier 8)": 0.18,
    }

    if gpm_tier == "Custom":
        gpm_slider = st.slider("GPM Slider", 0, 100, 39, key="full_gpm_custom") / 100
    else:
        gpm_slider = gpm_values[gpm_tier]

    st.markdown(f'<div class="mbox"><div class="mval">{gpm_slider*100:.0f}%</div><div class="mlbl">GPM</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    st.markdown('<div class="lbl">Pricing</div>', unsafe_allow_html=True)

    base_cost = adj_sq * 410
    low_slope_cost = low_slope_sq * 375
    deck_cost = deck_sq * 350
    total_cost = base_cost + low_slope_cost + deck_cost

    profit = total_cost * gpm_slider
    retail = total_cost + profit

    col_m1, col_m2, col_m3 = st.columns(3, gap="large")
    with col_m1:
        st.markdown(f'<div class="mbox"><div class="mval">${total_cost:,.0f}</div><div class="mlbl">Cost</div></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="mbox"><div class="mval">${profit:,.0f}</div><div class="mlbl">Profit ({gpm_slider*100:.0f}%)</div></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown(f'<div class="mbox"><div class="mval">${retail:,.0f}</div><div class="mlbl">Retail Price</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbl">Financing Options (monthly est.)</div>', unsafe_allow_html=True)

    finance_options = [
        ("Cash", retail),
        ("12 Month (0%)", retail / 12),
        ("24 Month (4.99%)", (retail * 1.0499) / 24),
        ("36 Month (6.99%)", (retail * 1.0699) / 36),
        ("60 Month (8.99%)", (retail * 1.0899) / 60),
    ]

    finance_cols = st.columns(5)
    for i, (label, amt) in enumerate(finance_options):
        with finance_cols[i]:
            st.markdown(f'<div class="mbox"><div style="font-size:.75rem;color:#666;margin-bottom:4px;">{label}</div><div class="mval">${amt:,.0f}</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SMALL JOB CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_small:
    st.markdown('<div class="lbl">Small Job Pricing (1–19 SQ)</div>', unsafe_allow_html=True)

    sq_small = st.number_input("Roofing Squares", value=5, min_value=1, max_value=19, step=1, key="small_sq")

    if sq_small > 19:
        st.markdown('<div class="warn">⚠ Over 19 SQ — use Full Roof tab</div>', unsafe_allow_html=True)
        sq_small = 19

    small_job_rates = {
        1: 500,
        2: 800,
        3: 1050,
        4: 1400,
        5: 1750,
        6: 2100,
        7: 2450,
        8: 2800,
        9: 3150,
        10: 3500,
        11: 3850,
        12: 4200,
        13: 4550,
        14: 4900,
        15: 5250,
        16: 5600,
        17: 5950,
        18: 6300,
        19: 6650,
    }

    cost = small_job_rates.get(int(sq_small), 0)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbl">GPM Tier</div>', unsafe_allow_html=True)

    gpm_tier_small = st.select_slider(
        "GPM",
        options=["39%", "37%", "35% (Fin)", "35%", "32%", "26%", "18% (Fin)", "18%", "Custom"],
        value="39%",
        key="small_gpm"
    )

    gpm_vals = {"39%": 0.39, "37%": 0.37, "35% (Fin)": 0.35, "35%": 0.35, "32%": 0.32, "26%": 0.26, "18% (Fin)": 0.18, "18%": 0.18}

    if gpm_tier_small == "Custom":
        gpm_small = st.slider("GPM", 0, 100, 39, key="small_gpm_custom") / 100
    else:
        gpm_small = gpm_vals[gpm_tier_small]

    profit_small = cost * gpm_small
    retail_small = cost + profit_small

    col_s1, col_s2, col_s3 = st.columns(3, gap="large")
    with col_s1:
        st.markdown(f'<div class="mbox"><div class="mval">${cost:,.0f}</div><div class="mlbl">Cost</div></div>', unsafe_allow_html=True)
    with col_s2:
        st.markdown(f'<div class="mbox"><div class="mval">${profit_small:,.0f}</div><div class="mlbl">Profit</div></div>', unsafe_allow_html=True)
    with col_s3:
        st.markdown(f'<div class="mbox"><div class="mval">${retail_small:,.0f}</div><div class="mlbl">Retail</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REPAIR CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_repair:
    st.markdown('<div class="lbl">Repair Bidding</div>', unsafe_allow_html=True)

    repair_materials = {
        "Shingles (bundle)": 45,
        "Flashing Kit": 85,
        "Underlayment (roll)": 120,
        "Vents & Boots": 65,
        "Gutters (linear ft)": 8,
        "Tar & Sealants": 35,
        "Nails & Hardware": 25,
        "Ice Dam Treatment": 150,
        "Chimney Cricket": 200,
        "Valley Repair Kit": 95,
        "Soffit & Fascia (linear ft)": 12,
        "Drip Edge (linear ft)": 4,
        "Vent Flashing": 55,
        "Pipe Flashing": 45,
        "Ridge Vent (linear ft)": 10,
        "Starter Strip (linear ft)": 6,
        "Netting & Screens": 75,
        "Caulk (cartridge)": 8,
        "Sealant (bucket)": 50,
        "Walkway Pads (set)": 120,
        "Safety Equipment": 200,
        "Inspection & Report": 100,
        "Warranty Document": 50,
        "Permits & Misc": 150,
    }

    mat_col, qty_col = st.columns(2)
    with mat_col:
        material = st.selectbox("Material", list(repair_materials.keys()), key="repair_material")
    with qty_col:
        quantity = st.number_input("Quantity", value=1, min_value=1, step=1, key="repair_qty")

    material_cost = repair_materials[material] * quantity

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbl">Labor Tier</div>', unsafe_allow_html=True)

    labor_tiers = {
        "Basic (Patches, sealing)": 50,
        "Intermediate (Shingle replacement, flashing)": 85,
        "Advanced (Restoration, complex repairs)": 120,
        "Premium (Full structural work)": 150,
    }

    labor_tier = st.selectbox("Labor Type", list(labor_tiers.keys()), key="repair_labor")
    labor_rate = labor_tiers[labor_tier]
    labor_hours = st.number_input("Labor Hours", value=2, min_value=0.5, step=0.5, key="repair_hours")

    labor_cost = labor_rate * labor_hours

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbl">Profit Margin</div>', unsafe_default=True)

    gpm_repair = st.slider("GPM", 40, 60, 50, key="repair_gpm") / 100

    total_cost_repair = material_cost + labor_cost
    profit_repair = total_cost_repair * gpm_repair
    retail_repair = total_cost_repair + profit_repair

    col_r1, col_r2, col_r3 = st.columns(3, gap="large")
    with col_r1:
        st.markdown(f'<div class="mbox"><div class="mval">${total_cost_repair:,.0f}</div><div class="mlbl">Cost</div></div>', unsafe_allow_html=True)
    with col_r2:
        st.markdown(f'<div class="mbox"><div class="mval">${profit_repair:,.0f}</div><div class="mlbl">Profit</div></div>', unsafe_allow_html=True)
    with col_r3:
        st.markdown(f'<div class="mbox"><div class="mval">${retail_repair:,.0f}</div><div class="mlbl">Retail</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CPO & RATE GUIDE
# ══════════════════════════════════════════════════════════════════════════════
with tab_cpo:
    st.markdown('<div class="lbl">Warranty Comparison</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
      <table class="ptbl">
        <thead><tr><th>Warranty</th><th>Material</th><th>Workmanship</th><th>Wind</th><th>Hail</th></tr></thead>
        <tbody>
          <tr><td><strong>Signature (GAF)</strong></td><td>Lifetime</td><td>10 yrs</td><td>Unlimited mph</td><td>Yes</td></tr>
          <tr><td><strong>Gold (CertainTeed)</strong></td><td>40 years</td><td>15 yrs</td><td>110+ mph</td><td>Yes</td></tr>
          <tr><td><strong>Silver (GAF Standard)</strong></td><td>25 years</td><td>10 yrs</td><td>90 mph</td><td>Limited</td></tr>
          <tr><td><strong>Bronze (Contractor)</strong></td><td>15 years</td><td>5 yrs</td><td>70 mph</td><td>Limited</td></tr>
        </tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbl">Per-SQ Rates by Product & Tier</div>', unsafe_allow_html=True)

    RATES = {
        "GAF Timberline HDZ": {
            "Signature": (360, 380, 410),
            "Gold": (340, 360, 390),
            "Silver": (320, 340, 370),
            "Bronze": (290, 310, 340),
        },
        "GAF Timberline UHDZ": {
            "Signature": (410, 430, 460),
            "Gold": (390, 410, 440),
            "Silver": (370, 390, 420),
            "Bronze": (340, 360, 390),
        },
        "CertainTeed Landmark": {
            "Gold": (380, 400, 430),
            "Silver": (350, 370, 400),
            "Bronze": (320, 340, 370),
        },
    }

    rate_rows = ""
    for prod, tiers in RATES.items():
        for tier, (r1, r2, r3) in tiers.items():
            rate_rows += f"<tr><td>{prod}</td><td>{tier}</td><td>${r1}</td><td>${r2}</td><td>${r3}</td></tr>"
    st.markdown(f"""
    <div class="card">
      <table class="wtbl">
        <thead><tr><th>Product</th><th>Tier</th><th>Pitch 4-7</th><th>Pitch 8-10</th><th>Pitch 11+</th></tr></thead>
        <tbody>{rate_rows}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbl">Low Slope Cost Rates</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
      <table class="wtbl">
        <thead><tr><th>Pitch</th><th>Rate per Adj. SQ</th></tr></thead>
        <tbody>
          <tr><td>1/12</td><td>$375/SQ</td></tr>
          <tr><td>2/12</td><td>$370/SQ</td></tr>
          <tr><td>3/12</td><td>$350/SQ</td></tr>
        </tbody>
      </table>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — HANDBOOK Q&A
# ══════════════════════════════════════════════════════════════════════════════
with tab_handbook:
    handbook_chunks = load_handbook()

    if "hb_results" not in st.session_state:
        st.session_state.hb_results = []
    if "hb_pending_q" not in st.session_state:
        st.session_state.hb_pending_q = ""

    st.markdown('<div class="lbl">Thunderbird Handbook — Instant Search</div>', unsafe_allow_html=True)
    st.markdown('<div class="note">Search the handbook instantly — shows the exact relevant sections with page number and chapter. Free, instant, no limits.</div>', unsafe_allow_html=True)

    if not handbook_chunks:
        st.markdown('<div class="warn">Handbook data not found. Make sure <strong>handbook_chunks.json</strong> is in your GitHub repo.</div>', unsafe_allow_html=True)
    else:
        hb_col, ref_col = st.columns([1.3, 1], gap="large")

        with hb_col:
            st.markdown('<div class="lbl">Suggested Topics — click to search instantly</div>', unsafe_allow_html=True)
            suggestions = [
                "T-Bird monthly sales expectations",
                "Pay commission structure GPM",
                "5-step sales process flow chart",
                "Insurance claim appointment steps",
                "Warranty differences tiers",
                "No-show SOP procedure",
                "Full replacement bid calculation",
                "Repair labor rates",
            ]
            s_cols = st.columns(2)
            for i, s in enumerate(suggestions):
                if s_cols[i % 2].button(s, key=f"sugg_{i}", use_container_width=True):
                    st.session_state.hb_pending_q = s

            if st.session_state.hb_pending_q:
                auto_q = st.session_state.hb_pending_q
                st.session_state.hb_pending_q = ""
                results = search_handbook(auto_q, handbook_chunks, top_k=5)
                st.session_state.hb_results = [{"q": auto_q, "pages": results}] + st.session_state.hb_results

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown('<div class="lbl">Search the Handbook</div>', unsafe_allow_html=True)
            question = st.text_area("Search", placeholder="e.g. minimum GPM for self-generated lead",
                                    label_visibility="collapsed", height=80, key="hb_question_input")
            ask_col, clear_col = st.columns([3, 1])
            ask_btn   = ask_col.button("🔍  Search Handbook", use_container_width=True, type="primary")
            clear_btn = clear_col.button("Clear History", use_container_width=True)

            if clear_btn:
                st.session_state.hb_results = []
                st.rerun()

            if ask_btn and question.strip():
                results = search_handbook(question.strip(), handbook_chunks, top_k=5)
                st.session_state.hb_results = [{"q": question.strip(), "pages": results}] + st.session_state.hb_results

            if st.session_state.hb_results:
                st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
                for entry in st.session_state.hb_results:
                    st.markdown(f"""
                    <div style="background:#fff;border:1px solid #b92227;border-radius:8px;padding:14px 18px;margin-bottom:6px;">
                      <div style="font-size:.68rem;color:#1e3158;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">Search</div>
                      <div style="font-size:.92rem;color:#2c3e50;font-style:italic;">"{entry['q']}"</div>
                    </div>
                    """, unsafe_allow_html=True)
                    for page in entry["pages"]:
                        text = page["text"].strip()
                        st.markdown(f"""
                        <div style="background:#f5f8fc;border:1px solid #d0d5e0;border-left:3px solid #b92227;border-radius:0 8px 8px 0;padding:14px 18px;margin-bottom:10px;">
                          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <span style="font-family:'Barlow Condensed',sans-serif;font-size:.75rem;font-weight:700;color:#b92227;text-transform:uppercase;letter-spacing:.08em;">Page {page['page']}</span>
                            <span style="font-size:.68rem;color:#1e4d7b;background:#e8f0ff;padding:2px 8px;border-radius:10px;">{page['chapter']}</span>
                          </div>
                          <div style="font-size:.85rem;color:#2c3e50;line-height:1.6;white-space:pre-wrap;">{text}</div>
                        </div>
                        """, unsafe_allow_html=True)

        with ref_col:
            st.markdown('<div class="lbl">Browse by Chapter</div>', unsafe_allow_html=True)
            chapters = [
                ("Chapter 1", "The Fundamentals",         "Mission, values, expectations, pay chart, appointment types",  "T-Bird expectations sales minimum pay commission"),
                ("Chapter 2", "5-Step Sales Success",     "Sales flow chart, financing 101, daily checklist",              "5-step sales process flow chart visualization"),
                ("Chapter 3", "Insurance 101",            "Claims workflow, overturn process, by-choice appointments",     "insurance claim workflow adjuster appointment"),
                ("Chapter 4", "Full Replacement Bidding", "Consumption chart, GPM magic, shingle costs, warranties",       "full replacement bid calculation GPM shingle cost"),
                ("Chapter 5", "Repair Bidding",           "Repair quotes, labor rates, materials, workmanship warranties", "repair labor rates bid quote materials"),
                ("Chapter 6", "Restoration Bidding",      "Restoration process and pricing",                               "restoration bidding process pricing"),
                ("Chapter 7", "SOPs",                     "Photo requirements, lead SOPs, payment terms, project submission","SOP procedure no-show lead follow-up payment"),
                ("Chapter 8", "Forms",                    "Chimney release, Xactimate, itel request forms",                "forms chimney xactimate itel request"),
                ("Chapter 9", "Sales Tools",              "Presentation folder, digital tools, quote attachments",         "sales tools presentation folder digital quote"),
            ]
            for ch, title, desc, ch_query in chapters:
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"""
                <div class="card" style="margin-bottom:2px;padding:10px 14px;">
                  <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:2px;">
                    <span style="font-family:'Barlow Condensed',sans-serif;font-size:.65rem;font-weight:700;color:#b92227;text-transform:uppercase;letter-spacing:.1em;">{ch}</span>
                    <span style="font-size:.85rem;font-weight:600;color:#1e3158;">{title}</span>
                  </div>
                  <div style="font-size:.72rem;color:#666;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
                if c2.button("Browse", key=f"ch_{ch}", use_container_width=True):
                    st.session_state.hb_pending_q = ch_query
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — INSTALLED JOBS CATALOGUE
# ══════════════════════════════════════════════════════════════════════════════
with tab_jobs:
    render_tab6()
