import streamlit as st
import math

# ─────────────────────────────────────────────
#  PAGE CONFIG & GLOBAL STYLING
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="REEP Pricing Calculator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0f1117;
    color: #e8e8e8;
}
.main-header {
    background: linear-gradient(135deg, #1c1c2e 0%, #16213e 100%);
    border-bottom: 3px solid #f47c20;
    padding: 20px 32px 16px 32px;
    margin: -80px -80px 28px -80px;
}
.main-header h1 {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.0rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.04em;
    margin: 0 0 2px 0;
    text-transform: uppercase;
}
.main-header .accent { color: #f47c20; }
.main-header .subtitle {
    font-size: 0.78rem;
    color: #7788aa;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.section-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #f47c20;
    margin-bottom: 6px;
}
.card { background: #1a1d2e; border: 1px solid #2d3150; border-radius: 8px; padding: 20px 24px; margin-bottom: 14px; }
.card-highlight { background: #1a1d2e; border: 1px solid #f47c20; border-radius: 8px; padding: 20px 24px; margin-bottom: 14px; }
.price-table { width: 100%; border-collapse: collapse; }
.price-table th { font-family:'Barlow Condensed',sans-serif; font-size:0.68rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#7788aa; padding:8px 12px; text-align:left; border-bottom:1px solid #2d3150; }
.price-table td { padding:10px 12px; border-bottom:1px solid #1e2235; font-size:0.92rem; color:#d8d8d8; }
.price-table tr:last-child td { border-bottom: none; }
.price-table tr:hover td { background: #1e2235; }
.price-table .hl-row td { background:#1e2d1e; color:#5dca6f; font-weight:600; }
.price-table .fin-row td { color:#5ba8f5; }
.price-table .big { font-family:'Barlow Condensed',sans-serif; font-size:1.25rem; font-weight:700; color:#f5f5f5; }
.hl-row .big { color: #6dea7f !important; }
.fin-row .big { color: #70b8ff !important; }
.metric-box { background:#1a1d2e; border:1px solid #2d3150; border-radius:8px; padding:14px 10px; text-align:center; }
.metric-val { font-family:'Barlow Condensed',sans-serif; font-size:1.7rem; font-weight:700; color:#f47c20; line-height:1; }
.metric-lbl { font-size:0.65rem; color:#6677aa; text-transform:uppercase; letter-spacing:0.08em; margin-top:4px; }
.chip { display:inline-block; background:#24293e; border:1px solid #3d4465; border-radius:20px; padding:3px 12px; font-size:0.82rem; color:#aab2cc; margin:3px 3px 3px 0; }
.chip strong { color:#e0e0e0; }
.note { background:#1e2438; border-left:3px solid #5ba8f5; border-radius:0 6px 6px 0; padding:9px 14px; font-size:0.82rem; color:#a0b4cc; margin:8px 0; }
.warn { background:#2a1e18; border-left:3px solid #f47c20; border-radius:0 6px 6px 0; padding:9px 14px; font-size:0.82rem; color:#c89060; margin:8px 0; }
.hr { border:none; border-top:1px solid #2d3150; margin:18px 0; }
/* Streamlit widget overrides */
.stSelectbox > div > div, .stNumberInput > div > div > input, .stTextInput > div > div > input {
    background:#1e2235 !important; border:1px solid #3d4465 !important; color:#e8e8e8 !important; border-radius:6px !important;
}
label { color:#9aadcc !important; font-size:0.83rem !important; font-weight:500 !important; }
.stTabs [data-baseweb="tab-list"] { background:#1a1d2e; border-radius:8px 8px 0 0; border-bottom:2px solid #f47c20; gap:0; }
.stTabs [data-baseweb="tab"] { font-family:'Barlow Condensed',sans-serif; font-size:0.95rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; color:#8899aa !important; padding:12px 28px; }
.stTabs [aria-selected="true"] { background:#f47c20 !important; color:#fff !important; border-radius:6px 6px 0 0; }
.stTabs [data-baseweb="tab-panel"] { background:transparent; padding:18px 0 0 0; }
.empty-state { text-align:center; padding:48px 24px; color:#445; }
.empty-state .es-icon { font-size:2.5rem; margin-bottom:8px; }
.empty-state .es-txt { font-family:'Barlow Condensed',sans-serif; font-size:1rem; color:#667799; text-transform:uppercase; letter-spacing:0.06em; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
  <h1>REEP <span class="accent">Pricing</span> Calculator</h1>
  <div class="subtitle">GAF Full Roof Replacement &nbsp;·&nbsp; Repair Jobs &nbsp;·&nbsp; Margin Analysis</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def ru(v):
    return math.ceil(v)

def total_sq_std(sq, facets):
    if facets < 5:      m = 1.12
    elif facets < 7:    m = 1.15
    elif facets <= 20:  m = 1.17
    elif facets <= 35:  m = 1.20
    else:               m = 1.25
    return ru(sq * m)

def total_sq_low(sq, facets, pitch):
    if pitch == 2:
        if facets < 5:     m = 1.17
        elif facets < 7:   m = 1.20
        elif facets <= 20: m = 1.22
        elif facets <= 35: m = 1.25
        else:              m = 1.30
    else:
        if facets < 5:     m = 1.12
        elif facets < 7:   m = 1.15
        elif facets <= 20: m = 1.17
        elif facets <= 35: m = 1.20
        else:              m = 1.25
    return ru(sq * m)

def low_slope_cost(tsq, pitch):
    return tsq * {1: 375, 2: 370, 3: 350}[pitch]

def pidx(pitch):
    if pitch < 8:    return 0
    elif pitch <= 10: return 1
    else:            return 2

RATES = {
    "HDZ":     {"Signature":[286,291,297], "Gold":[325,330,336], "Silver":[310,314,320], "Bronze":[295,301,306]},
    "UHDZ":    {"Signature":[300,305,311], "Gold":[339,344,350], "Silver":[324,328,334], "Bronze":[309,315,320]},
    "Camelot": {"Signature":[485,490,496], "Gold":[524,529,535], "Silver":[509,513,519], "Bronze":[494,500,505]},
}

def full_cost(tsq, pitch, product, tier, extra=0):
    return tsq * RATES[product][tier][pidx(pitch)] + extra

def small_cost(tsq, tier):
    add = {"Signature":0,"Gold":20,"Silver":15,"Bronze":10}[tier]
    lo  = {"Signature":300,"Gold":320,"Silver":315,"Bronze":310}[tier]
    hi  = {"Signature":325,"Gold":345,"Silver":340,"Bronze":335}[tier]
    if   tsq == 1: return 500 + add
    elif tsq == 2: return 800 + add
    elif tsq == 3: return 1050 + add
    elif tsq == 4: return 1300 + add
    elif 5 <= tsq <= 9:  return tsq * lo
    elif 10 <= tsq <= 15: return tsq * hi
    return None

def gpm_price(cost, m):
    return ru(cost / (1 - m))

def deck(low_tsq, std_tsq):
    sheets = ru(((low_tsq + std_tsq) * 100) / 32)
    return sheets, sheets * 35

MATERIALS = [
    (1,  "1x6's",                           11,  "12 ft board"),
    (2,  "3-in-1 Sewer Pipe Flashing",       7,   "each"),
    (3,  "3-in Sewer Pipe Collar",           7,   "each"),
    (4,  "3x3 Edge Metal (Rolled Roofing)", 10,   "10' piece"),
    (5,  "3-Tab Shingles",                  32,   "bundle"),
    (6,  "Architectural Shingles",          37,   "bundle"),
    (7,  "Button Caps",                     27,   "bucket"),
    (8,  "Caulking",                         9,   "tube"),
    (9,  "Coil Nails",                      47,   "box"),
    (10, "HVAC 6-8in Boot",                 40,   "each"),
    (11, "HVAC Cap",                        20,   "each"),
    (12, "Ice & Water Shield",              70,   "2-SQ roll"),
    (13, "Metal Primer (Rolled Roof)",      50,   "quart"),
    (14, "Plywood / OSB",                   25,   "sheet (32 sqft)"),
    (15, "Ridge Cap",                       60,   "20 ln ft"),
    (16, "Ridge Vent",                      12,   "4' piece"),
    (17, "Roll Roofing Base Sheet",        140,   "2-SQ roll"),
    (18, "Roll Roofing Cap Sheet",         140,   "1-SQ roll"),
    (19, "Spray Paint",                     10,   "can"),
    (20, "Standard Drip Edge / Apron",      10,   "10' piece"),
    (21, "Starter Shingles",               60,   "120 ln ft"),
    (22, "Step Flashing",                  65,   "box of 100"),
    (23, "Synthetic Felt",                 95,   "10-SQ roll"),
    (24, "Trim Coil (Counter Flashing)",  110,   "24\"×50' roll"),
    (25, "Excluder Mesh (Rodent/Pest)",    35,   "4\"×60\""),
]

LABOR = [
    ("Under 2 Hours",        250,  "Under 2 hrs work, $99 or less in materials"),
    ("2 Hours",              400,  "$100–$200 materials, 2–3 hrs work"),
    ("3–6 Hours (Half Day)", 750,  "1+ sheet decking, 3–6 bundles, 2-story 8/12+"),
    ("7+ Hours (Full Day)", 1100,  "Any job taking more than 6 hours"),
]


# ─────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────
tab_roof, tab_repair = st.tabs(["🏠  Full Roof Replacement", "🔧  Repair Calculator"])


# ══════════════════════════════════════
#  TAB 1 — FULL ROOF
# ══════════════════════════════════════
with tab_roof:
    left, right = st.columns([1, 1.4], gap="large")

    with left:
        st.markdown('<div class="section-label">Client</div>', unsafe_allow_html=True)
        client = st.text_input("Client", placeholder="Enter client name…", label_visibility="collapsed", key="r_client")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Job Type</div>', unsafe_allow_html=True)
        job_type = st.radio("Job Type", ["Standard (16 SQ+)", "Small Job (1–15 SQ)"],
                            horizontal=True, label_visibility="collapsed")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        std_sq = 0.0; std_tsq = 0; std_pitch = 4; product = "HDZ"; tier = "Signature"
        low_tsq = 0; low_cost_val = 0; add_low = False; sheets = 0; deck_cost = 0

        if "Standard" in job_type:
            st.markdown('<div class="section-label">Standard Slope (4/12 – 13/12)</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: std_sq     = st.number_input("Measured SQ",  0.0, step=0.01, format="%.2f")
            with c2: std_facets = st.number_input("Facets",       0,   step=1,    min_value=0)
            with c3: std_pitch  = st.number_input("Pitch (/12)",  4,   step=1,    min_value=4, max_value=13)
            std_tsq = total_sq_std(std_sq, std_facets) if std_sq > 0 else 0

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            add_low = st.checkbox("➕ Add Low Slope Section (1/12 – 3/12)")
            if add_low:
                st.markdown('<div class="section-label">Low Slope Section</div>', unsafe_allow_html=True)
                lc1, lc2, lc3 = st.columns(3)
                with lc1: low_sq_in   = st.number_input("Low Measured SQ", 0.0, step=0.01, format="%.2f", key="lsq")
                with lc2: low_facets  = st.number_input("Low Facets",       0,   step=1,    min_value=0,   key="lfac")
                with lc3: low_pitch   = st.selectbox("Low Pitch", [1, 2, 3], key="lpit")
                if low_sq_in > 0:
                    low_tsq      = total_sq_low(low_sq_in, low_facets, low_pitch)
                    low_cost_val = low_slope_cost(low_tsq, low_pitch)
                sheets, deck_cost = deck(low_tsq, std_tsq)

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Product & Tier</div>', unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1: product = st.selectbox("Product", ["HDZ", "UHDZ", "Camelot"])
            with p2: tier    = st.selectbox("Tier",    ["Signature", "Gold", "Silver", "Bronze"])

            cost = full_cost(std_tsq, std_pitch, product, tier, extra=low_cost_val) if std_tsq > 0 else 0

        else:  # Small job
            st.markdown('<div class="note">1–9 SQ: 40% minimum GPM &nbsp;|&nbsp; 10–15 SQ: 25% minimum GPM</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Roof Details (HDZ only)</div>', unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns(3)
            with sc1: std_sq     = st.number_input("Measured SQ",  0.0, step=0.01, format="%.2f")
            with sc2: std_facets = st.number_input("Facets",       0,   step=1,    min_value=0)
            with sc3: std_pitch  = st.number_input("Pitch (/12)",  4,   step=1,    min_value=2, max_value=13)
            std_tsq = total_sq_std(std_sq, std_facets) if std_sq > 0 else 0
            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Tier</div>', unsafe_allow_html=True)
            tier = st.selectbox("Tier", ["Signature", "Gold", "Silver", "Bronze"])
            product = "HDZ"
            raw_cost = small_cost(std_tsq, tier) if std_tsq > 0 else 0
            cost = raw_cost if raw_cost else 0

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Custom GPM (optional)</div>', unsafe_allow_html=True)
        use_cust = st.checkbox("Enable custom GPM", key="r_cust")
        custom_gpm = None
        if use_cust:
            custom_gpm = st.slider("Custom GPM", 0.10, 0.75, 0.60, 0.01, format="%.0f%%")

        # Metrics
        if std_sq > 0 and cost > 0:
            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f'<div class="metric-box"><div class="metric-val">{std_tsq}</div><div class="metric-lbl">Adj. SQ</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-box"><div class="metric-val">${cost:,.0f}</div><div class="metric-lbl">Total Cost</div></div>', unsafe_allow_html=True)
            with m3:
                cpsq = cost / std_tsq if std_tsq else 0
                st.markdown(f'<div class="metric-box"><div class="metric-val">${cpsq:,.0f}</div><div class="metric-lbl">Cost / SQ</div></div>', unsafe_allow_html=True)
            if add_low and low_tsq > 0:
                st.markdown(f'<div class="note">Low slope: {low_tsq} adj. SQ · ${low_cost_val:,.0f} cost &nbsp;|&nbsp; Deck over: {sheets} sheets · ${deck_cost:,.0f}</div>', unsafe_allow_html=True)

    # ── RIGHT: Price Table
    with right:
        st.markdown('<div class="section-label">Pricing Breakdown</div>', unsafe_allow_html=True)
        if std_sq == 0 or cost == 0:
            st.markdown('<div class="card"><div class="empty-state"><div class="es-icon">📐</div><div class="es-txt">Enter job details to see pricing</div></div></div>', unsafe_allow_html=True)
        else:
            # Chips
            cl = client or "—"
            st.markdown(f'''
            <div class="chip">Client: <strong>{cl}</strong></div>
            <div class="chip">{product} {tier}</div>
            <div class="chip">Pitch {std_pitch}/12</div>
            <br><br>
            ''', unsafe_allow_html=True)

            margins = [
                (0.40, "40% GPM", "", False),
                (0.35, "35% GPM", "", False),
                (None, "Financing (30% base)", "fin-row", True),
                (0.30, "30% GPM", "", False),
                (0.25, "25% GPM", "", False),
                (0.20, "20% GPM", "", False),
                (0.18, "18% GPM", "", False),
                (None, "Lowest Financing (18% base)", "fin-row", True),
            ]

            pa = {m: gpm_price(cost, m) for m, *_ in margins if m}

            rows_html = ""
            for entry in margins:
                m, label, cls, is_fin = entry
                if is_fin:
                    if "Lowest" in label:
                        p = pa[0.18] * 1.07
                    else:
                        p = pa[0.30] * 1.07
                    ppsq = p / std_tsq if std_tsq else 0
                    rows_html += f'<tr class="{cls}"><td>{label}</td><td>—</td><td class="big">${p:,.0f}</td><td>${ppsq:,.0f}/SQ</td></tr>'
                else:
                    p    = pa[m]
                    ppsq = p / std_tsq if std_tsq else 0
                    row_cls = "hl-row" if m == 0.40 else ""
                    rows_html += f'<tr class="{row_cls}"><td>{label}</td><td>{int(m*100)}%</td><td class="big">${p:,.0f}</td><td>${ppsq:,.0f}/SQ</td></tr>'

            if use_cust and custom_gpm:
                cp   = gpm_price(cost, custom_gpm)
                cf   = cp * 1.07
                cp_sq = cp / std_tsq if std_tsq else 0
                cf_sq = cf / std_tsq if std_tsq else 0
                rows_html += f'''
                <tr><td colspan="4"><hr style="border-color:#2d3150;margin:2px 0;"></td></tr>
                <tr class="hl-row">
                  <td>Custom {int(custom_gpm*100)}% GPM</td><td>{int(custom_gpm*100)}%</td>
                  <td class="big">${cp:,.0f}</td><td>${cp_sq:,.0f}/SQ</td>
                </tr>
                <tr class="fin-row">
                  <td>Custom GPM + Financing</td><td>—</td>
                  <td class="big">${cf:,.0f}</td><td>${cf_sq:,.0f}/SQ</td>
                </tr>'''

            st.markdown(f'''
            <div class="card-highlight">
              <table class="price-table">
                <thead><tr><th>Level</th><th>GPM</th><th>Sale Price</th><th>Per SQ</th></tr></thead>
                <tbody>{rows_html}</tbody>
              </table>
            </div>
            ''', unsafe_allow_html=True)


# ══════════════════════════════════════
#  TAB 2 — REPAIR CALCULATOR
# ══════════════════════════════════════
with tab_repair:
    rl, rr = st.columns([1.1, 1], gap="large")

    with rl:
        st.markdown('<div class="section-label">Client</div>', unsafe_allow_html=True)
        rep_client = st.text_input("Repair Client", placeholder="Enter client name…",
                                   label_visibility="collapsed", key="rep_client")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Materials — Enter Quantities Used</div>', unsafe_allow_html=True)

        quantities = {}
        cols = st.columns(2)
        for i, (mid, name, price, unit) in enumerate(MATERIALS):
            with cols[i % 2]:
                qty = st.number_input(
                    f"{name}  (${price}/{unit})",
                    min_value=0.0, value=0.0, step=1.0, format="%.0f",
                    key=f"m_{mid}"
                )
                quantities[mid] = qty

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Labor Tier</div>', unsafe_allow_html=True)
        labor_opts = [f"{l[0]}  —  ${l[1]:,}  ·  {l[2]}" for l in LABOR]
        labor_sel  = st.radio("Labor", labor_opts, label_visibility="collapsed")
        labor_idx  = labor_opts.index(labor_sel)
        labor_cost = LABOR[labor_idx][1]

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        use_cust_r = st.checkbox("Enable custom GPM", key="rep_cust")
        custom_gpm_r = None
        if use_cust_r:
            custom_gpm_r = st.slider("Repair Custom GPM", 0.10, 0.75, 0.60, 0.01,
                                     format="%.0f%%", key="rep_gpm")

    with rr:
        mat_cost   = sum(quantities[mid] * price for mid, _, price, _ in MATERIALS)
        total_cost = mat_cost + labor_cost
        used       = [(name, quantities[mid], price, quantities[mid]*price)
                      for mid, name, price, _ in MATERIALS if quantities[mid] > 0]

        st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)
        rm1, rm2, rm3 = st.columns(3)
        with rm1: st.markdown(f'<div class="metric-box"><div class="metric-val">${mat_cost:,.0f}</div><div class="metric-lbl">Materials</div></div>', unsafe_allow_html=True)
        with rm2: st.markdown(f'<div class="metric-box"><div class="metric-val">${labor_cost:,.0f}</div><div class="metric-lbl">Labor</div></div>', unsafe_allow_html=True)
        with rm3: st.markdown(f'<div class="metric-box"><div class="metric-val">${total_cost:,.0f}</div><div class="metric-lbl">Total Cost</div></div>', unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)

        if used:
            st.markdown('<div class="section-label">Materials Used</div>', unsafe_allow_html=True)
            chips = "".join(f'<div class="chip"><strong>{n}</strong> ×{int(q)} = ${t:,.0f}</div>'
                            for n, q, p, t in used)
            st.markdown(f'<div style="margin-bottom:14px">{chips}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label">Pricing Breakdown</div>', unsafe_allow_html=True)

        if total_cost == 0:
            st.markdown('<div class="card"><div class="empty-state"><div class="es-icon">🔧</div><div class="es-txt">Add materials & labor to see pricing</div></div></div>', unsafe_allow_html=True)
        else:
            rep_margins = [0.40, 0.45, 0.50, 0.55, 0.60]
            rows_html = ""

            if use_cust_r and custom_gpm_r:
                cp  = gpm_price(total_cost, custom_gpm_r)
                cf  = ru(cp * 1.07)
                rows_html += f'''
                <tr class="hl-row">
                  <td>Custom {int(custom_gpm_r*100)}% GPM</td><td>{int(custom_gpm_r*100)}%</td><td class="big">${cp:,.0f}</td>
                </tr>
                <tr class="fin-row">
                  <td>Custom GPM + Financing</td><td>—</td><td class="big">${cf:,.0f}</td>
                </tr>
                <tr><td colspan="3"><hr style="border-color:#2d3150;margin:2px 0;"></td></tr>'''

            for m in rep_margins:
                p = gpm_price(total_cost, m)
                rows_html += f'<tr><td>{int(m*100)}% GPM</td><td>{int(m*100)}%</td><td class="big">${p:,.0f}</td></tr>'

            # Standard financing on 60%
            base_fin = gpm_price(total_cost, 0.60)
            fin_pr   = ru(base_fin * 1.07)
            rows_html += f'<tr class="fin-row"><td>Financing (60% base)</td><td>—</td><td class="big">${fin_pr:,.0f}</td></tr>'

            rc = rep_client or "—"
            st.markdown(f'''
            <div class="chip">Client: <strong>{rc}</strong></div>
            <div class="chip">Labor: <strong>{LABOR[labor_idx][0]}</strong></div>
            <div class="chip">Items used: <strong>{len(used)}</strong></div>
            <br><br>
            <div class="card-highlight">
              <table class="price-table">
                <thead><tr><th>Level</th><th>GPM</th><th>Sale Price</th></tr></thead>
                <tbody>{rows_html}</tbody>
              </table>
            </div>
            ''', unsafe_allow_html=True)
