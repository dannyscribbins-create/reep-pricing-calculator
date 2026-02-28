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

# ─── LOGIN GATE (Google OAuth) ──────────────────────────────────────
import urllib.parse
import urllib.request
import hashlib
import base64
import hmac

def get_google_auth_url():
    """Build Google OAuth authorization URL."""
    client_id  = st.secrets["google"]["client_id"]
    redirect   = st.secrets["google"]["redirect_uri"]
    state      = base64.urlsafe_b64encode(os.urandom(16)).decode()
    st.session_state.oauth_state = state
    params = {
        "client_id":     client_id,
        "redirect_uri":  redirect,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "online",
        "prompt":        "select_account",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

def exchange_code_for_email(code):
    """Exchange OAuth code for user email."""
    try:
        client_id     = st.secrets["google"]["client_id"]
        client_secret = st.secrets["google"]["client_secret"]
        redirect      = st.secrets["google"]["redirect_uri"]
        # Exchange code for token
        payload = urllib.parse.urlencode({
            "code":          code,
            "client_id":     client_id,
            "client_secret": client_secret,
            "redirect_uri":  redirect,
            "grant_type":    "authorization_code",
        }).encode()
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            tokens = json.loads(r.read())
        access_token = tokens.get("access_token")
        if not access_token:
            return None, "Token exchange failed"
        # Get user info
        req2 = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(req2, timeout=15) as r:
            userinfo = json.loads(r.read())
        return userinfo.get("email"), userinfo.get("name", "")
    except Exception as e:
        return None, str(e)

def is_allowed_email(email):
    """Check if email is in the approved list."""
    try:
        allowed = list(st.secrets["allowed_emails"].values())
        return email.lower() in [e.lower() for e in allowed]
    except Exception:
        return False

def show_login():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Barlow', sans-serif; background:#f5f0eb; color:#1e3158; }
    .stButton>button { background:#fff !important; border:1px solid #dde3ee !important; color:#1e3158 !important; font-weight:600 !important; }
    .stButton>button:hover { background:#f8f9ff !important; border-color:#b92227 !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin-top:80px;margin-bottom:28px;">
          <div style="font-family:'Barlow Condensed',sans-serif;font-size:2.4rem;font-weight:800;
                      color:#1e3158;text-transform:uppercase;letter-spacing:.04em;line-height:1;">
            THUNDERBIRD <span style="color:#b92227;">HUB</span>
          </div>
          <div style="font-size:.72rem;color:#888;text-transform:uppercase;letter-spacing:.12em;margin-top:4px;">
            Powered by Accent Roofing Service
          </div>
        </div>
        <div style="background:#fff;border:1px solid #dde3ee;border-radius:12px;padding:32px 28px;
                    box-shadow:0 4px 24px rgba(30,49,88,.08);text-align:center;">
          <div style="font-family:'Barlow Condensed',sans-serif;font-size:.72rem;font-weight:700;
                      letter-spacing:.14em;text-transform:uppercase;color:#b92227;margin-bottom:20px;">
            Team Sign In
          </div>
        """, unsafe_allow_html=True)

        auth_url = get_google_auth_url()
        st.markdown(f"""
        <a href="{auth_url}" target="_self" style="text-decoration:none;">
          <div style="display:flex;align-items:center;justify-content:center;gap:12px;
                      background:#fff;border:1px solid #dde3ee;border-radius:8px;padding:12px 20px;
                      cursor:pointer;transition:all .2s;font-size:.95rem;font-weight:600;color:#1e3158;">
            <svg width="20" height="20" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/><path fill="none" d="M0 0h48v48H0z"/></svg>
            Sign in with Google
          </div>
        </a>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:16px;font-size:.72rem;color:#aaa;">
          Only approved Thunderbird team emails can access this app.
        </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get("login_error"):
            st.markdown(f"""
            <div style="background:#fff5f5;border-left:3px solid #b92227;border-radius:0 6px 6px 0;
                        padding:8px 12px;font-size:.82rem;color:#b92227;margin-top:12px;">
              {st.session_state.login_error}
            </div>
            """, unsafe_allow_html=True)

# ── Session state init ───────────────────────────────────────────────
if "logged_in"    not in st.session_state: st.session_state.logged_in    = False
if "current_user" not in st.session_state: st.session_state.current_user = ""
if "login_error"  not in st.session_state: st.session_state.login_error  = ""
if "oauth_state"  not in st.session_state: st.session_state.oauth_state  = ""

# ── Handle OAuth callback ────────────────────────────────────────────
params = st.query_params
if "code" in params and not st.session_state.logged_in:
    code  = params["code"]
    state = params.get("state", "")
    email, name = exchange_code_for_email(code)
    st.query_params.clear()
    if email and is_allowed_email(email):
        st.session_state.logged_in    = True
        st.session_state.current_user = name or email
        st.session_state.current_email = email
        st.session_state.login_error  = ""
    else:
        st.session_state.login_error = f"Access denied. {email or 'That account'} is not on the approved team list. Contact your manager."

if not st.session_state.logged_in:
    show_login()
    st.stop()

# ─── END LOGIN GATE ─────────────────────────────────────────────────

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Barlow', sans-serif;
        background: #ecf0f3; 
        color: #1e3158;
    }
    
    .stApp {
        background-color: #ecf0f3;
    }
    
    .hdr { 
        background: linear-gradient(135deg, #1e3158 0%, #0d1a2f 100%);
        border-bottom: 4px solid #b92227;
        padding: 18px 32px 14px; 
        margin: -80px -80px 24px -80px;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    
    .hdr h1 { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #fff;
        letter-spacing: 0.04em;
        margin: 0 0 2px 0;
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
    }
    
    .lbl { 
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #b92227;
        margin-bottom: 5px;
    }
    
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
    
    .hr { 
        border: none;
        border-top: 1px solid #d0d5e0;
        margin: 14px 0;
    }
    
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
        padding: 10px 22px;
    }
    
    .stTabs [aria-selected="true"] { 
        background: #b92227 !important;
        color: #fff !important;
        border-radius: 6px 6px 0 0;
    }
    
    .stTabs [data-baseweb="tab-panel"] { 
        background: transparent;
        padding: 16px 0 0;
    }
    
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
    
    </style>
""", unsafe_allow_html=True)

col_logo, col_header = st.columns([0.8, 2.2], gap="small")
with col_logo:
    logo_path = os.path.join(os.path.dirname(__file__), "Copy_of_AccentRoofing-Logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=70)

with col_header:
    st.markdown("""
    <div style="padding-top: 8px;">
        <div style="font-family: 'Barlow Condensed', sans-serif; font-size: 28px; font-weight: 800; color: #1e3158; margin: 0; line-height: 1.1; letter-spacing: -0.5px;">
            THUNDERBIRD <span style="color: #b92227;">HUB</span>
        </div>
        <div style="color: #666; font-size: 11px; margin-top: 4px; letter-spacing: 0.5px; font-weight: 500;">
            Powered by Accent Roofing Service
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─── SIDEBAR LOGOUT ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="font-family:'Barlow Condensed',sans-serif;font-size:.7rem;font-weight:700;
                letter-spacing:.1em;text-transform:uppercase;color:#b92227;margin-bottom:4px;">
        Signed In
    </div>
    <div style="font-size:.88rem;color:#1e3158;font-weight:600;margin-bottom:2px;">
        {st.session_state.current_user}
    </div>
    <div style="font-size:.72rem;color:#888;margin-bottom:16px;">
        {st.session_state.get('current_email', '')}
    </div>
    """, unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.session_state.current_email = ""
        st.rerun()

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

TICKS = '<div style="display:flex;justify-content:space-between;margin:-10px 0 10px 0;padding:0 4px;"><div style="text-align:center"><div style="width:1px;height:6px;background:#d0d5e0;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#666">0%</span></div><div style="text-align:center"><div style="width:1px;height:6px;background:#b92227;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#b92227">25%</span></div><div style="text-align:center"><div style="width:1px;height:6px;background:#b92227;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#b92227">50%</span></div><div style="text-align:center"><div style="width:1px;height:6px;background:#b92227;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#b92227">75%</span></div><div style="text-align:center"><div style="width:1px;height:6px;background:#d0d5e0;margin:0 auto 2px"></div><span style="font-size:.65rem;color:#666">100%</span></div></div>'

CPO_DATA = {
    "Workmanship":    ["15 Year", "15 Year", "15 Year (10 backed by GAF)", "25 Year (25 backed by GAF)"],
    "Material/Labor": ["50 Year (Pro-rated)", "50 Year (Not Pro-rated)", "50 Year (Not Pro-rated)", "50 Year (Not Pro-rated)"],
    "Flashing":       ["R&R Step Flashing as needed", "R&R Step Flashing as needed", "R&R Step Flashing as needed", "Replace ALL step flashing"],
    "Sewer Pipe":     ["Standard", "Standard", "Standard", "Upgrade to Perma Boots"],
}

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

CPO_DISPLAY_ORDER = ["Signature", "Bronze", "Silver", "Gold"]

TIER_BADGE_COLORS = {
    "Signature": ("#b99f2a", "#1a1700"),
    "Bronze":    ("#8b5a3c", "#1a0f00"),
    "Silver":    ("#7a8fa3", "#111622"),
    "Gold":      ("#b92227", "#1a0f00"),
}

def render_cpo_presentation(client_name, product, tiers_with_prices, financing=True):
    """Render a client-facing CPO presentation card grid."""
    display_tiers = [t for t in CPO_DISPLAY_ORDER if t in tiers_with_prices]
    if not display_tiers:
        display_tiers = list(tiers_with_prices.keys())

    cards_html = ""
    for tier in display_tiers:
        cash_price, fin_price = tiers_with_prices[tier]
        pkg_name  = TIER_PACKAGE_NAMES.get(tier, tier)
        features  = TIER_FEATURES.get(tier, [])
        badge_fg, badge_bg = TIER_BADGE_COLORS.get(tier, ("#ffffff", "#1e3158"))

        feat_html = "".join(
            f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:7px;">'
            f'<span style="color:#2d5a1a;font-size:.85rem;margin-top:1px;flex-shrink:0;">✓</span>'
            f'<span style="font-size:.82rem;color:#2c3e50;line-height:1.3;">{f}</span>'
            f'</div>'
            for f in features
        )

        fin_html = (
            f'<div style="margin-top:10px;padding-top:10px;border-top:1px solid #d0d5e0;">'
            f'<div style="font-size:.65rem;color:#666;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px;">Finance Option</div>'
            f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.4rem;font-weight:700;color:#1e4d7b;">${fin_price:,.0f}</div>'
            f'</div>'
        ) if financing and fin_price else ""

        cards_html += f"""
        <div style="background:#fff;border:1px solid #d0d5e0;border-radius:10px;padding:20px;flex:1;min-width:160px;display:flex;flex-direction:column;box-shadow:0 2px 8px rgba(30,49,88,0.1);">
          <div style="background:{badge_bg};border:1px solid {badge_fg}44;border-radius:6px;padding:6px 10px;margin-bottom:14px;text-align:center;">
            <div style="font-family:'Barlow Condensed',sans-serif;font-size:.65rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{badge_fg};margin-bottom:1px;">{tier}</div>
            <div style="font-size:.75rem;color:{badge_fg}cc;">{pkg_name}</div>
          </div>
          <div style="margin-bottom:14px;">
            <div style="font-size:.62rem;color:#666;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px;">Cash Price</div>
            <div style="font-family:'Barlow Condensed',sans-serif;font-size:2rem;font-weight:800;color:#1e3158;line-height:1;">${cash_price:,.0f}</div>
          </div>
          <div style="flex:1;margin-bottom:4px;">{feat_html}</div>
          {fin_html}
        </div>"""

    client_line = f'<div style="font-size:.78rem;color:#666;margin-bottom:14px;letter-spacing:.04em;">Prepared for: <strong style="color:#1e3158;">{client_name}</strong> &nbsp;·&nbsp; {product}</div>' if client_name and client_name != "—" else f'<div style="font-size:.78rem;color:#666;margin-bottom:14px;">{product}</div>'

    return f"""
    <div style="background:#fff;border:1px solid #d0d5e0;border-radius:10px;padding:20px;">
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:.7rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#b92227;margin-bottom:6px;">Client Presentation</div>
      {client_line}
      <div style="display:flex;gap:12px;flex-wrap:wrap;">{cards_html}</div>
      <div style="margin-top:14px;font-size:.68rem;color:#666;text-align:center;">Prices include all labor, materials, and cleanup. Ask your representative about available financing options.</div>
    </div>"""

# ─── TABS ────────────────────────────────────────────────────────────
from tab6_installed_jobs import render_tab6

tab_large, tab_small, tab_repair, tab_cpo, tab_handbook, tab_jobs = st.tabs([
    "🏠  Full Roof (20 SQ+)",
    "📐  Small Job (< 20 SQ)",
    "🔧  Repair Calculator",
    "📋  CPO & Rate Guide",
    "📖  Handbook Q&A",
    "🏘️  Installed Jobs",
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
        c1.markdown(f'<div style="font-size:.72rem;color:#b92227;margin-top:-10px;padding-left:2px;">Adj: <strong>{std_tsq} SQ</strong></div>' if std_sq > 0 else '<div style="font-size:.72rem;color:#999;margin-top:-10px;padding-left:2px;">Adj: — SQ</div>', unsafe_allow_html=True)

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
                lc1.markdown(f'<div style="font-size:.72rem;color:#b92227;margin-top:-10px;padding-left:2px;">Adj: <strong>{low_tsq} SQ</strong></div>', unsafe_allow_html=True)
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
        sc1.markdown(f'<div style="font-size:.72rem;color:#b92227;margin-top:-10px;padding-left:2px;">Adj: <strong>{s_std_tsq} SQ</strong></div>' if s_sq > 0 else '<div style="font-size:.72rem;color:#999;margin-top:-10px;padding-left:2px;">Adj: — SQ</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        s_add_low = st.checkbox("Add Low Slope Section", key="sm_addlow")
        s_low_tsq = 0; s_low_lc = 0
        if s_add_low:
            st.markdown('<div class="lbl">Low Slope Section</div>', unsafe_allow_html=True)
            slc1, slc2, slc3 = st.columns(3)
            with slc1: slsq    = st.number_input("Low Measured SQ", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="sm_lsq")
            with slc2: slfac   = st.number_input("Low Facets",      min_value=0,   value=0,   step=1,    key="sm_lfac")
            with slc3: slpitch = st.selectbox("Low Pitch", [1, 2, 3], key="sm_lpit")
            if slsq > 0:
                s_low_tsq = waste_low(slsq, slfac, slpitch)
                slc1.markdown(f'<div style="font-size:.72rem;color:#b92227;margin-top:-10px;padding-left:2px;">Adj: <strong>{s_low_tsq} SQ</strong></div>', unsafe_allow_html=True)
                s_low_lc  = low_cost_val(s_low_tsq, slpitch)

        s_total_tsq = s_std_tsq + s_low_tsq

        if s_sq > 0 and s_total_tsq >= 20:
            st.markdown('<div class="warn">20+ SQ - switch to Full Roof tab instead.</div>', unsafe_allow_html=True)
        elif s_sq > 0:
            st.markdown(f'<div class="info">Total: {s_total_tsq} adj. SQ - qualifies as small job.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">GPM Tier</div>', unsafe_allow_html=True)
        sm_use_cust = st.checkbox("Enable custom GPM", key="sm_cust")
        s_custom_gpm = None
        if sm_use_cust:
            s_custom_gpm = st.slider("Custom GPM", min_value=0.01, max_value=0.99, value=0.50, step=0.01, format="%.0f%%", key="sm_gpm")
            st.markdown(TICKS, unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="lbl">Client Presentation Price</div>', unsafe_allow_html=True)
        sm_pres_margin_opts = {"60% Margin": 0.60, "50% Margin": 0.50, "40% Margin": 0.40, "Custom GPM": None}
        sm_pres_margin_label = st.selectbox("Presentation margin", list(sm_pres_margin_opts.keys()), index=2, label_visibility="collapsed", key="sm_pres_margin")
        sm_pres_margin = sm_pres_margin_opts[sm_pres_margin_label]
        if sm_pres_margin is None:
            sm_pres_margin = s_custom_gpm if s_custom_gpm else 0.40
        sm_show_fin = st.checkbox("Show financing price on presentation", value=True, key="sm_show_fin")

    with sr:
        st.markdown('<div class="lbl">Pricing by Tier</div>', unsafe_allow_html=True)
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
                rows_html += '<tr><td colspan="3"><hr style="border-color:#d0d5e0;margin:2px 0;"></td></tr>'
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
      <p style="font-size:.75rem;color:#666;margin-top:8px;">Static reference only. Use Full Roof tab for live calculations.</p>
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

# ══════════════════════════════════════════════════════
#  TAB 6 — INSTALLED JOBS CATALOGUE
# ══════════════════════════════════════════════════════
with tab_jobs:
    render_tab6()
