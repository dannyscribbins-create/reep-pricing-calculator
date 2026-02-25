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

def get_gemini_model(api_key):
    """Find the first available Gemini model on this key."""
    import urllib.request
    candidates = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.0-pro-latest",
        "gemini-1.0-pro",
        "gemini-pro",
    ]
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
            available = [m["name"].replace("models/", "") for m in data.get("models", [])
                         if "generateContent" in m.get("supportedGenerationMethods", [])]
            for c in candidates:
                if c in available:
                    return c
            # Return first available generateContent model
            return available[0] if available else "gemini-pro"
    except Exception:
        return "gemini-pro"

def ask_handbook(question, chunks, api_key):
    """Call Gemini API with relevant handbook chunks."""
    import urllib.request, urllib.error
    relevant = search_handbook(question, chunks, top_k=10)
    context = "\n\n".join(
        f"[Page {c['page']} — {c['chapter']}]\n{c['text']}"
        for c in relevant
    )
    prompt = """You are a helpful assistant for Thunderbird / Accent Roofing sales representatives.
You answer questions ONLY using the provided handbook excerpts below.

Rules:
- Answer clearly and directly.
- Always cite the source as "Page X — Chapter Name" at the end of your answer.
- If multiple pages are relevant, cite all of them.
- If the answer is not found in the excerpts, say: "I couldn't find that in the handbook. Try searching Chapter X or ask your manager."
- Never make up information not in the excerpts.
- Keep answers concise but complete — use bullet points for multi-step processes.

HANDBOOK EXCERPTS:
""" + context + "\n\nQUESTION: " + question

    model = get_gemini_model(api_key)
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.1}
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text, relevant
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        return f"API error ({model}): {e.code} — {err}", []
    except Exception as e:
        return f"Error: {str(e)}", []
import json
import re
import os

st.set_page_config(page_title="REEP Pricing Calculator", page_icon="🏠", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Barlow', sans-serif; background:#0f1117; color:#e8e8e8; }
.hdr { background:linear-gradient(135deg,#1c1c2e,#16213e); border-bottom:3px solid #f47c20;
       padding:18px 32px 14px; margin:-80px -80px 24px -80px; }
.hdr h1 { font-family:'Barlow Condensed',sans-serif; font-size:1.9rem; font-weight:800;
           color:#fff; letter-spacing:.04em; margin:0 0 2px; text-transform:uppercase; }
.hdr .acc { color:#f47c20; }
.hdr .sub { font-size:.75rem; color:#7788aa; letter-spacing:.1em; text-transform:uppercase; }
.lbl { font-family:'Barlow Condensed',sans-serif; font-size:.68rem; font-weight:700;
       letter-spacing:.14em; text-transform:uppercase; color:#f47c20; margin-bottom:5px; }
.card  { background:#1a1d2e; border:1px solid #2d3150; border-radius:8px; padding:18px 22px; margin-bottom:12px; }
.cardb { background:#1a1d2e; border:1px solid #f47c20; border-radius:8px; padding:18px 22px; margin-bottom:12px; }
.ptbl { width:100%; border-collapse:collapse; }
.ptbl th { font-family:'Barlow Condensed',sans-serif; font-size:.66rem; font-weight:700;
           letter-spacing:.1em; text-transform:uppercase; color:#7788aa;
           padding:7px 10px; text-align:left; border-bottom:1px solid #2d3150; }
.ptbl td { padding:9px 10px; border-bottom:1px solid #1e2235; font-size:.9rem; color:#d0d0d0; }
.ptbl tr:last-child td { border-bottom:none; }
.ptbl tr:hover td { background:#1e2235; }
.ptbl .hlr td  { background:#1e2d1e; color:#5dca6f; font-weight:600; }
.ptbl .finr td { color:#5ba8f5; }
.ptbl .big     { font-family:'Barlow Condensed',sans-serif; font-size:1.2rem; font-weight:700; color:#f5f5f5; }
.hlr  .big     { color:#6dea7f !important; }
.finr .big     { color:#70b8ff !important; }
.mbox { background:#1a1d2e; border:1px solid #2d3150; border-radius:8px; padding:12px 8px; text-align:center; }
.mval { font-family:'Barlow Condensed',sans-serif; font-size:1.6rem; font-weight:700; color:#f47c20; line-height:1; }
.mlbl { font-size:.62rem; color:#6677aa; text-transform:uppercase; letter-spacing:.08em; margin-top:3px; }
.chip { display:inline-block; background:#24293e; border:1px solid #3d4465; border-radius:20px;
        padding:3px 11px; font-size:.8rem; color:#aab2cc; margin:3px 3px 3px 0; }
.chip strong { color:#e0e0e0; }
.note { background:#1e2438; border-left:3px solid #5ba8f5; border-radius:0 6px 6px 0; padding:8px 12px; font-size:.8rem; color:#a0b4cc; margin:6px 0; }
.warn { background:#2a1e18; border-left:3px solid #f47c20; border-radius:0 6px 6px 0; padding:8px 12px; font-size:.8rem; color:#c89060; margin:6px 0; }
.info { background:#1e2820; border-left:3px solid #5dca6f; border-radius:0 6px 6px 0; padding:8px 12px; font-size:.8rem; color:#88bb88; margin:6px 0; }
.hr   { border:none; border-top:1px solid #2d3150; margin:14px 0; }
.stSelectbox>div>div, .stNumberInput>div>div>input, .stTextInput>div>div>input {
    background:#1e2235 !important; border:1px solid #3d4465 !important; color:#e8e8e8 !important; border-radius:6px !important; }
label { color:#9aadcc !important; font-size:.82rem !important; font-weight:500 !important; }
.stTabs [data-baseweb="tab-list"] { background:#1a1d2e; border-radius:8px 8px 0 0; border-bottom:2px solid #f47c20; gap:0; }
.stTabs [data-baseweb="tab"] { font-family:'Barlow Condensed',sans-serif; font-size:.9rem; font-weight:700;
    letter-spacing:.05em; text-transform:uppercase; color:#8899aa !important; padding:10px 22px; }
.stTabs [aria-selected="true"] { background:#f47c20 !important; color:#fff !important; border-radius:6px 6px 0 0; }
.stTabs [data-baseweb="tab-panel"] { background:transparent; padding:16px 0 0; }
.empty { text-align:center; padding:44px 24px; }
.empty .ei { font-size:2.2rem; margin-bottom:8px; }
.empty .et { font-family:'Barlow Condensed',sans-serif; font-size:.95rem; color:#667799; text-transform:uppercase; letter-spacing:.06em; }
.wtbl { width:100%; border-collapse:collapse; margin-top:6px; }
.wtbl th { background:#24293e; font-family:'Barlow Condensed',sans-serif; font-size:.68rem;
           font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#aab2cc;
           padding:8px 10px; text-align:left; border:1px solid #2d3150; }
.wtbl td { padding:8px 10px; font-size:.82rem; border:1px solid #2d3150; color:#c0c8d8; }
.wtbl tr:nth-child(even) td { background:#1a1d2e; }
.tier-sig { color:#ffd700 !important; font-weight:700 !important; }
.tier-gld { color:#f47c20 !important; font-weight:700 !important; }
.tier-sil { color:#aab8cc !important; font-weight:700 !important; }
.tier-brz { color:#cd7f32 !important; font-weight:700 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hdr">
  <h1>REEP <span class="acc">Pricing</span> Calculator</h1>
  <div class="sub">Full Roof · Small Jobs · Repairs · All Products</div>
</div>
""", unsafe_allow_html=True)

# ─── HELPERS ────────────────────────────────────────────────────────
def ru(v):
    return math.ceil(v)

def waste_std(sq, facets):
    if facets < 5:      m = 1.12
    elif facets < 7:    m = 1.15
    elif facets <= 20:  m = 1.17
    elif facets <= 35:  m = 1.20
    else:               m = 1.25
    return ru(sq * m)

def waste_low(sq, facets, pitch):
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

def low_cost_val(tsq, pitch):
    return tsq * {1: 375, 2: 370, 3: 350}[pitch]

def pidx(p):
    if 4 <= p <= 7:    return 0
    elif 8 <= p <= 10: return 1
    else:              return 2

RATES = {
    "HDZ":                {"Signature":[296,301,307],"Gold":[335,340,346],"Silver":[320,324,330],"Bronze":[305,311,316]},
    "UHDZ":               {"Signature":[317,322,328],"Gold":[356,361,367],"Silver":[341,345,351],"Bronze":[326,332,337]},
    "CAM II / Slateline": {"Signature":[481,486,492],"Gold":[520,525,531],"Silver":[505,509,515],"Bronze":[490,496,501]},
    "CT Landmark":        {"3-Star Land":[307,311,317],"3-Star Pro":[311,315,321],"4-Star Land":[322,327,333],"4-Star Pro":[326,331,337]},
    "OC / RS / Prud":     {"OC Dur":[301,306,312],"Royal Sov":[283,288,294],"Prud":[345,350,360]},
}

TIERS = {
    "HDZ":                ["Signature","Gold","Silver","Bronze"],
    "UHDZ":               ["Signature","Gold","Silver","Bronze"],
    "CAM II / Slateline": ["Signature","Gold","Silver","Bronze"],
    "CT Landmark":        ["3-Star Land","3-Star Pro","4-Star Land","4-Star Pro"],
    "OC / RS / Prud":     ["OC Dur","Royal Sov","Prud"],
}

TIER_CLS = {
    "Signature":"tier-sig","Gold":"tier-gld","Silver":"tier-sil","Bronze":"tier-brz",
    "3-Star Land":"tier-sil","3-Star Pro":"tier-sil","4-Star Land":"tier-gld","4-Star Pro":"tier-gld",
    "OC Dur":"tier-sig","Royal Sov":"tier-sil","Prud":"tier-gld",
}

LARGE_GPMS = [
    (0.39, "39% GPM",   False),
    (0.37, "37% GPM",   False),
    ("fin35", "Financing (35% base)", True),
    (0.35, "35% GPM",   False),
    (0.32, "32% GPM",   False),
    (0.26, "26% GPM",   False),
    ("fin18", "Lowest Financing (18% base)", True),
    (0.18, "18% GPM",   False),
]

SMALL_GPMS = [
    (0.60, "60% GPM",   False),
    (0.50, "50% GPM",   False),
    ("fin40", "Financing (40% base)", True),
    (0.40, "40% GPM",   False),
    (0.35, "35% GPM",   False),
    (0.30, "30% GPM",   False),
    ("fin20", "Lowest Financing (20% base)", True),
    (0.20, "20% GPM",   False),
]

def gp(cost, m):
    return ru(cost / (1 - m))

def cost_large(std_tsq, pitch, product, tier, lc=0):
    return std_tsq * RATES[product][tier][pidx(pitch)] + lc

def cost_small(total_tsq, tier):
    hi = {"Signature": 335, "Gold": 365, "Silver": 355, "Bronze": 345}[tier]
    if total_tsq == 1:              return 500
    if total_tsq == 2:              return 800
    if 3 <= total_tsq <= 9:         return total_tsq * 350
    if 10 <= total_tsq <= 19:       return total_tsq * hi
    return None

def price_rows(cost, gpm_list, custom_gpm=None):
    pa = {m: gp(cost, m) for m, _, _ in gpm_list if isinstance(m, float)}
    rows = []
    for m, label, is_fin in gpm_list:
        if   m == "fin35": p = pa[0.35] * 1.07
        elif m == "fin18": p = pa[0.18] * 1.07
        elif m == "fin40": p = pa[0.40] * 1.07
        elif m == "fin20": p = pa[0.20] * 1.07
        else:              p = pa[m]
        rows.append((label, f"{int(m*100)}%" if isinstance(m, float) else "—", p, is_fin))
    if custom_gpm:
        cp = gp(cost, custom_gpm)
        cf = cp * 1.07
        rows.append((f"Custom {int(custom_gpm*100)}% GPM", f"{int(custom_gpm*100)}%", cp, False))
        rows.append(("Custom GPM + Financing", "—", cf, True))
    return rows

def render_table(rows, std_tsq, show_sq=True):
    html = ""
    for i, (label, m_lbl, p, is_fin) in enumerate(rows):
        cls  = "finr" if is_fin else ("hlr" if i == 0 else "")
        ppsq = f"${p/std_tsq:,.0f}/SQ" if (show_sq and std_tsq > 0) else ""
        sq_td = f"<td>{ppsq}</td>" if show_sq else ""
        html += f'<tr class="{cls}"><td>{label}</td><td>{m_lbl}</td><td class="big">${p:,.0f}</td>{sq_td}</tr>'
    hdr_sq = "<th>Per SQ</th>" if show_sq else ""
    return f'<div class="cardb"><table class="ptbl"><thead><tr><th>Level</th><th>GPM</th><th>Sale Price</th>{hdr_sq}</tr></thead><tbody>{html}</tbody></table></div>'

def deck_info(total_tsq, gpm=0.33):
    sheets = ru((total_tsq * 100) / 32)
    cost   = sheets * 35
    price  = ru(cost / (1 - gpm))
    return sheets, cost, price

MATERIALS = [
    ("1x6's",                          11, "12 ft board"),
    ("3-in-1 Sewer Pipe Flashing",      7, "each"),
    ("3-in Sewer Pipe Collar",          7, "each"),
    ("3x3 Edge Metal (Rolled Roofing)", 10, "10' piece"),
    ("3-Tab Shingles",                  32, "bundle"),
    ("Architectural Shingles",          37, "bundle"),
    ("Button Caps",                     27, "bucket"),
    ("Caulking",                         9, "tube"),
    ("Coil Nails",                      47, "box"),
    ("HVAC 6-8in Boot",                 40, "each"),
    ("HVAC Cap",                        20, "each"),
    ("Ice & Water Shield",              70, "2-SQ roll"),
    ("Metal Primer (Rolled Roof)",      50, "quart"),
    ("Plywood / OSB",                   25, "sheet (32 sqft)"),
    ("Ridge Cap",                       60, "20 ln ft"),
    ("Ridge Vent",                      12, "4' piece"),
    ("Roll Roofing Base Sheet",        140, "2-SQ roll"),
    ("Roll Roofing Cap Sheet",         140, "1-SQ roll"),
    ("Spray Paint",                     10, "can"),
    ("Standard Drip Edge / Apron",      10, "10' piece"),
    ("Starter Shingles",                60, "120 ln ft"),
    ("Step Flashing",                   65, "box of 100"),
    ("Synthetic Felt",                  95, "10-SQ roll"),
    ("Trim Coil (Counter Flashing)",   110, "24x50' roll"),
]

LABOR = [
    ("Under 2 Hours",        250, "Under 2 hrs work, $99 or less in materials"),
    ("2 Hours",              400, "$100-$200 materials, 2-3 hrs work"),
    ("3-6 Hours (Half Day)", 750, "1+ sheet decking, 3-6 bundles, 2-story 8/12+"),
    ("7+ Hours (Full Day)", 1100, "Any job taking more than 6 hours"),
]

TICKS = '<div style="display:flex;justify-content:space-between;margin:-10px 0 10px 0;padding:0 4px;"><div style="text-align:center"><div style="width:1px;height:6px;background:#3d4465;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#6677aa">0%</span></div><div style="text-align:center"><div style="width:1px;height:6px;background:#f47c20;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#f47c20">25%</span></div><div style="text-align:center"><div style="width:1px;height:6px;background:#f47c20;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#f47c20">50%</span></div><div style="text-align:center"><div style="width:1px;height:6px;background:#f47c20;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#f47c20">75%</span></div><div style="text-align:center"><div style="width:1px;height:6px;background:#3d4465;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#6677aa">100%</span></div></div>'

CPO_DATA = {
    "Workmanship":    ["15 Year", "15 Year", "15 Year (10 backed by GAF)", "25 Year (25 backed by GAF)"],
    "Material/Labor": ["50 Year (Pro-rated)", "50 Year (Not Pro-rated)", "50 Year (Not Pro-rated)", "50 Year (Not Pro-rated)"],
    "Flashing":       ["R&R Step Flashing as needed", "R&R Step Flashing as needed", "R&R Step Flashing as needed", "Replace ALL step flashing"],
    "Sewer Pipe":     ["Standard", "Standard", "Standard", "Upgrade to Perma Boots"],
}

# Client-facing tier info — order: Signature, Bronze, Silver, Gold (index matches CPO_DATA)
TIER_PACKAGE_NAMES = {
    "Signature": "Signature Protection",
    "Bronze":    "Bronze Protection",
    "Silver":    "Silver Protection",
    "Gold":      "Gold Protection",
}

TIER_FEATURES = {
    "Signature": [
        "50-Year Pro-Rated Material Warranty",
        "15-Year Workmanship Warranty",
        "Step Flashing Replaced As Needed",
        "Standard Pipe Boot Replacement",
        "Professional Installation",
    ],
    "Bronze": [
        "50-Year Non Pro-Rated Material Warranty",
        "15-Year Workmanship Warranty",
        "Step Flashing Replaced As Needed",
        "Standard Pipe Boot Replacement",
        "Professional Installation",
    ],
    "Silver": [
        "50-Year Non Pro-Rated Material Warranty",
        "15-Year GAF-Backed Workmanship Warranty",
        "Step Flashing Replaced As Needed",
        "Standard Pipe Boot Replacement",
        "Professional Installation",
    ],
    "Gold": [
        "50-Year Non Pro-Rated Material Warranty",
        "25-Year GAF-Backed Workmanship Warranty",
        "ALL Step Flashing Replaced",
        "Perma-Boot Pipe Boot Upgrade",
        "Professional Installation",
        "Maximum Coverage & Peace of Mind",
    ],
}

# Presentation display order: low → high tier
CPO_DISPLAY_ORDER = ["Signature", "Bronze", "Silver", "Gold"]

TIER_BADGE_COLORS = {
    "Signature": ("#ffd700", "#1a1700"),
    "Bronze":    ("#cd7f32", "#1a0f00"),
    "Silver":    ("#aab8cc", "#111622"),
    "Gold":      ("#f47c20", "#1a0f00"),
}

def render_cpo_presentation(client_name, product, tiers_with_prices, financing=True):
    """Render a client-facing CPO presentation card grid."""
    # Filter to only HDZ-style tiers that have feature data
    display_tiers = [t for t in CPO_DISPLAY_ORDER if t in tiers_with_prices]
    if not display_tiers:
        display_tiers = list(tiers_with_prices.keys())

    cards_html = ""
    for tier in display_tiers:
        cash_price, fin_price = tiers_with_prices[tier]
        pkg_name  = TIER_PACKAGE_NAMES.get(tier, tier)
        features  = TIER_FEATURES.get(tier, [])
        badge_fg, badge_bg = TIER_BADGE_COLORS.get(tier, ("#ffffff", "#1a1d2e"))

        feat_html = "".join(
            f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:7px;">'
            f'<span style="color:#5dca6f;font-size:.85rem;margin-top:1px;flex-shrink:0;">✓</span>'
            f'<span style="font-size:.82rem;color:#c8d0e0;line-height:1.3;">{f}</span>'
            f'</div>'
            for f in features
        )

        fin_html = (
            f'<div style="margin-top:10px;padding-top:10px;border-top:1px solid #2d3150;">'
            f'<div style="font-size:.65rem;color:#7788aa;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px;">Finance Option</div>'
            f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.4rem;font-weight:700;color:#70b8ff;">${fin_price:,.0f}</div>'
            f'</div>'
        ) if financing and fin_price else ""

        cards_html += f"""
        <div style="background:#1a1d2e;border:1px solid #2d3150;border-radius:10px;padding:20px;flex:1;min-width:160px;display:flex;flex-direction:column;">
          <div style="background:{badge_bg};border:1px solid {badge_fg}44;border-radius:6px;padding:6px 10px;margin-bottom:14px;text-align:center;">
            <div style="font-family:'Barlow Condensed',sans-serif;font-size:.65rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{badge_fg};margin-bottom:1px;">{tier}</div>
            <div style="font-size:.75rem;color:{badge_fg}cc;">{pkg_name}</div>
          </div>
          <div style="margin-bottom:14px;">
            <div style="font-size:.62rem;color:#7788aa;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px;">Cash Price</div>
            <div style="font-family:'Barlow Condensed',sans-serif;font-size:2rem;font-weight:800;color:#ffffff;line-height:1;">${cash_price:,.0f}</div>
          </div>
          <div style="flex:1;margin-bottom:4px;">{feat_html}</div>
          {fin_html}
        </div>"""

    client_line = f'<div style="font-size:.78rem;color:#7788aa;margin-bottom:14px;letter-spacing:.04em;">Prepared for: <strong style="color:#c0c8d8;">{client_name}</strong> &nbsp;·&nbsp; {product}</div>' if client_name and client_name != "—" else f'<div style="font-size:.78rem;color:#7788aa;margin-bottom:14px;">{product}</div>'

    return f"""
    <div style="background:#0f1117;border:1px solid #f47c2033;border-radius:10px;padding:20px;">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:.7rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#f47c20;margin-bottom:6px;">Client Presentation</div>
      {client_line}
      <div style="display:flex;gap:12px;flex-wrap:wrap;">{cards_html}</div>
      <div style="margin-top:14px;font-size:.68rem;color:#445566;text-align:center;">Prices include all labor, materials, and cleanup. Ask your representative about available financing options.</div>
    </div>"""

# ─── TABS ────────────────────────────────────────────────────────────
tab_large, tab_small, tab_repair, tab_cpo, tab_handbook = st.tabs([
    "🏠  Full Roof (20 SQ+)",
    "📐  Small Job (< 20 SQ)",
    "🔧  Repair Calculator",
    "📋  CPO & Rate Guide",
    "📖  Handbook Q&A",
])

# ══════════════════════════════════════════════════════
#  TAB 1 — FULL ROOF (20 SQ+)
# ══════════════════════════════════════════════════════
with tab_large:
    inp_col, out_col = st.columns([1, 1.5], gap="large")

    with inp_col:
        st.markdown('<div class="lbl">Client</div>', unsafe_allow_html=True)
        client = st.text_input("Client", placeholder="Enter client name...", label_visibility="collapsed", key="lg_client")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Standard Slope Section (4/12 - 13/12)</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: std_sq    = st.number_input("Measured SQ",  min_value=0.0, value=0.0, step=0.01, format="%.2f", key="lg_sq")
        with c2: std_fac   = st.number_input("Facets",       min_value=0,   value=0,   step=1,    key="lg_fac")
        with c3: std_pitch = st.number_input("Pitch (/12)",  min_value=4,   value=8,   step=1, max_value=13, key="lg_pit")
        std_tsq = waste_std(std_sq, std_fac) if std_sq > 0 else 0
        c1.markdown(f'<div style="font-size:.72rem;color:#f47c20;margin-top:-10px;padding-left:2px;">Adj: <strong>{std_tsq} SQ</strong></div>' if std_sq > 0 else '<div style="font-size:.72rem;color:#3d4465;margin-top:-10px;padding-left:2px;">Adj: — SQ</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        add_low = st.checkbox("Add Low Slope Section (1/12 - 3/12)", key="lg_addlow")
        low_tsq = 0; low_lc = 0
        if add_low:
            st.markdown('<div class="lbl">Low Slope Section</div>', unsafe_allow_html=True)
            lc1, lc2, lc3 = st.columns(3)
            with lc1: lsq    = st.number_input("Low Measured SQ", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="lg_lsq")
            with lc2: lfac   = st.number_input("Low Facets",      min_value=0,   value=0,   step=1,    key="lg_lfac")
            with lc3: lpitch = st.selectbox("Low Pitch", [1, 2, 3], key="lg_lpit")
            if lsq > 0:
                low_tsq = waste_low(lsq, lfac, lpitch)
                lc1.markdown(f'<div style="font-size:.72rem;color:#f47c20;margin-top:-10px;padding-left:2px;">Adj: <strong>{low_tsq} SQ</strong></div>', unsafe_allow_html=True)
                low_lc  = low_cost_val(low_tsq, lpitch)

        total_tsq = std_tsq + low_tsq

        if std_sq > 0 and total_tsq < 20:
            st.markdown('<div class="warn">Under 20 SQ - use the Small Job tab instead.</div>', unsafe_allow_html=True)
        elif std_sq > 0:
            st.markdown(f'<div class="info">Total: {total_tsq} adj. SQ - qualifies as full roof job.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Product Line</div>', unsafe_allow_html=True)
        product = st.selectbox("Product", list(RATES.keys()), key="lg_prod")

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        use_cust = st.checkbox("Enable custom GPM", key="lg_cust")
        custom_gpm = None
        if use_cust:
            custom_gpm = st.slider("Custom GPM", min_value=0.01, max_value=0.99, value=0.32, step=0.01, format="%.0f%%", key="lg_gpm")
            st.markdown(TICKS, unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Deck Over GPM</div>', unsafe_allow_html=True)
        deck_gpm = st.slider("Deck GPM", min_value=0.01, max_value=0.99, value=0.33, step=0.01, format="%.0f%%", key="lg_deck_gpm")
        st.markdown(TICKS, unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Client Presentation Price</div>', unsafe_allow_html=True)
        pres_margin_opts = {"39% Margin": 0.39, "37% Margin": 0.37, "35% Margin": 0.35, "32% Margin": 0.32, "Custom GPM": None}
        pres_margin_label = st.selectbox("Presentation margin", list(pres_margin_opts.keys()), index=2, label_visibility="collapsed", key="lg_pres_margin")
        pres_margin = pres_margin_opts[pres_margin_label]
        if pres_margin is None:
            pres_margin = custom_gpm if custom_gpm else 0.35
        show_financing = st.checkbox("Show financing price on presentation", value=True, key="lg_show_fin")

        if std_tsq > 0:
            sh, sh_cost, sh_price = deck_info(total_tsq, deck_gpm)
            m1, m2, m3 = st.columns(3)
            with m1: st.markdown(f'<div class="mbox"><div class="mval">{total_tsq}</div><div class="mlbl">Adj. SQ</div></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="mbox"><div class="mval">{sh}</div><div class="mlbl">Deck Sheets</div></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="mbox"><div class="mval">${sh_price:,.0f}</div><div class="mlbl">Deck Price</div></div>', unsafe_allow_html=True)
            if add_low and low_tsq > 0:
                st.markdown(f'<div class="note">Low slope: {low_tsq} adj. SQ - ${low_lc:,.0f} added to all tier costs</div>', unsafe_allow_html=True)

    with out_col:
        st.markdown('<div class="lbl">Pricing by Tier</div>', unsafe_allow_html=True)
        if std_sq == 0:
            st.markdown('<div class="card"><div class="empty"><div class="ei">📐</div><div class="et">Enter roof measurements to see pricing</div></div></div>', unsafe_allow_html=True)
        elif total_tsq < 20:
            st.markdown('<div class="card"><div class="empty"><div class="ei">📐</div><div class="et">Under 20 SQ - switch to Small Job tab</div></div></div>', unsafe_allow_html=True)
        else:
            cl = client or "—"
            st.markdown(f'<div class="chip">Client: <strong>{cl}</strong></div><div class="chip">{product}</div><div class="chip">Pitch {std_pitch}/12</div><div class="chip">Std SQ: <strong>{std_tsq}</strong></div><br><br>', unsafe_allow_html=True)
            tiers = TIERS[product]
            tier_tabs = st.tabs(tiers)
            for i, tier in enumerate(tiers):
                with tier_tabs[i]:
                    c = cost_large(std_tsq, std_pitch, product, tier, lc=low_lc)
                    cpsq = c / std_tsq if std_tsq else 0
                    rows = price_rows(c, LARGE_GPMS, custom_gpm)
                    t1, t2, t3 = st.columns(3)
                    with t1: st.markdown(f'<div class="mbox"><div class="mval">${c:,.0f}</div><div class="mlbl">Total Cost</div></div>', unsafe_allow_html=True)
                    with t2: st.markdown(f'<div class="mbox"><div class="mval">${cpsq:,.0f}</div><div class="mlbl">Cost / SQ</div></div>', unsafe_allow_html=True)
                    with t3:
                        tcls = TIER_CLS.get(tier, "")
                        st.markdown(f'<div class="mbox"><div class="mval {tcls}">{tier}</div><div class="mlbl">Tier</div></div>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(render_table(rows, std_tsq), unsafe_allow_html=True)

            # ── CLIENT PRESENTATION ──────────────────────────────
            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            with st.expander("📋  Client Presentation View", expanded=False):
                tiers_with_prices = {}
                for tier in TIERS[product]:
                    if tier not in TIER_FEATURES:
                        continue
                    c = cost_large(std_tsq, std_pitch, product, tier, lc=low_lc)
                    cash_p = gp(c, pres_margin)
                    fin_p  = ru(cash_p * 1.07) if show_financing else None
                    tiers_with_prices[tier] = (cash_p, fin_p)
                cl = client or "—"
                st.markdown(render_cpo_presentation(cl, product, tiers_with_prices, financing=show_financing), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
#  TAB 2 — SMALL JOB (< 20 SQ)
# ══════════════════════════════════════════════════════
with tab_small:
    sl, sr = st.columns([1, 1.5], gap="large")

    with sl:
        st.markdown('<div class="lbl">Client</div>', unsafe_allow_html=True)
        s_client = st.text_input("Client", placeholder="Enter client name...", label_visibility="collapsed", key="sm_client")
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="note">Under 20 total adjusted SQ. HDZ product only.</div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Standard Slope (2/12 - 13/12)</div>', unsafe_allow_html=True)
        sc1, sc2, sc3 = st.columns(3)
        with sc1: s_sq    = st.number_input("Measured SQ", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="sm_sq")
        with sc2: s_fac   = st.number_input("Facets",      min_value=0,   value=0,   step=1,    key="sm_fac")
        with sc3: s_pitch = st.number_input("Pitch (/12)", min_value=2,   value=6,   step=1, max_value=13, key="sm_pit")
        s_std_tsq = waste_std(s_sq, s_fac) if s_sq > 0 else 0
        sc1.markdown(f'<div style="font-size:.72rem;color:#f47c20;margin-top:-10px;padding-left:2px;">Adj: <strong>{s_std_tsq} SQ</strong></div>' if s_sq > 0 else '<div style="font-size:.72rem;color:#3d4465;margin-top:-10px;padding-left:2px;">Adj: — SQ</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        s_add_low = st.checkbox("Add Low Slope Section", key="sm_addlow")
        s_low_tsq = 0; s_low_lc = 0
        if s_add_low:
            st.markdown('<div class="lbl">Low Slope Section</div>', unsafe_allow_html=True)
            slc1, slc2, slc3 = st.columns(3)
            with slc1: slsq    = st.number_input("Low SQ",     min_value=0.0, value=0.0, step=0.01, format="%.2f", key="sm_lsq")
            with slc2: slfac   = st.number_input("Low Facets", min_value=0,   value=0,   step=1,    key="sm_lfac")
            with slc3: slpitch = st.selectbox("Low Pitch",     [1, 2, 3],                           key="sm_lpit")
            if slsq > 0:
                s_low_tsq = waste_low(slsq, slfac, slpitch)
                slc1.markdown(f'<div style="font-size:.72rem;color:#f47c20;margin-top:-10px;padding-left:2px;">Adj: <strong>{s_low_tsq} SQ</strong></div>', unsafe_allow_html=True)
                s_low_lc  = low_cost_val(s_low_tsq, slpitch)

        s_total_tsq = s_std_tsq + s_low_tsq

        if s_sq > 0 and s_total_tsq >= 20:
            st.markdown('<div class="warn">Over 20 SQ - use the Full Roof tab instead.</div>', unsafe_allow_html=True)
        elif s_sq > 0:
            st.markdown(f'<div class="info">Total: {s_total_tsq} adj. SQ - qualifies as small job.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        s_use_cust = st.checkbox("Enable custom GPM", key="sm_cust")
        s_custom_gpm = None
        if s_use_cust:
            s_custom_gpm = st.slider("Custom GPM", min_value=0.01, max_value=0.99, value=0.32, step=0.01, format="%.0f%%", key="sm_gpm")
            st.markdown(TICKS, unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Deck Over GPM</div>', unsafe_allow_html=True)
        s_deck_gpm = st.slider("Deck GPM", min_value=0.01, max_value=0.99, value=0.33, step=0.01, format="%.0f%%", key="sm_deck_gpm")
        st.markdown(TICKS, unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Client Presentation Price</div>', unsafe_allow_html=True)
        sm_pres_opts = {"60% Margin": 0.60, "50% Margin": 0.50, "40% Margin": 0.40, "35% Margin": 0.35, "Custom GPM": None}
        sm_pres_label = st.selectbox("Presentation margin", list(sm_pres_opts.keys()), index=2, label_visibility="collapsed", key="sm_pres_margin")
        sm_pres_margin = sm_pres_opts[sm_pres_label]
        if sm_pres_margin is None:
            sm_pres_margin = s_custom_gpm if s_custom_gpm else 0.40
        sm_show_fin = st.checkbox("Show financing price on presentation", value=True, key="sm_show_fin")

        if s_std_tsq > 0:
            sh, sh_cost, sh_price = deck_info(s_total_tsq, s_deck_gpm)
            dm1, dm2, dm3 = st.columns(3)
            with dm1: st.markdown(f'<div class="mbox"><div class="mval">{s_total_tsq}</div><div class="mlbl">Adj. SQ</div></div>', unsafe_allow_html=True)
            with dm2: st.markdown(f'<div class="mbox"><div class="mval">{sh}</div><div class="mlbl">Deck Sheets</div></div>', unsafe_allow_html=True)
            with dm3: st.markdown(f'<div class="mbox"><div class="mval">${sh_price:,.0f}</div><div class="mlbl">Deck Price</div></div>', unsafe_allow_html=True)

    with sr:
        st.markdown('<div class="lbl">Pricing by Tier (HDZ)</div>', unsafe_allow_html=True)
        if s_sq == 0:
            st.markdown('<div class="card"><div class="empty"><div class="ei">📐</div><div class="et">Enter roof measurements to see pricing</div></div></div>', unsafe_allow_html=True)
        elif s_total_tsq >= 20:
            st.markdown('<div class="card"><div class="empty"><div class="ei">📐</div><div class="et">20+ SQ - switch to Full Roof tab</div></div></div>', unsafe_allow_html=True)
        else:
            scl = s_client or "—"
            st.markdown(f'<div class="chip">Client: <strong>{scl}</strong></div><div class="chip">HDZ</div><div class="chip">Pitch {s_pitch}/12</div><div class="chip">Total SQ: <strong>{s_total_tsq}</strong></div><br><br>', unsafe_allow_html=True)
            sm_tiers = ["Signature", "Gold", "Silver", "Bronze"]
            sm_tabs  = st.tabs(sm_tiers)
            for i, tier in enumerate(sm_tiers):
                with sm_tabs[i]:
                    base_cost = cost_small(s_total_tsq, tier)
                    if base_cost is None:
                        st.markdown('<div class="warn">Out of range for small job (must be 1-19 SQ).</div>', unsafe_allow_html=True)
                        continue
                    c = base_cost + s_low_lc
                    rows = price_rows(c, SMALL_GPMS, s_custom_gpm)
                    sm1, sm2 = st.columns(2)
                    with sm1: st.markdown(f'<div class="mbox"><div class="mval">${c:,.0f}</div><div class="mlbl">Total Cost</div></div>', unsafe_allow_html=True)
                    with sm2:
                        tcls = TIER_CLS.get(tier, "")
                        st.markdown(f'<div class="mbox"><div class="mval {tcls}">{tier}</div><div class="mlbl">Tier</div></div>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(render_table(rows, s_total_tsq, show_sq=False), unsafe_allow_html=True)

            # ── CLIENT PRESENTATION ──────────────────────────────
            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            with st.expander("📋  Client Presentation View", expanded=False):
                sm_tiers_prices = {}
                for tier in ["Signature", "Gold", "Silver", "Bronze"]:
                    base_cost = cost_small(s_total_tsq, tier)
                    if base_cost is None:
                        continue
                    c = base_cost + s_low_lc
                    cash_p = gp(c, sm_pres_margin)
                    fin_p  = ru(cash_p * 1.07) if sm_show_fin else None
                    sm_tiers_prices[tier] = (cash_p, fin_p)
                scl = s_client or "—"
                st.markdown(render_cpo_presentation(scl, "HDZ", sm_tiers_prices, financing=sm_show_fin), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
#  TAB 3 — REPAIR CALCULATOR
# ══════════════════════════════════════════════════════
with tab_repair:
    rl, rr = st.columns([1.1, 1], gap="large")

    with rl:
        st.markdown('<div class="lbl">Client</div>', unsafe_allow_html=True)
        r_client = st.text_input("Repair Client", placeholder="Enter client name...", label_visibility="collapsed", key="rep_client")
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Materials - Quantities Used</div>', unsafe_allow_html=True)
        qtys = {}
        cols = st.columns(2)
        for i, (name, price, unit) in enumerate(MATERIALS):
            with cols[i % 2]:
                qtys[name] = st.number_input(
                    f"{name}  (${price}/{unit})",
                    min_value=0.0, value=0.0, step=1.0, format="%.0f", key=f"rep_{i}"
                )
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Labor Tier</div>', unsafe_allow_html=True)
        labor_opts = [f"{l[0]}  -  ${l[1]:,}" for l in LABOR]
        labor_sel  = st.radio("Labor", labor_opts, label_visibility="collapsed")
        labor_idx  = labor_opts.index(labor_sel)
        labor_cost = LABOR[labor_idx][1]
        st.markdown(f'<div class="note">{LABOR[labor_idx][2]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        r_use_cust = st.checkbox("Enable custom GPM", key="rep_cust")
        r_custom_gpm = None
        if r_use_cust:
            r_custom_gpm = st.slider("Repair Custom GPM", min_value=0.01, max_value=0.99, value=0.60, step=0.01, format="%.0f%%", key="rep_gpm")
            st.markdown(TICKS, unsafe_allow_html=True)

    with rr:
        mat_cost   = sum(qtys[n] * p for n, p, _ in MATERIALS)
        total_cost = mat_cost + labor_cost
        used       = [(n, qtys[n], p, qtys[n]*p) for n, p, _ in MATERIALS if qtys[n] > 0]
        st.markdown('<div class="lbl">Summary</div>', unsafe_allow_html=True)
        rm1, rm2, rm3 = st.columns(3)
        with rm1: st.markdown(f'<div class="mbox"><div class="mval">${mat_cost:,.0f}</div><div class="mlbl">Materials</div></div>', unsafe_allow_html=True)
        with rm2: st.markdown(f'<div class="mbox"><div class="mval">${labor_cost:,.0f}</div><div class="mlbl">Labor</div></div>', unsafe_allow_html=True)
        with rm3: st.markdown(f'<div class="mbox"><div class="mval">${total_cost:,.0f}</div><div class="mlbl">Total Cost</div></div>', unsafe_allow_html=True)
        if used:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="lbl">Materials Used</div>', unsafe_allow_html=True)
            chips = "".join(f'<div class="chip"><strong>{n}</strong> x{int(q)} = ${t:,.0f}</div>' for n, q, p, t in used)
            st.markdown(f'<div style="margin-bottom:12px">{chips}</div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Pricing Breakdown</div>', unsafe_allow_html=True)
        if total_cost == 0:
            st.markdown('<div class="card"><div class="empty"><div class="ei">🔧</div><div class="et">Add materials and select labor to see pricing</div></div></div>', unsafe_allow_html=True)
        else:
            rows_html = ""
            if r_use_cust and r_custom_gpm:
                cp = gp(total_cost, r_custom_gpm)
                cf = ru(cp * 1.07)
                rows_html += f'<tr class="hlr"><td>Custom {int(r_custom_gpm*100)}% GPM</td><td>{int(r_custom_gpm*100)}%</td><td class="big">${cp:,.0f}</td></tr>'
                rows_html += f'<tr class="finr"><td>Custom GPM + Financing</td><td>—</td><td class="big">${cf:,.0f}</td></tr>'
                rows_html += '<tr><td colspan="3"><hr style="border-color:#2d3150;margin:2px 0;"></td></tr>'
            for m in [0.40, 0.45, 0.50, 0.55, 0.60]:
                p = gp(total_cost, m)
                rows_html += f'<tr><td>{int(m*100)}% GPM</td><td>{int(m*100)}%</td><td class="big">${p:,.0f}</td></tr>'
            fin60 = ru(gp(total_cost, 0.60) * 1.07)
            rows_html += f'<tr class="finr"><td>Financing (60% base)</td><td>—</td><td class="big">${fin60:,.0f}</td></tr>'
            rc = r_client or "—"
            st.markdown(f'''
            <div class="chip">Client: <strong>{rc}</strong></div>
            <div class="chip">Labor: <strong>{LABOR[labor_idx][0]}</strong></div>
            <div class="chip">Items: <strong>{len(used)}</strong></div><br><br>
            <div class="cardb">
              <table class="ptbl">
                <thead><tr><th>Level</th><th>GPM</th><th>Sale Price</th></tr></thead>
                <tbody>{rows_html}</tbody>
              </table>
            </div>
            ''', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
#  TAB 4 — CPO & RATE GUIDE
# ══════════════════════════════════════════════════════
with tab_cpo:
    st.markdown('<div class="lbl">GAF Timberline HDZ - CPO Tier Comparison</div>', unsafe_allow_html=True)
    rows_html = ""
    for feature, vals in CPO_DATA.items():
        s, b, si, g = vals
        rows_html += f"<tr><td><strong>{feature}</strong></td><td>{s}</td><td>{b}</td><td>{si}</td><td>{g}</td></tr>"
    st.markdown(f"""
    <div class="card">
      <table class="wtbl">
        <thead><tr><th>Feature</th><th class="tier-sig">Signature</th><th class="tier-brz">Bronze</th><th class="tier-sil">Silver</th><th class="tier-gld">Gold</th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbl">CPO Reference Pricing</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
      <table class="wtbl">
        <thead><tr><th>Payment</th><th class="tier-sig">Signature</th><th class="tier-brz">Bronze</th><th class="tier-sil">Silver</th><th class="tier-gld">Gold</th></tr></thead>
        <tbody>
          <tr><td><strong>Cash</strong></td><td>$23,700</td><td>$24,500</td><td>$25,500</td><td>$26,800</td></tr>
          <tr><td><strong>Finance</strong></td><td>$25,400</td><td>$26,200</td><td>$27,300</td><td>$28,700</td></tr>
        </tbody>
      </table>
      <p style="font-size:.75rem;color:#667799;margin-top:8px;">Static reference only. Use Full Roof tab for live calculations.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbl">Per-SQ Rate Reference (All Products)</div>', unsafe_allow_html=True)
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

# ══════════════════════════════════════════════════════
#  TAB 5 — HANDBOOK Q&A
# ══════════════════════════════════════════════════════
with tab_handbook:
    handbook_chunks = load_handbook()

    api_key = None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    # Session state init
    if "hb_messages" not in st.session_state:
        st.session_state.hb_messages = []
    if "hb_pending_q" not in st.session_state:
        st.session_state.hb_pending_q = ""

    st.markdown('<div class="lbl">Thunderbird Handbook Assistant</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="note">
        Ask any question about the handbook — sales process, SOPs, bidding, insurance, pay structure, warranties, and more.
        Every answer includes a reference to where it can be found.
    </div>
    """, unsafe_allow_html=True)

    if not handbook_chunks:
        st.markdown('<div class="warn">Handbook data not found. Make sure <strong>handbook_chunks.json</strong> is in your GitHub repo.</div>', unsafe_allow_html=True)
    elif not api_key:
        st.markdown('<div class="warn">API key not configured. Add <strong>GEMINI_API_KEY</strong> to your Streamlit secrets under Manage App → Settings → Secrets.</div>', unsafe_allow_html=True)
    else:
        detected_model = get_gemini_model(api_key)
        st.markdown(f'<div class="note">Using model: <strong>{detected_model}</strong></div>', unsafe_allow_html=True)
        hb_col, ref_col = st.columns([1.3, 1], gap="large")

        with hb_col:
            # ── SUGGESTED QUESTIONS ──────────────────────────────
            st.markdown('<div class="lbl">Suggested Questions — click to ask instantly</div>', unsafe_allow_html=True)
            suggestions = [
                "What are the T-Bird expectations for monthly sales?",
                "How does the pay commission structure work?",
                "What is the 5-step sales process?",
                "How do I handle an insurance claim appointment?",
                "What are the warranty differences between tiers?",
                "What is the no-show SOP?",
                "How do I calculate a full replacement bid?",
                "What are the repair labor rates?",
            ]
            s_cols = st.columns(2)
            for i, s in enumerate(suggestions):
                if s_cols[i % 2].button(s, key=f"sugg_{i}", use_container_width=True):
                    st.session_state.hb_pending_q = s

            # Auto-fire if suggestion was clicked
            if st.session_state.hb_pending_q:
                auto_q = st.session_state.hb_pending_q
                st.session_state.hb_pending_q = ""
                with st.spinner("Searching handbook..."):
                    answer, sources = ask_handbook(auto_q, handbook_chunks, api_key)
                st.session_state.hb_messages.append({"q": auto_q, "a": answer, "sources": sources})

            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

            # ── FREE TEXT INPUT ──────────────────────────────────
            st.markdown('<div class="lbl">Ask Your Own Question</div>', unsafe_allow_html=True)
            question = st.text_area(
                "Question",
                placeholder="e.g. What is the minimum GPM required for a self-generated lead?",
                label_visibility="collapsed",
                height=90,
                key="hb_question_input"
            )
            ask_col, clear_col = st.columns([3, 1])
            ask_btn   = ask_col.button("🔍  Ask the Handbook", use_container_width=True, type="primary")
            clear_btn = clear_col.button("Clear History", use_container_width=True)

            if clear_btn:
                st.session_state.hb_messages = []
                st.rerun()

            if ask_btn and question.strip():
                with st.spinner("Searching handbook..."):
                    answer, sources = ask_handbook(question.strip(), handbook_chunks, api_key)
                st.session_state.hb_messages.append({"q": question.strip(), "a": answer, "sources": sources})

            # ── ANSWERS ──────────────────────────────────────────
            if st.session_state.hb_messages:
                st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
                st.markdown('<div class="lbl">Answers</div>', unsafe_allow_html=True)
                for msg in reversed(st.session_state.hb_messages):
                    st.markdown(f"""
                    <div class="cardb" style="margin-bottom:14px;">
                      <div style="font-size:.72rem;color:#7788aa;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;">Question</div>
                      <div style="font-size:.92rem;color:#e0e8ff;margin-bottom:12px;font-style:italic;">"{msg['q']}"</div>
                      <div style="font-size:.72rem;color:#f47c20;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;">Answer</div>
                      <div style="font-size:.9rem;color:#d0d8e8;line-height:1.6;white-space:pre-wrap;">{msg['a']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        with ref_col:
            # ── CHAPTERS AS CLICKABLE BUTTONS ───────────────────
            st.markdown('<div class="lbl">Browse by Chapter — click to ask about it</div>', unsafe_allow_html=True)
            chapters = [
                ("Chapter 1", "The Fundamentals",        "Mission, values, expectations, pay chart, appointment types",  "Summarize Chapter 1: The Fundamentals"),
                ("Chapter 2", "5-Step Sales Success",    "Sales flow chart, financing 101, daily checklist",              "What is the 5-step sales process?"),
                ("Chapter 3", "Insurance 101",           "Claims workflow, overturn process, by-choice appointments",     "Explain the insurance claim workflow"),
                ("Chapter 4", "Full Replacement Bidding","Consumption chart, GPM magic, shingle costs, warranties",       "How do I calculate a full replacement bid?"),
                ("Chapter 5", "Repair Bidding",          "Repair quotes, labor rates, materials, workmanship warranties", "What are the repair labor rates and how do I bid a repair?"),
                ("Chapter 6", "Restoration Bidding",     "Restoration process and pricing",                               "How does restoration bidding work?"),
                ("Chapter 7", "SOPs",                    "Photo requirements, lead SOPs, payment terms, project submission","What are the key SOPs I need to know?"),
                ("Chapter 8", "Forms",                   "Chimney release, Xactimate, itel request forms",                "What forms are available and when do I use them?"),
                ("Chapter 9", "Sales Tools",             "Presentation folder, digital tools, quote attachments",         "What sales tools are available to me?"),
            ]
            for ch, title, desc, ch_query in chapters:
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"""
                <div class="card" style="margin-bottom:2px;padding:10px 14px;">
                  <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:2px;">
                    <span style="font-family:'Barlow Condensed',sans-serif;font-size:.65rem;font-weight:700;color:#f47c20;text-transform:uppercase;letter-spacing:.1em;">{ch}</span>
                    <span style="font-size:.85rem;font-weight:600;color:#e0e0e0;">{title}</span>
                  </div>
                  <div style="font-size:.72rem;color:#7788aa;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
                if c2.button("Ask", key=f"ch_{ch}", use_container_width=True):
                    st.session_state.hb_pending_q = ch_query
                    st.rerun()

            # ── PAGES REFERENCED ────────────────────────────────
            if st.session_state.hb_messages:
                st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
                st.markdown('<div class="lbl">Pages Referenced (Last Answer)</div>', unsafe_allow_html=True)
                last = st.session_state.hb_messages[-1]
                for src in last.get("sources", []):
                    st.markdown(f"""
                    <div class="card" style="margin-bottom:6px;padding:10px 14px;">
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span style="font-family:'Barlow Condensed',sans-serif;font-size:.72rem;font-weight:700;color:#f47c20;">PAGE {src['page']}</span>
                        <span style="font-size:.68rem;color:#7788aa;">{src['chapter']}</span>
                      </div>
                      <div style="font-size:.75rem;color:#8899aa;line-height:1.4;">{src['text'][:160].strip()}...</div>
                    </div>
                    """, unsafe_allow_html=True)
