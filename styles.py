import base64
import os
import streamlit as st
import streamlit.components.v1 as components

_LOGO_PATH    = os.path.join(os.path.dirname(__file__), "Air.png")
_ACC_SVG_PATH = os.path.join(os.path.dirname(__file__), "Accenture-logo.svg")


@st.cache_data
def _logo_base64() -> str:
    """Return the Air.png encoded as a base64 data URI."""
    with open(_LOGO_PATH, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"


@st.cache_data
def _acc_logo_base64() -> str:
    """Return the Accenture-logo.svg encoded as a base64 data URI."""
    with open(_ACC_SVG_PATH, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/svg+xml;base64,{data}"


def inject_styles():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">

    <style>
    /* ═══════════════════════════════════════════════════
       RESET & CSS VARIABLES
    ═══════════════════════════════════════════════════ */
    * { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
        /* ── Sidebar width (JS updates this to actual rendered value) ── */
        --sidebar-w: 260px;

        /* ── Colours ── */
        --bg:           #F4F6F9;
        --card-bg:      #FFFFFF;
        --sidebar-bg:   #FFFFFF;
        --foreground:   #111827;
        --muted-text:   #6B7280;
        --border:       #E5E7EB;
        --muted:        #F9FAFB;
        --accent:       #A100FF;
        --accent-light: #F3E8FF;
        --navy:         #002F5C;
        --critical:     #DC2626;
        --critical-bg:  #FEF2F2;
        --high:         #EA580C;
        --high-bg:      #FFF7ED;
        --medium:       #B45309;
        --medium-bg:    #FFFBEB;
        --low:          #16A34A;
        --low-bg:       #F0FDF4;
        --resolved:     #2563EB;
        --resolved-bg:  #EFF6FF;
        --shadow-sm:    0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md:    0 4px 12px rgba(0,0,0,0.08);
        --radius:       10px;
        --radius-sm:    6px;

        /* ── Type scale (scaled down ~10% for compact 13" display) ── */
        --font-sans:    'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        --font-mono:    'SF Mono', 'Fira Mono', 'Consolas', monospace;

        --text-xs:      0.625rem;   /* 10px — labels / badges    weight 500 */
        --text-sm:      0.6875rem;  /* 11px — captions / meta    weight 400 */
        --text-base:    0.75rem;    /* 12px — body               weight 400 */
        --text-card:    0.875rem;   /* 14px — card titles        weight 600 */
        --text-section: 1.0rem;     /* 16px — section headings   weight 600 */
        --text-page:    1.25rem;    /* 20px — page headings      weight 700 */
    }

    /* ── Base typography ────────────────────────────────────────────────────
       font-family and line-height apply to div too (structural, always wanted).
       font-size / font-weight / color are NOT forced on bare div — a stylesheet
       !important on div would silently beat any inline style="font-size:X" on
       custom HTML elements. Divs still inherit 13px/400 from body via the rule
       below, but that inherited value has no !important so inline styles win. */
    html, body, [class*="css"],
    .stApp, p, li, span, div, label,
    input, textarea, select, button {
        font-family: var(--font-sans) !important;
        line-height:  1.6 !important;
    }
    html, body, [class*="css"],
    .stApp, p, li, span, label,
    input, textarea, select, button {
        font-size:   var(--text-base) !important;
        font-weight: 400 !important;
        color:       var(--foreground) !important;
    }

    .stApp { background: var(--bg) !important; }

    /* ── Captions / meta — 14px ── */
    .stCaption, small,
    [data-testid="stCaptionContainer"],
    .notif-meta, .page-subtitle,
    .ir-navbar-wordmark-sub,
    .ir-navbar-market,
    .section-label,
    .market-stat,
    .incident-row-meta,
    .ai-stat-label,
    .metric-card-label {
        font-size: var(--text-sm) !important;
        font-weight: 300 !important;
        color: var(--muted-text) !important;
    }

    /* ── Labels / badges — 12px weight 500 ── */
    .badge,
    .ai-card-label,
    .ir-navbar-wordmark-sub,
    .nav-menu-label,
    [data-testid="stSidebar"] .nav-menu-label {
        font-size: var(--text-xs) !important;
        font-weight: 500 !important;
    }

    /* ── Body text explicit — 16px weight 400 ── */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    .notif-desc, .ai-reasoning, .ir-card {
        font-size: var(--text-base) !important;
        font-weight: 400 !important;
        color: var(--foreground) !important;
    }

    /* ── Card titles — 20px weight 600 ── */
    .notif-title,
    .market-card-name,
    .ai-stat-value,
    .metric-card-value {
        font-size: var(--text-card) !important;
        font-weight: 600 !important;
        color: var(--foreground) !important;
    }

    /* ── Section headings — semi-bold, slight tracking ── */
    h2, h3 {
        font-size:      var(--text-section) !important;
        font-weight:    600 !important;
        letter-spacing: -0.01em !important;
    }

    /* ── Page headings — bold, tighter tracking for large Poppins ── */
    .page-title, h1 {
        font-size:      var(--text-page) !important;
        font-weight:    700 !important;
        letter-spacing: -0.02em !important;
        color:          var(--foreground) !important;
    }

    /* ── Monospace ── */
    code, pre, .incident-row-id {
        font-family: var(--font-mono) !important;
        font-size: var(--text-sm) !important;
        background: #F3F4F6 !important;
        color: #374151 !important;
        border-radius: 4px !important;
    }

    /* Dropdown / selectbox — white on menu & popover only; NOT on every select child div
       (the old "[data-baseweb='select'] div" blanket rule painted internal wrappers white,
       creating a white overlay that covered the left edge of the first multiselect chip). */
    [data-baseweb="menu"], [data-baseweb="menu"] li,
    [data-baseweb="popover"] {
        background: #FFFFFF !important;
        color: var(--foreground) !important;
        font-size: var(--text-base) !important;
    }
    /* Keep the outer control surface white */
    [data-baseweb="select"] > div {
        background: #FFFFFF !important;
    }
    /* Internal wrappers must be transparent so chips show through */
    .stMultiSelect [data-baseweb="input"],
    .stMultiSelect [data-baseweb="base-input"],
    .stMultiSelect [data-baseweb="base-input"] > div {
        background: transparent !important;
    }
    [data-baseweb="option"]:hover { background: #F3E8FF !important; }

    /* ── Multiselect chips — white background with purple border ──────────────
       Root cause notes:
         • [data-baseweb="tag"] is a <span>, so the broad "select div" rule above
           never applies to it — Streamlit's own CSS keeps it purple.
         • First-chip clip: [data-baseweb="base-input"] defaults to overflow:hidden
           with no left padding, cutting off the leading edge of the first chip. */

    /* 1. Chip appearance */
    [data-baseweb="tag"] {
        background:    #FFFFFF !important;
        border:        1px solid var(--accent) !important;
        border-radius: 4px !important;
        margin:        2px 3px !important;
        padding:       2px 4px 2px 7px !important;
        height:        auto !important;
    }
    /* Inner span/div of chip — keep transparent so white shows through */
    [data-baseweb="tag"] span,
    [data-baseweb="tag"] div {
        background:  transparent !important;
        color:       var(--foreground) !important;
        font-size:   var(--text-sm) !important;
        font-weight: 500 !important;
    }
    /* Close (×) button inside chip */
    [data-baseweb="tag"] [role="button"],
    [data-baseweb="tag"] button {
        background: transparent !important;
        color:      var(--accent) !important;
    }
    [data-baseweb="tag"] [role="button"]:hover,
    [data-baseweb="tag"] button:hover {
        background: var(--accent-light) !important;
        color:      var(--accent) !important;
        border-radius: 50% !important;
    }

    /* 2. Fix first-chip clip — every level in the BaseWeb chain must be visible.
          BaseWeb nests: ControlContainer → [data-baseweb="input"] → [data-baseweb="base-input"]
          The middle layer ([data-baseweb="input"]) defaults to overflow:hidden and was
          not targeted previously, causing the first chip to be clipped in app.py. */
    .stMultiSelect [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="input"] {
        overflow: visible !important;
    }
    .stMultiSelect [data-baseweb="base-input"] {
        overflow:    visible !important;
        padding:     3px 6px 3px 4px !important;
        flex-wrap:   wrap !important;
        min-height:  36px !important;
        align-items: center !important;
        gap:         2px !important;
    }
    /* The hidden typing input inside multiselect — transparent, no overflow issue */
    .stMultiSelect [data-baseweb="base-input"] input {
        background: transparent !important;
        min-width:  50px !important;
    }

    /* Radio & checkbox */
    .stRadio > div label, .stCheckbox > label {
        font-size: var(--text-base) !important;
        font-weight: 400 !important;
        color: var(--foreground) !important;
    }


    /* Native metric widget — large bold value, light label */
    [data-testid="stMetricValue"] {
        font-size:      var(--text-section) !important;
        font-weight:    700 !important;
        letter-spacing: -0.01em !important;
        color:          var(--foreground) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size:   var(--text-sm) !important;
        font-weight: 300 !important;
        color:       var(--muted-text) !important;
    }

    /* Tabs (if used) */
    [data-baseweb="tab-list"] { background: #F4F6F9 !important; }
    [data-baseweb="tab"]      { color: #6B7280 !important; font-weight: 700 !important; font-family: var(--font-sans) !important; }
    [aria-selected="true"][data-baseweb="tab"] { color: #A100FF !important; font-weight: 700 !important; }

    /* Toast / notification popup */
    [data-testid="stNotification"] {
        background: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #E5E7EB !important;
    }

    /* ═══════════════════════════════════════════════════
       HIDE STREAMLIT CHROME
    ═══════════════════════════════════════════════════ */
    #MainMenu { display: none !important; }
    footer    { display: none !important; }
    header    { display: none !important; height: 0 !important; min-height: 0 !important; }
    [data-testid="stHeader"]               { display: none !important; height: 0 !important; min-height: 0 !important; }
    [data-testid="InputInstructions"] { display: none !important; }
    .stDeployButton                         { display: none !important; }
    [data-testid="stToolbar"]               { display: none !important; }
    [data-testid="stDecoration"]            { display: none !important; }
    [data-testid="stStatusWidget"]          { display: none !important; }

    /* Hide sidebar collapse/toggle arrow — sidebar always visible */
    [data-testid="collapsedControl"]        { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    button[kind="header"]                   { display: none !important; }
    .st-emotion-cache-1dp5vir              { display: none !important; }

    /* Lock sidebar — always expanded, no hover effect on toggle */
    [data-testid="stSidebar"][aria-expanded="false"] {
        display: block !important;
        transform: none !important;
        min-width: 245px !important;
    }

    /* ═══════════════════════════════════════════════════
       TOP NAVBAR
    ═══════════════════════════════════════════════════ */
    .ir-navbar {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 9999;
        height: 62px;
        background: #FFFFFF;
        border-bottom: 1px solid var(--border);
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
        display: flex;
        align-items: center;
        padding: 0 36px;
        gap: 18px;
        /* Always full width — overrides Streamlit's sidebar offset */
        margin-left: 0 !important;
        width: 100vw !important;
    }
    /* Brand section: SVG logo + wordmark */
    .ir-navbar-brand {
        display: flex; align-items: center; gap: 10px; flex-shrink: 0;
    }
    .ir-navbar-acc-logo {
        height: 34px; width: auto;
        object-fit: contain; display: block;
        flex-shrink: 0;
    }
    /* Air platform logo */
    .ir-navbar-air-logo {
        height: 34px; width: auto;
        object-fit: contain; display: block;
        flex-shrink: 0;
    }
    .ir-navbar-wordmark { display: flex; flex-direction: column; line-height: 1.15; }
    .ir-navbar-wordmark-main {
        font-size: 14px; font-weight: 700; color: #111827; letter-spacing: 0;
    }
    .ir-navbar-wordmark-sub {
        font-size: 9px; font-weight: 500; color: var(--muted-text);
        letter-spacing: 0.06em; text-transform: uppercase;
    }
    .ir-navbar-divider {
        width: 1px; height: 30px; background: var(--border); flex-shrink: 0;
    }
    .ir-navbar-appname {
        font-size: 13px; font-weight: 600; color: var(--foreground); letter-spacing: 0;
    }
    .ir-navbar-spacer { flex: 1; }
    .ir-navbar-user {
        display: flex; align-items: center; gap: 7px;
        background: var(--muted); border: 1px solid var(--border);
        border-radius: 999px; padding: 4px 13px 4px 5px;
        flex-shrink: 0;
    }
    .ir-navbar-avatar {
        width: 28px; height: 28px; border-radius: 50%;
        background: linear-gradient(135deg, var(--accent), var(--navy));
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 700; color: #fff; flex-shrink: 0;
        line-height: 1;
    }
    .ir-navbar-username {
        font-size: 12px !important; font-weight: 600 !important;
        color: var(--foreground) !important; white-space: nowrap;
    }
    .ir-navbar-refresh {
        width: 30px; height: 30px; border-radius: 50%;
        border: 1.5px solid var(--border); background: transparent;
        cursor: pointer; display: flex; align-items: center;
        justify-content: center; flex-shrink: 0; padding: 0; outline: none;
        transition: background 0.18s, border-color 0.18s, box-shadow 0.18s;
    }
    .ir-navbar-refresh:hover {
        background: #EDE9FE; border-color: var(--accent);
        box-shadow: 0 0 0 4px rgba(161,0,255,0.09);
    }

    /* ── Sidebar: fixed below navbar, never scrolls ── */
    [data-testid="stSidebar"] {
        position:     fixed !important;
        top:          62px !important;
        height:       calc(100vh - 62px) !important;
        width:        260px !important;
        min-width:    260px !important;
        max-width:    260px !important;
        background:   var(--sidebar-bg) !important;
        border-right: 1px solid var(--border) !important;
        z-index:      999 !important;
        overflow:     hidden !important;
        padding-top:  0 !important;
    }
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        height:   100% !important;
        overflow: hidden !important;
    }

    /* ── Sidebar stVerticalBlock: flex column base — JS assigns nav/footer roles ── */
    /* First/last-child flex rules intentionally omitted here: JS applies them only
       when there are exactly 2 container children (TL portal nav + footer), avoiding
       the reviewer sidebar (7+ children) being incorrectly styled.              */
    [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"],
    [data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {
        display:        flex !important;
        flex-direction: column !important;
        height:         100% !important;
        overflow:       hidden !important;
        gap:            0 !important;
    }
    /* Divider above Switch Market button */
    .ir-sidebar-divider {
        border:     none !important;
        border-top: 1px solid var(--border) !important;
        margin:     20px 8px 6px !important;
    }
    /* Main content area — push below navbar and right of fixed sidebar */
    section[data-testid="stMain"] {
        padding-top: 0 !important;
        margin-top:  0 !important;
        margin-left: var(--sidebar-w) !important;
        width:       calc(100vw - var(--sidebar-w)) !important;
        max-width:   calc(100vw - var(--sidebar-w)) !important;
        overflow-x:  hidden !important;
    }
    [data-testid="stMainBlockContainer"],
    .block-container {
        padding-top:   64px !important;
        padding-left:  2rem !important;
        padding-right: 2rem !important;
        max-width:     100% !important;
    }
    /* Zero out any Streamlit-internal top margin on the first rendered element */
    [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="element-container"]:first-child {
        margin-top:  0 !important;
        padding-top: 0 !important;
    }

    /* Kill ALL top spacing inside sidebar — every level (must come AFTER .block-container rule) */
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] * > *               { margin-top: 0 !important; padding-top: 0 !important; }
    /* Zero wrapper bottom padding so no phantom white space appears below custom HTML (status badge, labels) */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="element-container"] { padding-bottom: 0 !important; margin-bottom: 0 !important; }
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] > div > div,
    [data-testid="stSidebar"] > div > div > div,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebar"] section,
    [data-testid="stSidebar"] section > div  { padding-top: 0 !important; margin-top: 0 !important; }
    [data-testid="stSidebar"] .block-container,
    [data-testid="stSidebar"] [data-testid="stMainBlockContainer"] {
        padding-top:    0 !important;
        padding-bottom: 0 !important;
        margin-top:     0 !important;
    }
    /* Small controlled top padding for nav content only */
    [data-testid="stSidebarUserContent"]          { padding-top: 4px !important; }

    /* Login page bottom footer */
    .ir-login-footer {
        position: fixed;
        bottom: 0; left: 0; right: 0;
        z-index: 100;
        text-align: center;
        padding: 14px 0;
        font-size: 12px;
        color: var(--muted-text);
        font-family: 'Poppins', sans-serif;
        letter-spacing: 0.04em;
        background: var(--bg);
        border-top: 1px solid var(--border);
    }

    /* ═══════════════════════════════════════════════════
       SIDEBAR LAYOUT — nav section, spacer, bottom
    ═══════════════════════════════════════════════════ */
    .ir-nav-section { padding: 8px 8px 4px; }
    .ir-nav-label {
        font-size: 0.6rem !important;
        font-weight: 700 !important;
        color: var(--foreground) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        padding: 4px 6px 10px !important;
    }

    /* ═══════════════════════════════════════════════════
       SIDEBAR NAV BUTTONS
    ═══════════════════════════════════════════════════ */
    [data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        border: none !important;
        color: var(--foreground) !important;
        font-family: var(--font-sans) !important;
        font-size: var(--text-sm) !important;
        font-weight: 700 !important;
        text-align: left !important;
        padding: 10px 14px !important;
        border-radius: var(--radius-sm) !important;
        transition: background 0.15s, color 0.15s !important;
        width: 100% !important;
        box-shadow: none !important;
        line-height: 1.4 !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: var(--accent-light) !important;
        color: var(--accent) !important;
        font-weight: 700 !important;
    }

    /* Field error label — class beats base div rule */
    .ir-field-error,
    .ir-field-error span { color: #DC2626 !important; }

    /* Bordered container — incident table row cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        background: var(--card-bg) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,.05) !important;
        padding: 6px 14px !important;
        margin-bottom: 6px !important;
        transition: box-shadow .15s !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 3px 10px rgba(0,0,0,.09) !important;
    }

    /* ── Column header labels (plain, non-filterable) ── */
    .ir-col-header {
        font-size: 10px !important;
        font-weight: 700 !important;
        color: #374151 !important;
        text-transform: uppercase !important;
        letter-spacing: .08em !important;
        padding: 8px 4px 6px !important;
        white-space: nowrap !important;
    }

    /* ── Filterable column header selectboxes — label styled as column header ── */
    .stSelectbox [data-testid="stWidgetLabel"] p,
    .stSelectbox [data-testid="stWidgetLabel"] {
        font-size: 10px !important;
        font-weight: 700 !important;
        color: #374151 !important;
        text-transform: uppercase !important;
        letter-spacing: .08em !important;
        margin-bottom: 2px !important;
    }

    /* Restore normal label styling inside forms (Create Incident etc.) */
    [data-testid="stForm"] .stSelectbox [data-testid="stWidgetLabel"] p,
    [data-testid="stForm"] .stSelectbox [data-testid="stWidgetLabel"] {
        font-size: var(--text-sm) !important;
        font-weight: 400 !important;
        color: var(--foreground) !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        margin-bottom: 4px !important;
    }

    /* ═══════════════════════════════════════════════════
       PAGE HEADER — 32px/700 title, 14px/400 subtitle
    ═══════════════════════════════════════════════════ */
    .page-header {
        margin-bottom: 28px;
        padding-bottom: 20px;
        border-bottom: 1px solid var(--border);
    }
    .page-title {
        font-size: var(--text-page) !important;
        font-weight: 700 !important;
        color: var(--foreground) !important;
        margin: 0 0 6px !important;
        letter-spacing: -0.5px !important;
        line-height: 1.15 !important;
    }
    .page-subtitle {
        font-size: var(--text-sm) !important;
        color: var(--muted-text) !important;
        font-weight: 400 !important;
        margin: 0 0 18px 0 !important;
        line-height: 1.5 !important;
    }

    /* ═══════════════════════════════════════════════════
       METRIC CARDS — value 20px/600, label 12px/500
    ═══════════════════════════════════════════════════ */
    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px 22px;
        box-shadow: var(--shadow-sm);
        border-left: 4px solid var(--border);
        transition: box-shadow 0.2s;
        animation: _irFadeInUp 320ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
    }
    .metric-card:hover    { box-shadow: var(--shadow-md); }
    .metric-card.primary  { border-left-color: var(--accent); }
    .metric-card.high     { border-left-color: var(--high); }
    .metric-card.critical { border-left-color: var(--critical); }
    .metric-card.resolved { border-left-color: var(--resolved); }
    .metric-card-value {
        font-size: var(--text-card) !important;
        font-weight: 600 !important;
        color: var(--foreground) !important;
        line-height: 1.2 !important;
        margin-bottom: 4px !important;
    }
    .metric-card-label {
        font-size: var(--text-xs) !important;
        color: var(--muted-text) !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
    }

    /* ═══════════════════════════════════════════════════
       GENERAL IR CARD — body 16px/400
    ═══════════════════════════════════════════════════ */
    .ir-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px 22px;
        margin-bottom: 16px;
        box-shadow: var(--shadow-sm);
        font-size: var(--text-base) !important;
    }

    /* ═══════════════════════════════════════════════════
       AI CARD — label 12px/500, values 16px/700
    ═══════════════════════════════════════════════════ */
    .ai-card {
        background: #FAFBFF;
        border: 1px solid #E0E7FF;
        border-radius: var(--radius);
        padding: 18px 22px;
        margin: 16px 0;
    }
    .ai-card-label {
        font-size: var(--text-xs) !important;
        font-weight: 700 !important;
        color: var(--accent) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin-bottom: 14px !important;
    }
    .ai-stat-row { display: flex; gap: 28px; margin-bottom: 14px; flex-wrap: wrap; }
    .ai-stat { display: flex; flex-direction: column; gap: 5px; }
    .ai-stat-label {
        font-size: var(--text-xs) !important;
        font-weight: 500 !important;
        color: var(--muted-text) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    .ai-stat-value {
        font-size: var(--text-base) !important;
        font-weight: 700 !important;
        color: var(--foreground) !important;
    }
    .ai-reasoning {
        font-size: var(--text-sm) !important;
        color: var(--muted-text) !important;
        background: var(--muted) !important;
        border-radius: var(--radius-sm) !important;
        padding: 10px 14px !important;
        line-height: 1.6 !important;
        border-left: 3px solid var(--accent) !important;
    }

    /* ═══════════════════════════════════════════════════
       BADGES
    ═══════════════════════════════════════════════════ */
    .badge {
        display: inline-flex; align-items: center;
        padding: 3px 9px; border-radius: 999px;
        font-size: 11px; font-weight: 600;
        letter-spacing: 0.02em; white-space: nowrap;
    }
    .badge-critical  { background: var(--critical-bg); color: var(--critical); }
    .badge-high      { background: var(--high-bg);     color: var(--high); }
    .badge-medium    { background: var(--medium-bg);   color: var(--medium); }
    .badge-low       { background: var(--low-bg);      color: var(--low); }
    .badge-unknown   { background: #F3F4F6;             color: #6B7280; }
    .badge-resolved  { background: var(--resolved-bg); color: var(--resolved); }
    .badge-open      { background: var(--high-bg);     color: var(--high); }
    .badge-new       { background: var(--accent-light);color: var(--accent); }
    .badge-read      { background: #F3F4F6;             color: #6B7280; }
    .badge-unread    { background: var(--critical-bg); color: var(--critical); }
    .badge-responded { background: var(--low-bg);      color: var(--low); }

    /* ═══════════════════════════════════════════════════
       NOTIFICATION CARDS
    ═══════════════════════════════════════════════════ */
    .notif-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-left: 4px solid var(--critical);
        border-radius: var(--radius);
        padding: 18px 20px 14px;
        margin-bottom: 12px;
        box-shadow: var(--shadow-sm);
        animation: slideIn 0.25s ease both;
        transition: box-shadow 0.2s;
    }
    .notif-card:hover    { box-shadow: var(--shadow-md); }
    .notif-card.read     { border-left-color: var(--border); opacity: 0.8; }
    .notif-card.critical { border-left-color: var(--critical); }
    .notif-card.high     { border-left-color: var(--high); }
    .notif-card.medium   { border-left-color: #D97706; }
    .notif-card.low      { border-left-color: var(--low); }
    .notif-card.unknown  { border-left-color: var(--border); }
    .notif-title {
        font-size: var(--text-base) !important;
        font-weight: 600 !important;
        color: var(--foreground) !important;
        line-height: 1.4 !important;
    }
    .notif-meta {
        display: flex; gap: 14px; margin-top: 8px; flex-wrap: wrap;
        font-size: var(--text-xs) !important;
        color: var(--muted-text) !important;
        font-weight: 500 !important;
    }
    .notif-desc {
        margin-top: 10px;
        font-size: var(--text-sm) !important;
        color: #374151 !important;
        line-height: 1.6 !important;
        background: var(--muted);
        border-radius: var(--radius-sm);
        padding: 10px 13px;
    }

    /* ═══════════════════════════════════════════════════
       INCIDENT ROW
    ═══════════════════════════════════════════════════ */
    .incident-row {
        display: flex; align-items: center; gap: 14px;
        background: var(--card-bg); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 13px 18px; margin-bottom: 8px;
        box-shadow: var(--shadow-sm); animation: slideIn 0.2s ease both;
        transition: box-shadow 0.15s; flex-wrap: wrap;
    }
    .incident-row:hover { box-shadow: var(--shadow-md); }
    .incident-row-id {
        font-size: 0.72rem; font-weight: 700; color: var(--muted-text);
        letter-spacing: 0.05em; background: var(--muted);
        border: 1px solid var(--border); border-radius: 4px;
        padding: 2px 8px; flex-shrink: 0;
        font-family: 'SF Mono', 'Fira Mono', monospace;
    }
    .incident-row-title {
        font-size: var(--text-sm) !important;
        font-weight: 600 !important;
        color: var(--foreground) !important;
        flex: 1; min-width: 180px;
    }
    .incident-row-meta {
        display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        font-size: var(--text-xs) !important;
        color: var(--muted-text) !important;
        font-weight: 500 !important;
    }

    /* ═══════════════════════════════════════════════════
       MARKET CARDS
    ═══════════════════════════════════════════════════ */
    .market-card {
        background: var(--card-bg); border: 1px solid var(--border);
        border-radius: var(--radius); padding: 16px 18px; box-shadow: var(--shadow-sm);
    }
    .market-card-name {
        font-size: var(--text-sm) !important;
        font-weight: 700 !important;
        color: var(--foreground) !important;
        margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border);
    }
    .market-stat {
        display: flex; justify-content: space-between; align-items: center;
        font-size: var(--text-xs) !important;
        color: var(--muted-text) !important;
        padding: 4px 0; font-weight: 500 !important;
    }
    .market-stat-value {
        font-size: var(--text-sm) !important;
        font-weight: 700 !important;
        color: var(--foreground) !important;
    }

    /* ═══════════════════════════════════════════════════
       DIVIDER & LABELS
    ═══════════════════════════════════════════════════ */
    .ir-divider {
        border: none; border-top: 1px solid var(--border); margin: 20px 0;
    }
    .section-label {
        font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.08em; color: var(--muted-text); margin-bottom: 14px;
    }
    .response-line {
        font-size: 0.82rem; color: var(--muted-text); padding: 3px 0; font-weight: 500;
    }

    /* ═══════════════════════════════════════════════════
       STREAMLIT COMPONENT OVERRIDES
    ═══════════════════════════════════════════════════ */

    /* Primary button — matches secondary/back button style */
    .stButton > button[kind="primary"] {
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        color: var(--foreground) !important;
        font-family: var(--font-sans) !important;
        font-size: var(--text-sm) !important;
        font-weight: 600 !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow-sm) !important;
        transition: background 0.15s, border-color 0.15s !important;
    }
    .stButton > button[kind="primary"]:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-light) !important;
    }

    /* Secondary button — 14px/600 semi-bold */
    .stButton > button:not([kind="primary"]) {
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        color: var(--foreground) !important;
        font-family: var(--font-sans) !important;
        font-size: var(--text-sm) !important;
        font-weight: 600 !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow-sm) !important;
        transition: background 0.15s, border-color 0.15s !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-light) !important;
    }

    /* Inputs — 16px/400 */
    .stTextInput input, .stTextArea textarea {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        background: var(--card-bg) !important;
        color: var(--foreground) !important;
        font-family: var(--font-sans) !important;
        font-size: var(--text-base) !important;
        font-weight: 400 !important;
        transition: border-color 0.15s, box-shadow 0.15s !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(161,0,255,0.1) !important;
    }
    /* Hide browser-native password reveal button (Edge/IE ::-ms-reveal) —
       Streamlit already provides its own toggle so the native one is a duplicate. */
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear { display: none !important; }

    /* Selectbox — 16px/400 */
    .stSelectbox > div > div {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        background: var(--card-bg) !important;
        font-size: var(--text-base) !important;
        font-family: var(--font-sans) !important;
    }
    /* ── Sidebar selectbox: full vertical-centering chain ──────────────────
       Each level must be explicitly set — JS fixes don't survive re-renders.
       BaseWeb ValueContainer defaults to flex-wrap:wrap which breaks centering.
       ControlContainer needs an explicit height so height:100% resolves below. */

    /* Level 1 — ControlContainer (the visible box) */
    [data-testid="stSidebar"] [data-baseweb="select"] > div > div:first-child {
        display:         flex !important;
        align-items:     center !important;
        justify-content: center !important;
        position:        relative !important;
        height:          38px !important;
        padding:         0 !important;
    }
    /* Level 2 — ValueContainer (wraps the value + hidden input)
       No height:100% — let flex auto-height so the * rule's padding-top:0 doesn't
       shift the content box relative to the control's visual centre. */
    [data-testid="stSidebar"] [data-baseweb="select"] > div > div:first-child > div:first-child {
        display:         flex !important;
        flex-wrap:       nowrap !important;
        align-items:     center !important;
        justify-content: center !important;
        flex:            1 !important;
        overflow:        hidden !important;
        padding:         0 !important;
        margin:          0 !important;
    }
    /* Level 3 — SingleValue div ([data-baseweb="value"])
       Same: no height:100%, no padding, no margin — pure flex centering. */
    [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="value"] {
        flex:            1 1 0 !important;
        display:         flex !important;
        justify-content: center !important;
        align-items:     center !important;
        text-align:      center !important;
        max-width:       100% !important;
        padding:         0 !important;
        margin:          0 !important;
    }
    /* Selected value text — line-height:1 removes asymmetric font leading (Poppins
       has extra descender space that makes line-height:1.5 appear top-heavy). */
    [data-testid="stSidebar"] [data-baseweb="value"],
    [data-testid="stSidebar"] [data-baseweb="value"] div,
    [data-testid="stSidebar"] [data-baseweb="value"] span {
        font-size:      0.9375rem !important;
        font-weight:    600 !important;
        letter-spacing: 0.01em !important;
        line-height:    1 !important;
        text-align:     center !important;
        width:          100% !important;
        padding:        0 !important;
        margin:         0 !important;
    }
    /* Take typing input out of flex flow entirely */
    [data-testid="stSidebar"] [data-baseweb="select"] input {
        position:       absolute !important;
        pointer-events: none !important;
        opacity:        0 !important;
        width:          0 !important;
        height:         0 !important;
    }
    /* Pointer cursor on sidebar dropdowns — overrides browser's text cursor
       which leaks from the hidden BaseWeb input element inside the select */
    [data-testid="stSidebar"] [data-baseweb="select"],
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        cursor: pointer !important;
    }

    /* Date input — outer wrapper: no border, inner base-input: full border */
    [data-testid="stDateInput"] [data-baseweb="input"] {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    [data-testid="stDateInput"] [data-baseweb="base-input"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        background: var(--card-bg) !important;
        box-shadow: none !important;
        min-height: 42px !important;
        transition: border-color 0.15s !important;
    }
    [data-testid="stDateInput"] [data-baseweb="base-input"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(161,0,255,0.1) !important;
    }
    [data-testid="stDateInput"] input {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        color: var(--foreground) !important;
        font-family: var(--font-sans) !important;
        font-size: var(--text-base) !important;
        min-height: 40px !important;
    }

    /* Custom collapsible — replaces st.expander (Description section) */
    .custom-details {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--card-bg);
        box-shadow: var(--shadow-sm);
        margin-bottom: 10px;
        overflow: hidden;
    }
    .custom-summary {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 14px 18px;
        cursor: pointer;
        list-style: none;
        font-family: var(--font-sans);
        font-size: var(--text-base);
        font-weight: 600;
        color: var(--foreground);
        user-select: none;
    }
    .custom-summary::-webkit-details-marker { display: none; }
    .custom-summary::marker { display: none; }
    .custom-summary:hover { background: var(--muted); }
    .custom-summary-label { flex: 1; }
    .custom-summary-arrow {
        display: inline-block;
        flex-shrink: 0;
        width: 7px;
        height: 7px;
        border-right: 2px solid #6B7280;
        border-bottom: 2px solid #6B7280;
        transform: rotate(45deg);
        transition: transform 0.25s ease;
    }
    .custom-details[open] .custom-summary-arrow {
        transform: rotate(-135deg);
    }
    .custom-details-body {
        padding: 14px 18px;
        border-top: 1px solid var(--border);
        font-size: var(--text-base);
        color: var(--foreground);
        line-height: 1.6;
    }

    /* Download PDF button — matches secondary/back button style */
    [data-testid="stDownloadButton"] button {
        background: var(--card-bg) !important;
        color: var(--foreground) !important;
        border: 1px solid var(--border) !important;
        font-family: var(--font-sans) !important;
        font-size: var(--text-sm) !important;
        font-weight: 600 !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow-sm) !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        transition: background 0.15s, border-color 0.15s !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-light) !important;
    }
    [data-testid="stDownloadButton"] button::before {
        font-family: 'Material Icons Round' !important;
        content: 'download' !important;
        font-size: 17px !important;
        line-height: 1 !important;
    }

    /* Form */
    [data-testid="stForm"] {
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 24px 26px !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* Alert — 14px */
    [data-testid="stAlert"] {
        border-radius: var(--radius-sm) !important;
        font-size: var(--text-sm) !important;
    }

    /* Caption — 12px/500 */
    .stCaption, small {
        font-size: var(--text-xs) !important;
        font-weight: 500 !important;
        color: var(--muted-text) !important;
    }

    /* Spinner */
    .stSpinner > div { border-top-color: var(--accent) !important; }

    /* ═══════════════════════════════════════════════════
       INCIDENTS TABLE
    ═══════════════════════════════════════════════════ */
    .ir-table-wrap {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
        overflow: hidden;
        margin-top: 4px;
    }
    .ir-table {
        width: 100%;
        border-collapse: collapse;
        font-family: var(--font-sans);
        font-size: var(--text-sm);
    }
    .ir-table thead tr {
        background: #F9FAFB;
        border-bottom: 2px solid var(--border);
    }
    .ir-table th {
        padding: 11px 14px;
        text-align: left;
        font-size: var(--text-xs) !important;
        font-weight: 700 !important;
        color: var(--muted-text) !important;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        white-space: nowrap;
        user-select: none;
    }
    .ir-table th.sortable { cursor: pointer; }
    .ir-table th.sortable:hover { color: var(--accent) !important; }
    .ir-table td {
        padding: 11px 14px;
        border-bottom: 1px solid var(--border);
        vertical-align: middle;
        color: var(--foreground) !important;
        font-size: var(--text-sm) !important;
    }
    .ir-table tbody tr:last-child td { border-bottom: none; }
    .ir-table tbody tr:hover td { background: #F9FAFB; }
    .ir-table-id {
        font-family: var(--font-mono) !important;
        font-size: 0.68rem !important;
        font-weight: 700 !important;
        color: var(--muted-text) !important;
        background: var(--muted);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 2px 7px;
        white-space: nowrap;
    }
    .ir-table-title {
        font-weight: 600 !important;
        color: var(--foreground) !important;
        font-size: var(--text-sm) !important;
        max-width: 280px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
    }
    .ir-table-meta {
        font-size: var(--text-xs) !important;
        color: var(--muted-text) !important;
    }
    /* Status badges */
    .ir-status { display: inline-flex; align-items: center; gap: 5px;
                 padding: 3px 10px; border-radius: 999px;
                 font-size: 11px !important; font-weight: 600 !important; white-space: nowrap; }
    .ir-status-open           { background: #FFF7ED; color: var(--high); }
    .ir-status-under-review   { background: #EFF6FF; color: var(--resolved); }
    .ir-status-critical-active{ background: var(--critical-bg); color: var(--critical); }
    .ir-status-resolved       { background: var(--low-bg); color: var(--low); }
    .ir-status-logged         { background: #F3F4F6; color: #6B7280; }

    /* ── Broadcast Impact Check — radio pill toggles ──────────────────────── */
    [data-testid="stRadio"] [role="radiogroup"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        align-items: center !important;
    }
    [data-testid="stRadio"] label {
        background: #F9FAFB !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 100px !important;
        padding: 7px 20px 7px 14px !important;
        cursor: pointer !important;
        margin: 0 !important;
        transition: background 0.22s ease, border-color 0.22s ease !important;
    }
    [data-testid="stRadio"] label:has(input:checked) {
        background: #FAF5FF !important;
        border-color: #A100FF !important;
    }
    [data-testid="stRadio"] label p {
        font-size: 0.825rem !important;
        font-weight: 500 !important;
        font-family: 'Poppins', sans-serif !important;
        color: #111827 !important;
        margin: 0 !important;
        transition: color 0.2s ease, font-weight 0.15s ease !important;
    }
    [data-testid="stRadio"] label:has(input:checked) p {
        color: #7C3AED !important;
        font-weight: 700 !important;
    }
    /* Hide the radio dot — pill border + text colour carry the selected state */
    [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
        display: none !important;
    }

    /* ── Impact hint + action-ready badge — shared fade-in ────────────────── */
    @keyframes impactHintIn {
        from { opacity: 0; transform: translateY(-3px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .impact-hint {
        font-size: 0.78rem !important;
        font-family: 'Poppins', sans-serif !important;
        margin: 6px 0 0 !important;
        animation: impactHintIn 0.25s ease forwards !important;
        display: inline-block !important;
        padding: 3px 12px !important;
        border-radius: 100px !important;
    }
    .impact-hint-broadcast {
        color: #7C3AED !important; background: #FAF5FF !important;
        border: 1px solid #DDD6FE !important;
    }
    .impact-hint-log {
        color: #6B7280 !important; background: #F3F4F6 !important;
        border: 1px solid #E5E7EB !important;
    }
    .impact-hint-none { color: #9CA3AF !important; }

    .btn-action-ready {
        font-size: 0.75rem !important;
        font-family: 'Poppins', sans-serif !important;
        padding: 3px 14px !important;
        border-radius: 100px !important;
        display: inline-block !important;
        animation: impactHintIn 0.25s ease forwards !important;
    }
    .btn-action-broadcast {
        background: #FAF5FF !important; color: #7C3AED !important;
        border: 1px solid #DDD6FE !important;
    }
    .btn-action-log {
        background: #F3F4F6 !important; color: #6B7280 !important;
        border: 1px solid #E5E7EB !important;
    }
    .btn-action-none { color: #9CA3AF !important; }

    /* Disabled submit buttons — clear dimmed state */
    [data-testid="stFormSubmitButton"] button:disabled {
        opacity: 0.3 !important;
        transition: opacity 0.2s ease !important;
    }
    [data-testid="stFormSubmitButton"] button:not(:disabled) {
        transition: all 0.2s ease !important;
    }

    /* Filter bar */
    .ir-filter-bar {
        display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 12px 16px;
        margin-bottom: 14px;
        box-shadow: var(--shadow-sm);
    }
    .ir-filter-label {
        font-size: var(--text-xs) !important; font-weight: 700 !important;
        color: var(--muted-text) !important; text-transform: uppercase;
        letter-spacing: 0.07em; white-space: nowrap;
    }
    .ir-table-empty {
        text-align: center; padding: 48px 20px;
        color: var(--muted-text);
        font-size: var(--text-sm) !important;
    }
    .ir-table-action button {
        font-size: 11px !important; padding: 4px 10px !important;
        height: auto !important; min-height: 0 !important;
    }

    /* ═══════════════════════════════════════════════════
       ANIMATIONS & SCROLLBAR
    ═══════════════════════════════════════════════════ */
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #CBD5E1; }

    /* ═══════════════════════════════════════════════════
       CARD ENTRANCE ANIMATION
    ═══════════════════════════════════════════════════ */
    @keyframes _irFadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .ir-animate-in {
        animation: _irFadeInUp 320ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
    }
    @media (prefers-reduced-motion: reduce) {
        .ir-animate-in, .metric-card, .incident-row { animation: none !important; }
    }

    </style>
    """, unsafe_allow_html=True)

    air_src = _logo_base64()
    st.markdown(f"""
    <style>
    @keyframes _airOverlayFade {{
      0%   {{ opacity: 1; }}
      70%  {{ opacity: 1; }}
      100% {{ opacity: 0; visibility: hidden; pointer-events: none; }}
    }}
    @keyframes _airLogoEntry {{
      0%   {{ transform: scale(0.82) translateY(8px); opacity: 0; }}
      50%  {{ transform: scale(1.03) translateY(-2px); opacity: 1; }}
      100% {{ transform: scale(1.0)  translateY(0);    opacity: 1; }}
    }}
    @keyframes _airTaglineFade {{
      0%   {{ opacity: 0; letter-spacing: 0.35em; }}
      100% {{ opacity: 0.55; letter-spacing: 0.28em; }}
    }}
    #_air-splash {{
      position: fixed; inset: 0; z-index: 99999;
      background: #ffffff;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center; gap: 20px;
      animation: _airOverlayFade 2.4s ease-in-out forwards;
      animation-delay: 0.3s;
      pointer-events: none;
    }}
    #_air-splash.skip {{ display: none !important; }}
    #_air-splash img {{
      width: 140px; height: auto;
      animation: _airLogoEntry 0.9s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    }}
    #_air-splash-tag {{
      font-family: Poppins, sans-serif;
      font-size: 0.72rem; font-weight: 500;
      letter-spacing: 0.35em; color: #A100FF;
      text-transform: uppercase;
      animation: _airTaglineFade 1.1s ease-out 0.5s forwards;
      opacity: 0;
    }}
    </style>

    <div id="_air-splash">
      <img src="{air_src}" alt="AIR"/>
      <span id="_air-splash-tag">Global Accenture Incident Response</span>
    </div>

    <script>
    (function() {{
      if (sessionStorage.getItem('_airSplashShown') === '1') {{
        var el = document.getElementById('_air-splash');
        if (el) el.classList.add('skip');
      }} else {{
        sessionStorage.setItem('_airSplashShown', '1');
      }}
    }})();
    </script>
    """, unsafe_allow_html=True)


def fix_sidebar_padding():
    """Inject JS into parent page to remove sidebar top padding and fix date input border."""
    components.html(
        """
        <script>
        (function() {
            function injectStyle(doc) {
                /* intentionally empty — date input CSS handled in inject_styles() */
            }

            function fixSidebar(doc) {
                /* Zero out padding on all sidebar wrappers */
                var uc = doc.querySelector('[data-testid="stSidebarUserContent"]');
                [doc.querySelector('[data-testid="stSidebarContent"]'), uc]
                    .forEach(function(el) {
                        if (!el) return;
                        el.style.setProperty('padding-top',    '0px',    'important');
                        el.style.setProperty('padding-bottom', '0px',    'important');
                        el.style.setProperty('margin-top',     '0px',    'important');
                        el.style.setProperty('height',         '100%',   'important');
                        el.style.setProperty('overflow',       'hidden', 'important');
                    });
                /* Kill Streamlit's default 3rem bottom padding on sidebar block-container */
                var sbc = doc.querySelector('[data-testid="stSidebar"] .block-container')
                       || doc.querySelector('[data-testid="stSidebar"] [data-testid="stMainBlockContainer"]');
                if (sbc) {
                    sbc.style.setProperty('padding-top',    '0px', 'important');
                    sbc.style.setProperty('padding-bottom', '0px', 'important');
                    sbc.style.setProperty('margin-top',     '0px', 'important');
                }
                if (!uc) return;

                /* Find the stVerticalBlock that owns ≥2 direct div children
                   (those are the nav container + footer container).
                   Streamlit may nest several stVerticalBlocks — we want the outermost
                   one that actually has both containers as direct children. */
                var vb = null;
                var allVBs = uc.querySelectorAll('[data-testid="stVerticalBlock"]');
                for (var i = 0; i < allVBs.length; i++) {
                    var directDivs = Array.prototype.filter.call(
                        allVBs[i].children, function(c) { return c.tagName === 'DIV'; }
                    );
                    if (directDivs.length >= 2) { vb = allVBs[i]; break; }
                }
                if (!vb) vb = uc.querySelector('[data-testid="stVerticalBlock"]');
                if (!vb) return;

                /* Walk UP from vb to uc — every element in the chain must be
                   a flex column at full height so the stretch reaches all the way down */
                var el = vb.parentElement;
                while (el && el !== uc) {
                    el.style.setProperty('display',        'flex',     'important');
                    el.style.setProperty('flex-direction', 'column',   'important');
                    el.style.setProperty('height',         '100%',     'important');
                    el.style.setProperty('overflow',       'hidden',   'important');
                    el.style.setProperty('flex',           '1 1 auto', 'important');
                    el = el.parentElement;
                }

                /* vb itself: flex column, full height */
                vb.style.setProperty('display',        'flex',    'important');
                vb.style.setProperty('flex-direction', 'column',  'important');
                vb.style.setProperty('height',         '100%',    'important');
                vb.style.setProperty('overflow',       'hidden',  'important');
                vb.style.setProperty('gap',            '0',       'important');

                /* Apply flex roles to direct div children ONLY when there are
                   exactly 2 wrapper children (TL portal: nav container + footer container).
                   Reviewer portal has many raw element children — skip to avoid
                   making the first element consume all space and cut off the rest. */
                var kids = Array.prototype.filter.call(
                    vb.children, function(c) { return c.tagName === 'DIV'; }
                );
                if (kids.length === 2) {
                    /* Nav section: grows to fill all available space */
                    kids[0].style.setProperty('flex',       '1 1 auto', 'important');
                    kids[0].style.setProperty('overflow-y', 'auto',     'important');
                    kids[0].style.setProperty('min-height', '0',        'important');
                    /* Footer: natural height, pinned at bottom */
                    var footer = kids[1];
                    footer.style.setProperty('flex',           '0 0 auto', 'important');
                    footer.style.setProperty('background',     '#ffffff',  'important');
                    footer.style.setProperty('padding-bottom', '12px',     'important');
                }

                /* ── Sidebar selectbox: center value + match option font + remove typing ── */
                var selValues = uc.querySelectorAll('[data-baseweb="value"]');
                for (var sv = 0; sv < selValues.length; sv++) {
                    var v = selValues[sv];
                    /* ValueContainer (parent of value div):
                       flex-wrap:wrap causes align-items to center each line
                       independently — line sits at top of container.
                       Setting nowrap makes it a single-line container so
                       align-items:center truly centres vertically. */
                    var parent = v.parentElement;
                    if (parent) {
                        parent.style.setProperty('display',         'flex',   'important');
                        parent.style.setProperty('flex-wrap',       'nowrap', 'important');
                        parent.style.setProperty('align-items',     'center', 'important');
                        parent.style.setProperty('justify-content', 'center', 'important');
                        parent.style.setProperty('padding',         '0px',    'important');
                        parent.style.setProperty('margin',          '0px',    'important');
                        /* No height:100% — auto height lets flex centre correctly */
                    }
                    /* Value div: pure flex centering, no height trick */
                    v.style.setProperty('flex',            '1 1 0',  'important');
                    v.style.setProperty('display',         'flex',   'important');
                    v.style.setProperty('justify-content', 'center', 'important');
                    v.style.setProperty('align-items',     'center', 'important');
                    v.style.setProperty('align-self',      'center', 'important');
                    v.style.setProperty('text-align',      'center', 'important');
                    v.style.setProperty('max-width',       '100%',   'important');
                    v.style.setProperty('padding',         '0px',    'important');
                    v.style.setProperty('margin',          '0px',    'important');
                    /* No height:100% on v either */
                    v.style.setProperty('font-weight', '600', 'important');
                    var allInner = v.querySelectorAll('*');
                    for (var ai = 0; ai < allInner.length; ai++) {
                        var el = allInner[ai];
                        el.style.setProperty('font-weight',    '600',                                              'important');
                        el.style.setProperty('font-family',    'Poppins,-apple-system,BlinkMacSystemFont,sans-serif', 'important');
                        el.style.setProperty('color',          '#111827',                                           'important');
                        el.style.setProperty('text-align',     'center',                                            'important');
                        el.style.setProperty('white-space',    'nowrap',                                            'important');
                        el.style.setProperty('overflow',       'hidden',                                            'important');
                        el.style.setProperty('font-size',      '0.9375rem',                                         'important');
                        el.style.setProperty('letter-spacing', '0.01em',                                            'important');
                        el.style.setProperty('line-height',    '1',                                                  'important');
                        el.style.setProperty('width',          '100%',                                              'important');
                        el.style.setProperty('padding',        '0px',                                               'important');
                        el.style.setProperty('margin',         '0px',                                               'important');
                    }
                }
                /* Pull typing inputs out of flex flow */
                var selInputs = uc.querySelectorAll('[data-baseweb="select"] input');
                for (var si = 0; si < selInputs.length; si++) {
                    var inp = selInputs[si];
                    inp.style.setProperty('position',       'absolute', 'important');
                    inp.style.setProperty('opacity',        '0',        'important');
                    inp.style.setProperty('width',          '0',        'important');
                    inp.style.setProperty('height',         '0',        'important');
                    inp.style.setProperty('pointer-events', 'none',     'important');
                }
            }

            function fixMainPadding(doc) {
                /* Always overwrite the style tag so reruns stay correct */
                var styleId = 'ir-spacing-override';
                var s = doc.getElementById(styleId);
                if (!s) { s = doc.createElement('style'); s.id = styleId; doc.head.appendChild(s); }
                /* Dynamic width: read actual sidebar width */
                var sb  = doc.querySelector('[data-testid="stSidebar"]');
                var sbW = (sb && sb.getBoundingClientRect().width > 0)
                            ? Math.ceil(sb.getBoundingClientRect().width)
                            : 320;

                /* Update CSS variable so all rules using var(--sidebar-w) stay in sync */
                doc.documentElement.style.setProperty('--sidebar-w', sbW + 'px');

                s.textContent = [
                    'header,[data-testid="stHeader"]{display:none!important;height:0!important;min-height:0!important;}',
                    ':root{--sidebar-w:'+sbW+'px;}',
                    'section[data-testid="stMain"]{padding-top:0!important;margin-top:0!important;margin-left:var(--sidebar-w)!important;width:calc(100vw - var(--sidebar-w))!important;max-width:calc(100vw - var(--sidebar-w))!important;overflow-x:hidden!important;}',
                    '[data-testid="stMainBlockContainer"],.block-container{padding-top:64px!important;}',
                    '[data-testid="stSidebar"] .block-container,[data-testid="stSidebar"] [data-testid="stMainBlockContainer"]{padding-top:0!important;padding-bottom:0!important;margin-top:0!important;}',
                    '[data-testid="stSidebarUserContent"]>[data-testid="stVerticalBlock"],[data-testid="stSidebarUserContent"]>div>[data-testid="stVerticalBlock"]{display:flex!important;flex-direction:column!important;height:100%!important;overflow:hidden!important;gap:0!important;}',
                ].join('\n');

                /* Also set inline styles directly for immediate effect */
                var stMainSec = doc.querySelector('section[data-testid="stMain"]');
                if (stMainSec) {
                    stMainSec.style.setProperty('padding-top',  '0px', 'important');
                    stMainSec.style.setProperty('margin-top',   '0px', 'important');
                    stMainSec.style.setProperty('margin-left',  sbW + 'px', 'important');
                    stMainSec.style.setProperty('width',        'calc(100vw - ' + sbW + 'px)', 'important');
                    stMainSec.style.setProperty('max-width',    'calc(100vw - ' + sbW + 'px)', 'important');
                    stMainSec.style.setProperty('overflow-x',   'hidden', 'important');
                }
                var bc = doc.querySelector('[data-testid="stMainBlockContainer"]') || doc.querySelector('.main .block-container');
                if (bc) bc.style.setProperty('padding-top', '64px', 'important');
            }

            function applyFix() {
                var doc = window.parent.document;
                injectStyle(doc);
                fixSidebar(doc);
                fixMainPadding(doc);
            }

            applyFix();
            setTimeout(applyFix, 100);
            setTimeout(applyFix, 400);
            setTimeout(applyFix, 900);

            /* Re-run on window resize so layout stays correct if browser is resized */
            try {
                window.parent.addEventListener('resize', function() {
                    setTimeout(applyFix, 60);
                }, { passive: true });
            } catch(e) {}

            /* Re-run whenever Streamlit re-renders the DOM */
            try {
                var observer = new window.parent.MutationObserver(function(muts) {
                    for (var i = 0; i < muts.length; i++) {
                        if (muts[i].addedNodes.length) { setTimeout(applyFix, 80); break; }
                    }
                });
                observer.observe(
                    window.parent.document.querySelector('[data-testid="stMain"]') || window.parent.document.body,
                    { childList: true, subtree: false }
                );
            } catch(e) {}
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )


def render_footer():
    """Render the fixed bottom footer across all pages."""
    st.markdown("""
    <style>
    @keyframes _footerShimmer {
        0%   { background-position: -400px 0; }
        100% { background-position: 400px 0; }
    }
    @keyframes _footerPulse {
        0%, 100% { opacity: 0.35; }
        50%       { opacity: 0.9; }
    }
    @keyframes _footerFadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .ir-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 9998;
        height: 36px;
        background: rgba(255,255,255,0.96);
        backdrop-filter: blur(8px);
        border-top: 1px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        padding: 0 24px;
        animation: _footerFadeIn 0.6s ease 0.4s both;
    }
    .ir-footer-center {
        display: flex;
        align-items: center;
        gap: 8px;
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
    }
    .ir-footer-reviewer-btn {
        font-size: 0.6rem;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        letter-spacing: 0.05em;
        color: #A100FF;
        text-decoration: none;
        border: 1px solid #A100FF;
        border-radius: 4px;
        padding: 3px 10px;
        white-space: nowrap;
        transition: background 0.18s, color 0.18s;
        flex-shrink: 0;
    }
    .ir-footer-reviewer-btn:hover {
        background: #A100FF;
        color: #fff;
    }
    .ir-footer-label {
        font-size: 0.6rem;
        font-weight: 500;
        color: var(--muted-text);
        font-family: 'Poppins', sans-serif;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        flex-shrink: 0;
    }
    .ir-footer-brand {
        font-size: 0.65rem;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        letter-spacing: 0.05em;
        background: linear-gradient(
            90deg,
            #A100FF 0%,
            #002F5C 30%,
            #A100FF 60%,
            #002F5C 100%
        );
        background-size: 400px 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: _footerShimmer 4s linear infinite;
        flex-shrink: 0;
    }
    .ir-footer-sep {
        font-size: 0.6rem;
        font-weight: 300;
        color: var(--accent);
        font-family: 'Poppins', sans-serif;
        animation: _footerPulse 2.6s ease-in-out infinite;
        flex-shrink: 0;
    }
    .ir-footer-year {
        font-size: 0.6rem;
        font-weight: 600;
        color: var(--accent);
        font-family: 'Poppins', sans-serif;
        letter-spacing: 0.04em;
        flex-shrink: 0;
    }
    /* Push main content up so footer never overlaps */
    [data-testid="stMainBlockContainer"],
    .block-container {
        padding-bottom: 48px !important;
    }
    </style>

    <div class="ir-footer">
        <div style="flex:1;display:flex;justify-content:flex-start;align-items:center;">
            <a href="?portal=reviewer" target="_blank" class="ir-footer-reviewer-btn">
                Reviewer Portal →
            </a>
        </div>
        <div class="ir-footer-center">
            <span class="ir-footer-label">Powered by</span>
            <span class="ir-footer-brand">BKK IO VVO Innovation</span>
            <span class="ir-footer-sep">|</span>
            <span class="ir-footer-year">House of Odyssey 2026</span>
        </div>
        <div style="flex:1;"></div>
    </div>
    """, unsafe_allow_html=True)


def render_navbar(display_name: str = "", role: str = ""):
    """Render the fixed top navbar with the Accenture SVG logo."""
    air_logo_src = _logo_base64()
    acc_logo_src = _acc_logo_base64()

    initials = "".join(w[0].upper() for w in display_name.split()[:2]) if display_name else ""

    user_html = ""
    if display_name:
        user_html = (
            f'<div class="ir-navbar-user">'
            f'<div class="ir-navbar-avatar">{initials}</div>'
            f'<span class="ir-navbar-username">{display_name}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div class="ir-navbar">'
        f'<div class="ir-navbar-brand">'
        f'<img src="{acc_logo_src}" class="ir-navbar-acc-logo" alt="Accenture"/>'
        f'<div class="ir-navbar-wordmark">'
        f'<div class="ir-navbar-wordmark-main">Accenture</div>'
        f'<div class="ir-navbar-wordmark-sub">Operations</div>'
        f'</div>'
        f'</div>'
        f'<div class="ir-navbar-divider"></div>'
        f'<img src="{air_logo_src}" class="ir-navbar-air-logo" alt="Air"/>'
        f'<div class="ir-navbar-divider"></div>'
        f'<div class="ir-navbar-appname">Global Accenture Incident Response</div>'
        f'<div class="ir-navbar-spacer"></div>'
        f'{user_html}'
        f'</div>',
        unsafe_allow_html=True
    )


def render_chat_widget():
    """Render the floating global TL chat widget (demo — CSS checkbox toggle, no JS needed)."""
    st.markdown("""
    <style>
    /* Hidden checkbox drives the open/close — no JavaScript needed */
    #irChatCheck { display: none; }

    /* FAB — label acts as the clickable button */
    label.ir-chat-fab {
        position: fixed;
        bottom: 46px;
        right: 24px;
        z-index: 9997;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #A100FF, #002F5C);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 16px rgba(161,0,255,0.38);
        transition: transform 0.2s, box-shadow 0.2s;
        font-size: 18px;
        color: #fff;
        user-select: none;
    }
    label.ir-chat-fab:hover {
        transform: scale(1.08);
        box-shadow: 0 6px 22px rgba(161,0,255,0.48);
    }
    .ir-chat-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        background: #DC2626;
        color: #fff;
        font-size: 9px;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        border-radius: 999px;
        padding: 1px 5px;
        min-width: 16px;
        text-align: center;
        line-height: 14px;
        border: 1.5px solid #fff;
    }

    /* Panel — hidden by default */
    .ir-chat-panel {
        position: fixed;
        bottom: 98px;
        right: 24px;
        z-index: 9997;
        width: 320px;
        height: 430px;
        background: #fff;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.14);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        transform-origin: bottom right;
        opacity: 0;
        pointer-events: none;
        transform: scale(0.92) translateY(10px);
        transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.2,0.8,0.2,1);
    }

    /* When checkbox checked: show panel, hide badge */
    #irChatCheck:checked ~ label.ir-chat-fab .ir-chat-badge {
        display: none;
    }
    #irChatCheck:checked ~ .ir-chat-panel {
        opacity: 1;
        pointer-events: all;
        transform: scale(1) translateY(0);
    }

    .ir-chat-header {
        padding: 12px 16px;
        border-bottom: 1px solid #E5E7EB;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-shrink: 0;
        background: linear-gradient(90deg,rgba(161,0,255,0.04),rgba(0,47,92,0.03));
    }
    .ir-chat-header-title {
        font-size: 12px;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        color: #111827;
        display: flex;
        align-items: center;
        gap: 7px;
    }
    .ir-chat-online-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #16A34A;
        box-shadow: 0 0 0 2px #dcfce7;
        flex-shrink: 0;
    }
    label.ir-chat-close-btn {
        background: transparent;
        cursor: pointer;
        color: #9CA3AF;
        font-size: 15px;
        line-height: 1;
        padding: 3px 5px;
        border-radius: 4px;
        transition: background 0.15s, color 0.15s;
        font-family: sans-serif;
        user-select: none;
    }
    label.ir-chat-close-btn:hover { background: #F3F4F6; color: #374151; }
    .ir-chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 12px 14px;
        display: flex;
        flex-direction: column;
        gap: 11px;
    }
    .ir-chat-msg { display: flex; flex-direction: column; gap: 3px; }
    .ir-chat-msg-meta {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 10px;
        color: #9CA3AF;
        font-family: 'Poppins', sans-serif;
    }
    .ir-chat-msg-name {
        font-weight: 600;
        color: #374151;
        font-family: 'Poppins', sans-serif;
        font-size: 10px;
    }
    .ir-chat-mkt {
        background: #F3E8FF;
        color: #A100FF;
        font-size: 8.5px;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        padding: 1px 5px;
        border-radius: 999px;
    }
    .ir-chat-msg-bubble {
        background: #F3F4F6;
        border-radius: 4px 10px 10px 10px;
        padding: 7px 11px;
        font-size: 11.5px;
        font-family: 'Poppins', sans-serif;
        color: #111827;
        line-height: 1.5;
        max-width: 270px;
        word-break: break-word;
    }
    .ir-chat-msg.ir-own .ir-chat-msg-meta { justify-content: flex-end; }
    .ir-chat-msg.ir-own .ir-chat-msg-bubble {
        background: linear-gradient(135deg,#A100FF,#7C3AED);
        color: #fff;
        border-radius: 10px 4px 10px 10px;
        align-self: flex-end;
    }
    .ir-chat-msg.ir-own .ir-chat-mkt { background: #EDE9FE; color: #7C3AED; }
    .ir-chat-input-row {
        border-top: 1px solid #E5E7EB;
        padding: 10px 12px;
        display: flex;
        gap: 8px;
        align-items: center;
        flex-shrink: 0;
    }
    .ir-chat-input {
        flex: 1;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 7px 11px;
        font-size: 11.5px;
        font-family: 'Poppins', sans-serif;
        color: #111827;
        background: #F9FAFB;
        outline: none;
        transition: border-color 0.15s, background 0.15s;
        height: 36px;
    }
    .ir-chat-input:focus { border-color: #A100FF; background: #fff; }
    .ir-chat-send-btn {
        width: 36px; height: 36px;
        background: linear-gradient(135deg,#A100FF,#7C3AED);
        border: none;
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 13px;
        color: #fff;
        transition: opacity 0.15s, transform 0.12s;
    }
    .ir-chat-send-btn:hover { opacity: 0.88; transform: scale(1.06); }
    </style>

    <!-- Checkbox is the toggle mechanism — no JS needed -->
    <input type="checkbox" id="irChatCheck">

    <!-- FAB: label linked to checkbox -->
    <label for="irChatCheck" class="ir-chat-fab" title="Global TL Chat">
        💬
        <span class="ir-chat-badge">3</span>
    </label>

    <!-- Chat panel -->
    <div class="ir-chat-panel">
        <div class="ir-chat-header">
            <div class="ir-chat-header-title">
                <div class="ir-chat-online-dot"></div>
                Global TL Chat
            </div>
            <!-- Close button: also a label for the same checkbox -->
            <label for="irChatCheck" class="ir-chat-close-btn">✕</label>
        </div>
        <div class="ir-chat-messages">
            <div class="ir-chat-msg">
                <div class="ir-chat-msg-meta">
                    <span class="ir-chat-msg-name">Amir H.</span>
                    <span class="ir-chat-mkt">BKK</span>
                    <span>10:02 AM</span>
                </div>
                <div class="ir-chat-msg-bubble">Anyone seeing Maxbill spikes in your market? We've had 3 alerts in the past hour.</div>
            </div>
            <div class="ir-chat-msg">
                <div class="ir-chat-msg-meta">
                    <span class="ir-chat-msg-name">Sara K.</span>
                    <span class="ir-chat-mkt">KL</span>
                    <span>10:04 AM</span>
                </div>
                <div class="ir-chat-msg-bubble">Yes, same here. AHT jumped 15% in the past hour too. Raised a P2 already.</div>
            </div>
            <div class="ir-chat-msg">
                <div class="ir-chat-msg-meta">
                    <span class="ir-chat-msg-name">Wei L.</span>
                    <span class="ir-chat-mkt">SG</span>
                    <span>10:06 AM</span>
                </div>
                <div class="ir-chat-msg-bubble">We're clear on our end. No spikes. Could be a regional infra issue.</div>
            </div>
            <div class="ir-chat-msg">
                <div class="ir-chat-msg-meta">
                    <span class="ir-chat-msg-name">Priya M.</span>
                    <span class="ir-chat-mkt">MNL</span>
                    <span>10:09 AM</span>
                </div>
                <div class="ir-chat-msg-bubble">Just escalated to infra. They're investigating the Maxbill gateway. Will update soon.</div>
            </div>
            <div class="ir-chat-msg ir-own">
                <div class="ir-chat-msg-meta">
                    <span class="ir-chat-msg-name">You</span>
                    <span class="ir-chat-mkt">VVO</span>
                    <span>10:11 AM</span>
                </div>
                <div class="ir-chat-msg-bubble">Thanks for the update. Monitoring closely from our side.</div>
            </div>
        </div>
        <div class="ir-chat-input-row">
            <input class="ir-chat-input" placeholder="Type a message…"/>
            <button class="ir-chat-send-btn" title="Send">&#9658;</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
