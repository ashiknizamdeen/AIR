import streamlit as st
import streamlit.components.v1 as components
import base64, json, os, sys

sys.path.insert(0, os.path.dirname(__file__))

from config import MARKETS, MARKET_REVIEWERS, REVIEWER_FLOWS, SEVERITY_ICONS
from storage import (
    get_user_notifications,
    mark_notification_read,
    mark_notification_responded,
    add_response,
    add_resolution_response,
    acknowledge_news,
    mark_news_acknowledged,
)
from styles import fix_sidebar_padding



# ══════════════════════════════════════════════════════════════════════════════
# ASSETS
# ══════════════════════════════════════════════════════════════════════════════

_ACC_SVG_PATH = os.path.join(os.path.dirname(__file__), "Accenture-logo.svg")

def _acc_logo_b64() -> str:
    with open(_ACC_SVG_PATH, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/svg+xml;base64,{data}"


SEVERITY_COLORS = {
    "Critical": ("#FEF2F2", "#DC2626"),
    "High":     ("#FFF7ED", "#EA580C"),
    "Medium":   ("#FFFBEB", "#B45309"),
    "Low":      ("#F0FDF4", "#16A34A"),
    "Unknown":  ("#F3F4F6", "#6B7280"),
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _pending(username: str) -> list:
    return [
        n for n in get_user_notifications(username)
        if not n.get("responded") and not n.get("superseded")
    ]


# ══════════════════════════════════════════════════════════════════════════════
# NAVBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_navbar():
    acc_src  = _acc_logo_b64()
    username = st.session_state.rev_username or ""

    if username:
        display_name = username.rsplit('_', 1)[0].capitalize()
        initials     = display_name[0].upper() if display_name else "?"
        flow         = REVIEWER_FLOWS.get(username, ["—"])[0]
        arrow_rotate = "rotate(180deg)" if st.session_state.navbar_open else "rotate(0deg)"
        arrow_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
            f'viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" '
            f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" '
            f'style="transition:transform 0.2s ease;transform:{arrow_rotate};'
            f'flex-shrink:0;margin-left:2px;">'
            f'<polyline points="6 9 12 15 18 9"></polyline>'
            f'</svg>'
        )
        user_html = (
            f'<div id="ir-navbar-user-trigger" class="ir-navbar-user" '
            f'style="cursor:pointer;user-select:none;">'
            f'<div class="ir-navbar-avatar">{initials}</div>'
            f'<div>'
            f'<div class="ir-navbar-username">{display_name}</div>'
            f'<div class="ir-navbar-market">{flow}</div>'
            f'</div>'
            f'{arrow_svg}'
            f'</div>'
        )
    else:
        user_html = ""

    st.markdown(
        f'<style>'
        f'@keyframes _demoFadeIn{{'
        f'from{{opacity:0;transform:translateY(-2px)}}'
        f'to{{opacity:1;transform:translateY(0)}}'
        f'}}'
        f'.ir-demo-pill{{'
        f'display:inline-flex;align-items:center;gap:6px;'
        f'padding:3px 10px 3px 8px;'
        f'border-radius:999px;'
        f'border:1px solid #E5E7EB;'
        f'background:#FAFAFA;'
        f'animation:_demoFadeIn 0.4s ease 0.2s both;'
        f'flex-shrink:0;'
        f'}}'
        f'.ir-demo-pill-dot{{'
        f'width:6px;height:6px;border-radius:50%;'
        f'background:#D97706;flex-shrink:0;'
        f'}}'
        f'.ir-demo-pill-text{{'
        f'font-size:0.58rem;font-weight:600;'
        f'color:#6B7280;letter-spacing:0.07em;'
        f'text-transform:uppercase;font-family:Poppins,sans-serif;'
        f'white-space:nowrap;'
        f'}}'
        f'</style>'
        f'<div class="ir-navbar">'
        f'<div class="ir-navbar-brand">'
        f'<img src="{acc_src}" class="ir-navbar-acc-logo" alt="Accenture"/>'
        f'<div class="ir-navbar-wordmark">'
        f'<div class="ir-navbar-wordmark-main">Accenture</div>'
        f'<div class="ir-navbar-wordmark-sub">Operations</div>'
        f'</div>'
        f'</div>'
        f'<div class="ir-navbar-divider"></div>'
        f'<div class="ir-navbar-appname">Accenture Response Team</div>'
        f'<div class="ir-demo-pill">'
        f'<span class="ir-demo-pill-dot"></span>'
        f'<span class="ir-demo-pill-text">Demo</span>'
        f'</div>'
        f'<div class="ir-navbar-spacer"></div>'
        f'{user_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

_SECTION_LABEL = (
    'font-size:0.53rem;font-weight:700;color:#111827;'
    'text-transform:uppercase;letter-spacing:0.1em;'
    'padding-bottom:6px;font-family:Poppins,sans-serif;'
)

def render_sidebar():
    with st.sidebar:

        st.markdown(
            '<div style="padding:16px 0 12px;border-bottom:1px solid #E5E7EB;">'
            f'<div style="font-size:1.05rem;font-weight:700;color:#111827;'
            f'text-align:left;font-family:Poppins,sans-serif;">Reviewer Portal</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        username      = st.session_state.rev_username or ""
        pending_count = len(_pending(username)) if username else 0

        st.markdown(
            f'<div style="height:16px;"></div>'
            f'<div style="{_SECTION_LABEL}">Status</div>',
            unsafe_allow_html=True,
        )
        if pending_count:
            st.markdown(
                f'<div style="background:#FEF2F2;border:1px solid #E5E7EB;'
                f'border-radius:6px;height:32px;width:100%;'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:0.70rem;color:#DC2626;font-weight:600;'
                f'font-family:Poppins,sans-serif;">'
                f'🔔 {pending_count} pending response{"s" if pending_count != 1 else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:#F0FDF4;border:1px solid #E5E7EB;'
                'border-radius:6px;height:32px;width:100%;'
                'display:flex;align-items:center;justify-content:center;'
                'font-size:0.70rem;color:#16A34A;font-weight:600;'
                'font-family:Poppins,sans-serif;">'
                '✓ All caught up</div>',
                unsafe_allow_html=True,
            )



# ══════════════════════════════════════════════════════════════════════════════
# NAVBAR DROPDOWN
# ══════════════════════════════════════════════════════════════════════════════

def _inject_navbar_js(is_open: bool):
    """
    Injects a 0-height iframe that:
      - Hides U+2801 (toggle) and U+2802 (selection) buttons off-screen
      - Wires click on #ir-navbar-user-trigger to the hidden toggle button
      - When is_open=True, builds a floating panel injected into document.body
        with native <select> elements; on change, clicks the matching hidden button
    """
    market    = st.session_state.get("rev_market", MARKETS[0])
    reviewers = MARKET_REVIEWERS.get(market, [])
    username  = st.session_state.get("rev_username") or (reviewers[0] if reviewers else "")
    rev_labels = {
        r: "{} ({})".format(
            r.rsplit('_', 1)[0].capitalize(),
            ", ".join(REVIEWER_FLOWS.get(r, ["—"]))
        )
        for r in reviewers
    }

    data = {
        "isOpen":      is_open,
        "curMarket":   market,
        "curReviewer": username,
        "markets":     list(MARKETS),
        "reviewers":   reviewers,
        "revLabels":   rev_labels,
    }
    data_json = json.dumps(data, ensure_ascii=True)

    # JS written as a plain string (no Python f-string braces to escape)
    js_template = r"""
(function() {
    var DATA = __DATA__;
    var doc  = window.parent.document;

    /* ── Helpers ─────────────────────────────────────────────────── */
    function clickBtn(search) {
        var btns = doc.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].textContent.indexOf(search) !== -1) {
                btns[i].click();
                return;
            }
        }
    }

    function hideSpecialBtns() {
        var btns = doc.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            var txt = btns[i].textContent;
            if (txt.indexOf('\u2801') !== -1 || txt.indexOf('\u2802') !== -1) {
                var w = btns[i].closest('[data-testid="stButton"]') || btns[i].parentElement;
                if (w) w.style.cssText = 'position:fixed!important;top:-600px!important;'
                    + 'left:-600px!important;opacity:0!important;pointer-events:none!important;';
            }
        }
    }

    function removePanel() {
        var p = doc.getElementById('_ndp');
        if (p) p.remove();
        var s = doc.getElementById('_ndp_style');
        if (s) s.remove();
    }

    /* ── Build floating panel ────────────────────────────────────── */
    function buildPanel() {
        removePanel();
        if (!DATA.isOpen) return;

        /* CSS injected into <head> */
        var style = doc.createElement('style');
        style.id  = '_ndp_style';
        style.textContent = [
            '@keyframes _ndpIn{from{opacity:0;transform:translateY(-10px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}',
            '#_ndp{',
            '  position:fixed;top:68px;right:16px;z-index:99999;',
            '  background:#fff;border:1px solid #E5E7EB;border-radius:14px;',
            '  box-shadow:0 10px 32px rgba(0,0,0,.13),0 2px 8px rgba(0,0,0,.07);',
            '  padding:16px;width:236px;font-family:Poppins,Arial,sans-serif;',
            '  animation:_ndpIn .2s cubic-bezier(.4,0,.2,1);',
            '}',
            '#_ndp .acc{height:3px;background:linear-gradient(90deg,#002F5C 0%,#6E3FA3 55%,#A100FF 100%);border-radius:3px;margin-bottom:12px;}',
            '#_ndp .hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;}',
            '#_ndp .ttl{font-size:.72rem;font-weight:700;color:#111827;}',
            '#_ndp .cls{width:20px;height:20px;border-radius:50%;background:#F3F4F6;border:none;',
            '  cursor:pointer;font-size:.62rem;color:#6B7280;line-height:1;}',
            '#_ndp .cls:hover{background:#E5E7EB;color:#111827;}',
            '#_ndp .lbl{font-size:.52rem;font-weight:700;color:#9CA3AF;',
            '  text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;}',
            '#_ndp select{width:100%;padding:6px 8px;border:1px solid #D1D5DB;',
            '  border-radius:7px;font-size:.72rem;font-family:Poppins,Arial,sans-serif;',
            '  color:#111827;background:#F9FAFB;outline:none;cursor:pointer;}',
            '#_ndp select:focus{border-color:#A100FF;background:#fff;}',
            '#_ndp .dvd{height:1px;background:#F3F4F6;margin:10px 0;}',
        ].join('\n');
        doc.head.appendChild(style);

        /* Panel element */
        var p = doc.createElement('div');
        p.id  = '_ndp';

        /* Accent bar */
        var acc = doc.createElement('div'); acc.className = 'acc'; p.appendChild(acc);

        /* Header */
        var hdr = doc.createElement('div'); hdr.className = 'hdr';
        var ttl = doc.createElement('span'); ttl.className = 'ttl'; ttl.textContent = 'Switch Reviewer';
        var cls = doc.createElement('button'); cls.className = 'cls'; cls.innerHTML = '&#10005;';
        cls.addEventListener('click', function(e) {
            e.stopPropagation(); removePanel(); clickBtn('\u2801');
        });
        hdr.appendChild(ttl); hdr.appendChild(cls); p.appendChild(hdr);

        /* Market select */
        var mLbl = doc.createElement('div'); mLbl.className = 'lbl'; mLbl.textContent = 'Market';
        p.appendChild(mLbl);
        var mSel = doc.createElement('select'); mSel.id = '_ndp_msel';
        DATA.markets.forEach(function(m) {
            var o = doc.createElement('option'); o.value = m; o.textContent = m;
            if (m === DATA.curMarket) o.selected = true;
            mSel.appendChild(o);
        });
        mSel.addEventListener('change', function() {
            var v = this.value; removePanel(); clickBtn('\u2802' + v);
        });
        p.appendChild(mSel);

        /* Divider */
        var dvd = doc.createElement('div'); dvd.className = 'dvd'; p.appendChild(dvd);

        /* Reviewer select */
        var rLbl = doc.createElement('div'); rLbl.className = 'lbl'; rLbl.textContent = 'Reviewer';
        p.appendChild(rLbl);
        var rSel = doc.createElement('select'); rSel.id = '_ndp_rsel';
        DATA.reviewers.forEach(function(r) {
            var o = doc.createElement('option'); o.value = r;
            o.textContent = DATA.revLabels[r] || r;
            if (r === DATA.curReviewer) o.selected = true;
            rSel.appendChild(o);
        });
        rSel.addEventListener('change', function() {
            var v = this.value; removePanel(); clickBtn('\u2802' + v);
        });
        p.appendChild(rSel);

        doc.body.appendChild(p);

        /* Click-outside to close — stored reference so stale copies are removed */
        if (window.parent._ndpOutside) {
            doc.removeEventListener('click', window.parent._ndpOutside);
            window.parent._ndpOutside = null;
        }
        setTimeout(function() {
            window.parent._ndpOutside = function(e) {
                var panel   = doc.getElementById('_ndp');
                var trigger = doc.getElementById('ir-navbar-user-trigger');
                if (panel && !panel.contains(e.target) && (!trigger || !trigger.contains(e.target))) {
                    removePanel();
                    doc.removeEventListener('click', window.parent._ndpOutside);
                    window.parent._ndpOutside = null;
                    clickBtn('\u2801');
                }
            };
            doc.addEventListener('click', window.parent._ndpOutside);
        }, 120);
    }

    /* ── Wire navbar user trigger via event delegation ───────────── */
    /* Attach ONE handler on document (not on the trigger element),   */
    /* so it survives React replacing #ir-navbar-user-trigger on      */
    /* each rerun.  Old handler is removed before adding the new one. */
    function wireNavbar() {
        if (window.parent._ndpNavHandler) {
            doc.removeEventListener('click', window.parent._ndpNavHandler, true);
        }
        window.parent._ndpNavHandler = function(e) {
            var trigger = doc.getElementById('ir-navbar-user-trigger');
            if (trigger && trigger.contains(e.target)) {
                e.stopPropagation();
                clickBtn('\u2801');
            }
        };
        doc.addEventListener('click', window.parent._ndpNavHandler, true);
    }

    function setup() {
        hideSpecialBtns();
        wireNavbar();
        buildPanel();
    }

    setTimeout(setup, 80);
})();
"""
    js_code = js_template.replace('__DATA__', data_json)
    components.html(f"<script>{js_code}</script>", height=0)


def render_nav_dropdown():
    """
    Renders hidden Streamlit buttons (U+2801 toggle, U+2802+name selection),
    then injects the floating dropdown panel via _inject_navbar_js().
    """
    is_open = st.session_state.navbar_open

    # ── U+2801 toggle button ──────────────────────────────────────────────────
    if st.button("\u2801", key="navbar_toggle_btn"):
        st.session_state.navbar_open = not st.session_state.navbar_open
        st.rerun()

    # ── Hidden selection buttons (only rendered when dropdown is open) ────────
    if is_open:
        # One button per market (U+2802 + market name)
        for i, market in enumerate(MARKETS):
            if st.button(f"\u2802{market}", key=f"nav_msel_{i}"):
                st.session_state.rev_market    = market
                st.session_state.rev_username  = None
                st.session_state.open_notif    = None
                st.session_state.popup_expanded = False
                st.session_state.navbar_open   = False
                st.rerun()

        # One button per reviewer in current market (U+2802 + reviewer name)
        for reviewer in MARKET_REVIEWERS.get(st.session_state.rev_market, []):
            if st.button(f"\u2802{reviewer}", key=f"nav_rsel_{reviewer}"):
                st.session_state.rev_username  = reviewer
                st.session_state.open_notif    = None
                st.session_state.popup_expanded = False
                st.session_state.navbar_open   = False
                st.rerun()

    # ── Floating panel via JS injection ──────────────────────────────────────
    _inject_navbar_js(is_open)


# ══════════════════════════════════════════════════════════════════════════════
# COLORS
# ══════════════════════════════════════════════════════════════════════════════

_NEWS_RL_BG = {"Critical": "#FEF2F2", "High": "#FFF7ED", "Medium": "#FFFBEB", "Low": "#F0FDF4"}
_NEWS_RL_FG = {"Critical": "#DC2626", "High": "#EA580C", "Medium": "#B45309", "Low": "#16A34A"}

# Invisible Unicode characters used as unique trigger-button labels for the
# popup JS to locate and click each Streamlit hidden button without ambiguity.
_TRIG0 = "\u2800"   # slot 0 — bottom card (most urgent)
_TRIG1 = "\u2801"   # slot 1 — card stacked above slot 0
_TRIG2 = "\u2802"   # overflow "+N more" pill


# ══════════════════════════════════════════════════════════════════════════════
# POPUP — stacked notification cards (bottom-right, single fixed iframe)
# ══════════════════════════════════════════════════════════════════════════════

def _notif_card_fragment(notif: dict, slot: int) -> str:
    """Return an HTML fragment for one card inside the shared stack iframe."""
    def _esc(s: str) -> str:
        return (str(s)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("'", "&#39;"))

    trig     = _TRIG0 if slot == 0 else _TRIG1
    fn_name  = f"go{slot}"
    ntype    = notif.get("type", "new_incident")

    if ntype == "news":
        rl         = notif.get("risk_level", "Medium")
        bg_col     = _NEWS_RL_BG.get(rl, "#F3F4F6")
        fg_col     = _NEWS_RL_FG.get(rl, "#6B7280")
        badge_html = (f'<span class="badge" style="background:{bg_col};color:{fg_col};">'
                      f'📢 {_esc(rl)} Risk</span>')
        label_txt  = "News Alert"
        prompt_txt = "Click to view details &amp; acknowledge ›"
    elif ntype == "status_check":
        badge_html = '<span class="badge" style="background:#EFF6FF;color:#2563EB;">📡 Status Check</span>'
        label_txt  = "Status Check"
        prompt_txt = "Click to view details &amp; respond ›"
    else:
        severity   = notif.get("severity", "Unknown")
        sev_icon   = SEVERITY_ICONS.get(severity, "⚪")
        bg_col, fg_col = SEVERITY_COLORS.get(severity, ("#F3F4F6", "#6B7280"))
        badge_html = (f'<span class="badge" style="background:{bg_col};color:{fg_col};">'
                      f'{sev_icon} {_esc(severity)}</span>')
        label_txt  = "New Incident"
        prompt_txt = "Click to view details &amp; respond ›"

    title     = _esc(notif["title"])
    market    = _esc(notif["market"])
    team_lead = _esc(notif["team_lead"])
    ts        = _esc(notif["created_at"][:16].replace("T", " "))

    # Use plain string concatenation (no f-string brace escaping) so that
    # JS curly braces are always literal in the output.
    click_js = (
        "function " + fn_name + "(){"
        "try{"
        "var b=window.parent.document.querySelectorAll('button');"
        "for(var i=0;i<b.length;i++){"
        "if(b[i].textContent.trim()==='" + trig + "'){b[i].click();return;}"
        "}"
        "}catch(e){}}"
    )

    return f"""
<div class="card" onclick="{fn_name}()">
    <div class="accent"></div>
    <div class="cbody">
        <div class="header">{badge_html}<span class="lbl">{label_txt}</span></div>
        <div class="title">{title}</div>
        <div class="meta">
            <span>🌏 {market}</span><span>·</span>
            <span>👤 {team_lead}</span><span>·</span>
            <span>🕐 {ts}</span>
        </div>
        <div class="cta">{prompt_txt}</div>
    </div>
</div>
<script>{click_js}</script>
"""


def render_notification_stack(notifs: list, overflow_count: int = 0):
    """
    Render 1–2 notification cards (plus an optional '+N more' pill) in one
    fixed-position iframe anchored to the bottom-right corner.

    notifs[0] = bottom card (most urgent), notifs[1] = card above (if present).
    overflow_count > 0 adds an interactive pill above the top card that routes
    through a hidden _TRIG2 button to an inbox dialog.

    Animation strategy: entry motion is applied to the iframe element in the
    parent DOM (slide up from below viewport) — no keyframes inside the iframe,
    which eliminates background-container clipping artefacts.
    """
    if not notifs:
        return

    # Cards are ordered top→bottom in the DOM; flex-column renders them that way.
    # slot 1 (top) first, slot 0 (bottom) second.
    fragments = []

    if len(notifs) >= 2:
        fragments.append(_notif_card_fragment(notifs[1], 1))
    fragments.append(_notif_card_fragment(notifs[0], 0))

    overflow_html = ""
    overflow_js   = ""
    if overflow_count > 0:
        label = f"+{overflow_count} more notification{'s' if overflow_count > 1 else ''}"
        overflow_html = f"""
<div class="pill" onclick="goOverflow()">
    <span>{label}</span>
    <span style="opacity:.7;font-size:.65rem;">View all ›</span>
</div>"""
        overflow_js = (
            "function goOverflow(){"
            "try{"
            "var b=window.parent.document.querySelectorAll('button');"
            "for(var i=0;i<b.length;i++){"
            f"if(b[i].textContent.trim()==='{_TRIG2}'){{b[i].click();return;}}"
            "}"
            "}catch(e){}}"
        )

    cards_html = "\n".join(fragments)
    all_trigs  = f"'{_TRIG0}','{_TRIG1}','{_TRIG2}'"

    popup_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{background:transparent!important;overflow:hidden;}}
.stack{{display:flex;flex-direction:column;gap:8px;}}
.card{{
    background:#fff;border-radius:20px;overflow:hidden;
    font-family:'Poppins',sans-serif;cursor:pointer;
}}
.accent{{height:3px;background:linear-gradient(90deg,#002F5C 0%,#6E3FA3 55%,#A100FF 100%);}}
.cbody {{padding:10px 12px 10px;}}
.header{{display:flex;align-items:center;gap:6px;margin-bottom:6px;}}
.badge {{padding:2px 7px;border-radius:20px;font-size:.54rem;font-weight:700;
        letter-spacing:.03em;text-transform:uppercase;flex-shrink:0;}}
.lbl   {{font-size:.50rem;font-weight:600;color:#9CA3AF;text-transform:uppercase;
        letter-spacing:.08em;margin-left:auto;flex-shrink:0;}}
.title {{font-size:.75rem;font-weight:700;color:#111827;margin-bottom:5px;
        line-height:1.35;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.meta  {{font-size:.60rem;color:#9CA3AF;display:flex;gap:8px;margin-bottom:8px;
        flex-wrap:nowrap;overflow:hidden;}}
.meta span{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.cta   {{background:#F9FAFB;border:1px solid #E5E7EB;border-radius:7px;
        padding:6px 10px;font-size:.62rem;font-weight:600;
        color:#374151;text-align:center;}}
.pill  {{display:flex;justify-content:space-between;align-items:center;
        background:linear-gradient(90deg,#002F5C,#6E3FA3);
        color:#fff;border-radius:12px;padding:7px 14px;cursor:pointer;
        font-family:'Poppins',sans-serif;font-size:.62rem;font-weight:600;
        letter-spacing:.02em;}}
.pill:hover{{opacity:.88;}}
</style>
</head>
<body>
<div class="stack">
{overflow_html}
{cards_html}
</div>
<script>
{overflow_js}
(function(){{
    var f = null;
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {{
        try {{ if (iframes[i].contentWindow === window) {{ f = iframes[i]; break; }} }} catch(e) {{}}
    }}
    if (!f) return;

    var stackH = document.querySelector('.stack').offsetHeight;
    f.setAttribute('allowtransparency', 'true');
    f.style.setProperty('position',   'fixed',             'important');
    f.style.setProperty('right',      '24px',              'important');
    f.style.setProperty('width',      '360px',             'important');
    f.style.setProperty('height',     stackH + 'px',       'important');
    f.style.setProperty('z-index',    '99999',             'important');
    f.style.setProperty('border',     'none',              'important');
    f.style.setProperty('background', 'transparent',       'important');
    f.style.setProperty('transition', 'bottom .45s cubic-bezier(0.22,1,0.36,1)', 'important');

    f.style.setProperty('bottom', '-' + stackH + 'px', 'important');
    requestAnimationFrame(function() {{
        requestAnimationFrame(function() {{
            f.style.setProperty('bottom', '24px', 'important');
        }});
    }});

    // Hide ALL trigger buttons (slot 0, slot 1, overflow pill)
    try {{
        var trigs = [{all_trigs}];
        var btns = window.parent.document.querySelectorAll('button');
        for (var j = 0; j < btns.length; j++) {{
            if (trigs.indexOf(btns[j].textContent.trim()) !== -1) {{
                var wrap = btns[j].closest('[data-testid="stButton"]') || btns[j].parentElement;
                if (wrap) {{
                    wrap.style.setProperty('position',       'fixed',  'important');
                    wrap.style.setProperty('top',            '-200px', 'important');
                    wrap.style.setProperty('left',           '-200px', 'important');
                    wrap.style.setProperty('opacity',        '0',      'important');
                    wrap.style.setProperty('pointer-events', 'none',   'important');
                }}
            }}
        }}
    }} catch(ee) {{}}
}})();
</script>
</body>
</html>"""

    components.html(popup_html, height=1, scrolling=False)


# ══════════════════════════════════════════════════════════════════════════════
# NEWS DIALOG — modal overlay with full details + acknowledge button
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("News Alert")
def _show_news_dialog(notif: dict):
    rl     = notif.get("risk_level", "Medium")
    cat    = notif.get("category",   "Other")
    rsn    = notif.get("reasoning",  "")
    bg_col = _NEWS_RL_BG.get(rl, "#F3F4F6")
    fg_col = _NEWS_RL_FG.get(rl, "#6B7280")
    rsn_html = (
        f'<div style="font-size:0.67rem;color:#6B7280;font-style:italic;'
        f'padding:8px 10px;background:#FAFAFA;border-radius:7px;'
        f'border-left:3px solid #D1D5DB;margin-top:2px;">💡 {rsn}</div>'
        if rsn else ""
    )

    st.html(f"""
    <style>
    @keyframes dlgFadeIn {{
        from {{ transform:translateY(10px); opacity:0; }}
        to   {{ transform:translateY(0);   opacity:1; }}
    }}
    </style>
    <div style="font-family:'Poppins',sans-serif;
                animation:dlgFadeIn 0.3s cubic-bezier(.4,0,.2,1);">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;">
            <span style="background:{bg_col};color:{fg_col};padding:3px 9px;
                         border-radius:20px;font-size:0.62rem;font-weight:700;
                         letter-spacing:.5px;text-transform:uppercase;">
                📢 {rl} Risk
            </span>
            <span style="background:#F3F4F6;color:#374151;padding:3px 9px;
                         border-radius:20px;font-size:0.62rem;font-weight:600;">
                {cat}
            </span>
        </div>
        <div style="font-size:0.88rem;font-weight:700;color:#111827;
                    margin-bottom:8px;line-height:1.4;">
            {notif["title"]}
        </div>
        <div style="font-size:0.72rem;color:#374151;line-height:1.6;
                    padding:10px 12px;background:#F9FAFB;
                    border-radius:8px;border:1px solid #E5E7EB;margin-bottom:10px;">
            {notif.get("description", "")}
        </div>
        <div style="font-size:0.65rem;color:#6B7280;display:flex;
                    flex-wrap:wrap;gap:10px;margin-bottom:10px;">
            <span>🌏 {notif["market"]}</span>
            <span>👤 Team Lead: {notif["team_lead"]}</span>
            <span>🕐 {notif["created_at"][:16].replace("T", " ")}</span>
        </div>
        {rsn_html}
    </div>
    """)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    if st.button("✓ Acknowledge", type="primary", use_container_width=True,
                 key="dlg_ack"):
        news_id  = notif.get("news_id", "")
        username = st.session_state.rev_username
        acknowledge_news(news_id, username)
        mark_news_acknowledged(username, news_id)
        st.session_state.responded_msg = "acknowledged_news"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# NEWS READ-ONLY CARD — informational display in main body
# ══════════════════════════════════════════════════════════════════════════════

def _render_news_readonly(notif: dict):
    rl     = notif.get("risk_level", "Medium")
    cat    = notif.get("category",   "Other")
    rsn    = notif.get("reasoning",  "")
    bg_col = _NEWS_RL_BG.get(rl, "#F3F4F6")
    fg_col = _NEWS_RL_FG.get(rl, "#6B7280")
    rsn_html = (
        f'<div style="font-size:0.67rem;color:#6B7280;font-style:italic;'
        f'padding:8px 10px;background:#FAFAFA;border-radius:7px;'
        f'border-left:3px solid #D1D5DB;margin-bottom:0;">💡 {rsn}</div>'
        if rsn else ""
    )

    _, col, _ = st.columns([1, 2.4, 1])
    with col:
        st.html(f"""
        <style>
        @keyframes newsCardIn {{
            from {{ transform:translateY(14px); opacity:0; }}
            to   {{ transform:translateY(0);   opacity:1; }}
        }}
        </style>
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:14px;
                    padding:20px;box-shadow:0 4px 20px rgba(0,0,0,0.07);
                    font-family:'Poppins',sans-serif;
                    animation:newsCardIn 0.4s cubic-bezier(.4,0,.2,1);">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;">
                <span style="background:{bg_col};color:{fg_col};padding:3px 9px;
                             border-radius:20px;font-size:0.62rem;font-weight:700;
                             letter-spacing:.5px;text-transform:uppercase;">
                    📢 {rl} Risk
                </span>
                <span style="background:#F3F4F6;color:#374151;padding:3px 9px;
                             border-radius:20px;font-size:0.60rem;font-weight:600;">
                    {cat}
                </span>
                <span style="font-size:0.57rem;font-weight:600;color:#9CA3AF;
                             text-transform:uppercase;letter-spacing:.06em;margin-left:auto;">
                    News Alert
                </span>
            </div>
            <div style="font-size:0.92rem;font-weight:700;color:#111827;
                        margin-bottom:8px;line-height:1.4;">
                {notif["title"]}
            </div>
            <div style="font-size:0.72rem;color:#374151;line-height:1.6;
                        padding:10px 12px;background:#F9FAFB;
                        border-radius:8px;border:1px solid #E5E7EB;margin-bottom:10px;">
                {notif.get("description", "")}
            </div>
            <div style="font-size:0.65rem;color:#6B7280;display:flex;
                        flex-wrap:wrap;gap:10px;margin-bottom:{'10px' if rsn else '14px'};">
                <span>🌏 {notif["market"]}</span>
                <span>👤 Team Lead: {notif["team_lead"]}</span>
                <span>🕐 {notif["created_at"][:16].replace("T", " ")}</span>
            </div>
            {rsn_html}
            <div style="margin-top:14px;padding:10px 12px;
                        background:linear-gradient(135deg,#EFF6FF,#DBEAFE);
                        border-radius:7px;border:1px solid #BFDBFE;text-align:center;">
                <span style="font-size:0.67rem;color:#1D4ED8;font-weight:600;">
                    Use the notification popup at the bottom right to acknowledge this alert
                </span>
            </div>
        </div>
        """)


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENT READ-ONLY CARD — shown in main body while popup awaits click
# ══════════════════════════════════════════════════════════════════════════════

def _render_incident_readonly(notif: dict):
    severity        = notif.get("severity", "Unknown")
    sev_icon        = SEVERITY_ICONS.get(severity, "⚪")
    bg_col, txt_col = SEVERITY_COLORS.get(severity, ("#F3F4F6", "#6B7280"))
    notif_type      = notif.get("type", "new_incident")

    if notif_type == "status_check":
        badge = '<span style="background:#EFF6FF;color:#2563EB;padding:3px 9px;border-radius:20px;font-size:0.62rem;font-weight:700;letter-spacing:.5px;text-transform:uppercase;">📡 Status Check</span>'
        label = "Resolution Check"
        cta   = "Click the popup to confirm your resolution status"
        cta_bg, cta_border, cta_color = "#EFF6FF", "#BFDBFE", "#1D4ED8"
    else:
        badge = f'<span style="background:{bg_col};color:{txt_col};padding:3px 9px;border-radius:20px;font-size:0.62rem;font-weight:700;letter-spacing:.5px;text-transform:uppercase;">{sev_icon} {severity}</span>'
        label = "New Incident"
        cta   = "Click the notification popup at the bottom right to respond"
        cta_bg, cta_border, cta_color = "#FFFBEB", "#FDE68A", "#B45309"

    _, col, _ = st.columns([1, 2.4, 1])
    with col:
        st.html(f"""
        <style>
        @keyframes incCardIn {{
            from {{ transform:translateY(14px); opacity:0; }}
            to   {{ transform:translateY(0);   opacity:1; }}
        }}
        </style>
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:14px;
                    padding:20px;box-shadow:0 4px 20px rgba(0,0,0,0.07);
                    font-family:'Poppins',sans-serif;
                    animation:incCardIn 0.4s cubic-bezier(.4,0,.2,1);">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;">
                {badge}
                <span style="font-size:0.57rem;font-weight:600;color:#9CA3AF;
                             text-transform:uppercase;letter-spacing:.06em;margin-left:auto;">
                    {label}
                </span>
            </div>
            <div style="font-size:0.92rem;font-weight:700;color:#111827;
                        margin-bottom:8px;line-height:1.4;">
                {notif["title"]}
            </div>
            <div style="font-size:0.72rem;color:#374151;line-height:1.6;
                        padding:10px 12px;background:#F9FAFB;
                        border-radius:8px;border:1px solid #E5E7EB;margin-bottom:10px;">
                {notif.get("description", "—")}
            </div>
            <div style="font-size:0.65rem;color:#6B7280;display:flex;
                        flex-wrap:wrap;gap:10px;margin-bottom:14px;">
                <span>🌏 {notif["market"]}</span>
                <span>👤 Team Lead: {notif["team_lead"]}</span>
                <span>🕐 {notif["created_at"][:16].replace("T", " ")}</span>
            </div>
            <div style="padding:10px 12px;background:{cta_bg};
                        border-radius:7px;border:1px solid {cta_border};text-align:center;">
                <span style="font-size:0.67rem;color:{cta_color};font-weight:600;">
                    {cta}
                </span>
            </div>
        </div>
        """)


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENT DIALOGS — modal popups triggered by clicking the floating card
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("Incident Response")
def _show_incident_dialog(notif: dict):
    severity        = notif.get("severity", "Unknown")
    sev_icon        = SEVERITY_ICONS.get(severity, "⚪")
    bg_col, txt_col = SEVERITY_COLORS.get(severity, ("#F3F4F6", "#6B7280"))
    notif_id        = notif["notif_id"]
    inc_id          = notif["incident_id"]
    username        = st.session_state.rev_username

    mark_notification_read(username, notif_id)

    st.html(f"""
    <style>
    @keyframes dlgFadeIn {{
        from {{ transform:translateY(10px); opacity:0; }}
        to   {{ transform:translateY(0);   opacity:1; }}
    }}
    </style>
    <div style="font-family:'Poppins',sans-serif;
                animation:dlgFadeIn 0.3s cubic-bezier(.4,0,.2,1);">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;">
            <span style="background:{bg_col};color:{txt_col};padding:3px 9px;
                         border-radius:20px;font-size:0.62rem;font-weight:700;
                         letter-spacing:.5px;text-transform:uppercase;">
                {sev_icon} {severity}
            </span>
            <span style="font-size:0.57rem;font-weight:600;color:#9CA3AF;
                         text-transform:uppercase;letter-spacing:.06em;margin-left:auto;">
                Action Required
            </span>
        </div>
        <div style="font-size:0.88rem;font-weight:700;color:#111827;
                    margin-bottom:8px;line-height:1.4;">
            {notif["title"]}
        </div>
        <div style="font-size:0.72rem;color:#374151;line-height:1.6;
                    padding:10px 12px;background:#F9FAFB;
                    border-radius:8px;border:1px solid #E5E7EB;margin-bottom:10px;">
            {notif.get("description", "—")}
        </div>
        <div style="font-size:0.65rem;color:#6B7280;display:flex;
                    flex-wrap:wrap;gap:10px;margin-bottom:14px;">
            <span>🌏 {notif["market"]}</span>
            <span>👤 Team Lead: {notif["team_lead"]}</span>
            <span>🕐 {notif["created_at"][:16].replace("T", " ")}</span>
        </div>
        <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;
                    padding:10px 12px;font-size:0.75rem;font-weight:600;color:#111827;
                    text-align:center;margin-bottom:4px;">
            Are you impacted by this incident?
        </div>
    </div>
    """)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("I'm Impacted", use_container_width=True, type="primary",
                     key=f"dlg_aff_{notif_id}"):
            add_response(inc_id, username, True)
            mark_notification_responded(username, inc_id)
            st.session_state.open_notif    = None
            st.session_state.responded_msg = "confirmed_impacted"
            st.rerun()
    with c2:
        if st.button("Not Impacted", use_container_width=True,
                     key=f"dlg_not_{notif_id}"):
            add_response(inc_id, username, False)
            mark_notification_responded(username, inc_id)
            st.session_state.open_notif    = None
            st.session_state.responded_msg = "confirmed_not_impacted"
            st.rerun()


@st.dialog("Status Check")
def _show_status_check_dialog(notif: dict):
    notif_id = notif["notif_id"]
    inc_id   = notif["incident_id"]
    username = st.session_state.rev_username

    mark_notification_read(username, notif_id)

    actions = notif.get("remediation_actions", [])
    actions_html = ""
    if actions:
        steps = "".join(
            f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:7px;">'
            f'<span style="min-width:18px;height:18px;background:#EDE9FE;color:#7C3AED;'
            f'border-radius:50%;font-size:0.58rem;font-weight:700;display:inline-flex;'
            f'align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;">{i+1}</span>'
            f'<span style="font-size:0.76rem;color:#374151;line-height:1.45;">{act}</span>'
            f'</div>'
            for i, act in enumerate(actions)
        )
        actions_html = (
            f'<div style="background:#FAF5FF;border:1px solid #DDD6FE;border-radius:8px;'
            f'padding:12px 14px;margin-bottom:14px;">'
            f'<div style="font-size:0.62rem;font-weight:700;color:#7C3AED;'
            f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
            f'⚡ Actions to Take</div>'
            f'{steps}</div>'
        )

    st.html(f"""
    <style>
    @keyframes dlgFadeIn {{
        from {{ transform:translateY(10px); opacity:0; }}
        to   {{ transform:translateY(0);   opacity:1; }}
    }}
    </style>
    <div style="font-family:'Poppins',sans-serif;
                animation:dlgFadeIn 0.3s cubic-bezier(.4,0,.2,1);">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;">
            <span style="background:#EFF6FF;color:#2563EB;padding:3px 9px;
                         border-radius:20px;font-size:0.62rem;font-weight:700;
                         letter-spacing:.5px;text-transform:uppercase;">
                📡 Status Check
            </span>
            <span style="font-size:0.57rem;font-weight:600;color:#9CA3AF;
                         text-transform:uppercase;letter-spacing:.06em;margin-left:auto;">
                Resolution Check
            </span>
        </div>
        <div style="font-size:0.88rem;font-weight:700;color:#111827;
                    margin-bottom:8px;line-height:1.4;">
            {notif["title"]}
        </div>
        <div style="font-size:0.65rem;color:#6B7280;display:flex;
                    flex-wrap:wrap;gap:10px;margin-bottom:12px;">
            <span>🌏 {notif["market"]}</span>
            <span>👤 Team Lead: {notif["team_lead"]}</span>
            <span>🕐 {notif["created_at"][:16].replace("T", " ")}</span>
        </div>
        {actions_html}
        <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;
                    padding:10px 12px;font-size:0.75rem;font-weight:600;color:#1D4ED8;
                    text-align:center;margin-bottom:4px;">
            Is this issue now resolved for you?
        </div>
    </div>
    """)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✓ Resolved", use_container_width=True, type="primary",
                     key=f"dlg_sc_res_{notif_id}"):
            add_resolution_response(inc_id, username, True)
            mark_notification_responded(username, inc_id)
            st.session_state.open_notif    = None
            st.session_state.responded_msg = "sc_resolved"
            st.rerun()
    with c2:
        if st.button("⚠ Still Impacted", use_container_width=True,
                     key=f"dlg_sc_still_{notif_id}"):
            add_resolution_response(inc_id, username, False)
            mark_notification_responded(username, inc_id)
            st.session_state.open_notif    = None
            st.session_state.responded_msg = "sc_still_impacted"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENT RESPONSE SECTION — main body response card for incidents
# ══════════════════════════════════════════════════════════════════════════════

def render_response_section(notif: dict):
    notif_type = notif.get("type", "new_incident")
    notif_id   = notif["notif_id"]
    username   = st.session_state.rev_username

    mark_notification_read(username, notif_id)

    # News alerts are handled by _show_news_dialog — this function is incident-only
    if notif_type == "news":
        _render_news_readonly(notif)
        return

    inc_id = notif["incident_id"]

    # ── Status Check ─────────────────────────────────────────────────────────
    if notif_type == "status_check":
        actions = notif.get("remediation_actions", [])
        actions_html = ""
        if actions:
            steps = "".join(
                f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:7px;">'
                f'<span style="min-width:18px;height:18px;background:#EDE9FE;color:#7C3AED;'
                f'border-radius:50%;font-size:0.58rem;font-weight:700;display:inline-flex;'
                f'align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;">{i+1}</span>'
                f'<span style="font-size:0.76rem;color:#374151;line-height:1.45;">{act}</span>'
                f'</div>'
                for i, act in enumerate(actions)
            )
            actions_html = (
                f'<div style="background:#FAF5FF;border:1px solid #DDD6FE;border-radius:8px;'
                f'padding:12px 14px;margin-bottom:14px;">'
                f'<div style="font-size:0.62rem;font-weight:700;color:#7C3AED;'
                f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
                f'⚡ Actions to Take</div>'
                f'{steps}</div>'
            )

        _, col, _ = st.columns([1, 2.2, 1])
        with col:
            st.html(f"""
            <div style="background:#fff;border:1px solid #BFDBFE;border-radius:14px;
                        padding:20px 20px 14px;box-shadow:0 4px 18px rgba(0,0,0,0.07);
                        font-family:'Poppins',sans-serif;margin-bottom:6px;">
                <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;">
                    <span style="background:#EFF6FF;color:#2563EB;padding:2px 8px;
                                 border-radius:20px;font-size:0.60rem;font-weight:700;
                                 letter-spacing:.5px;text-transform:uppercase;">
                        📡 Status Check
                    </span>
                    <span style="font-size:0.60rem;color:#6B7280;font-weight:600;
                                 text-transform:uppercase;letter-spacing:.06em;margin-left:auto;">
                        Resolution Check
                    </span>
                </div>
                <div style="font-size:0.88rem;font-weight:700;color:#111827;
                            margin-bottom:4px;line-height:1.4;">
                    {notif["title"]}
                </div>
                <div style="font-size:0.67rem;color:#6B7280;margin-bottom:12px;
                            display:flex;flex-wrap:wrap;gap:10px;">
                    <span>🌏 {notif["market"]}</span>
                    <span>👤 TL: {notif["team_lead"]}</span>
                    <span>🕐 {notif["created_at"][:16].replace("T", " ")}</span>
                </div>
                {actions_html}
                <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;
                            padding:10px 12px;font-size:0.75rem;font-weight:600;color:#1D4ED8;
                            text-align:center;margin-bottom:4px;">
                    Is this issue now resolved for you?
                </div>
            </div>
            """)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✓ Resolved", use_container_width=True, type="primary",
                             key=f"sc_res_{notif_id}"):
                    add_resolution_response(inc_id, username, True)
                    mark_notification_responded(username, inc_id)
                    st.session_state.open_notif    = None
                    st.session_state.responded_msg = "sc_resolved"
                    st.rerun()
            with c2:
                if st.button("⚠ Still Impacted", use_container_width=True,
                             key=f"sc_still_{notif_id}"):
                    add_resolution_response(inc_id, username, False)
                    mark_notification_responded(username, inc_id)
                    st.session_state.open_notif    = None
                    st.session_state.responded_msg = "sc_still_impacted"
                    st.rerun()
        return

    # ── New Incident ─────────────────────────────────────────────────────────
    severity        = notif.get("severity", "Unknown")
    sev_icon        = SEVERITY_ICONS.get(severity, "⚪")
    bg_col, txt_col = SEVERITY_COLORS.get(severity, ("#F3F4F6", "#6B7280"))

    _, col, _ = st.columns([1, 2.2, 1])
    with col:
        st.html(f"""
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:14px;
                    padding:20px 20px 14px;box-shadow:0 4px 18px rgba(0,0,0,0.07);
                    font-family:'Poppins',sans-serif;margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;">
                <span style="background:{bg_col};color:{txt_col};padding:2px 8px;
                             border-radius:20px;font-size:0.60rem;font-weight:700;
                             letter-spacing:.5px;text-transform:uppercase;">
                    {sev_icon} {severity}
                </span>
                <span style="font-size:0.60rem;color:#6B7280;font-weight:600;
                             text-transform:uppercase;letter-spacing:.06em;margin-left:auto;">
                    Action Required
                </span>
            </div>
            <div style="font-size:0.88rem;font-weight:700;color:#111827;
                        margin-bottom:4px;line-height:1.4;">
                {notif["title"]}
            </div>
            <div style="font-size:0.67rem;color:#6B7280;margin-bottom:12px;
                        display:flex;flex-wrap:wrap;gap:10px;">
                <span>🌏 {notif["market"]}</span>
                <span>👤 TL: {notif["team_lead"]}</span>
                <span>🕐 {notif["created_at"][:16].replace("T", " ")}</span>
            </div>
            <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;
                        padding:10px 12px;font-size:0.75rem;font-weight:600;color:#111827;
                        text-align:center;margin-bottom:4px;">
                Are you impacted by this incident?
            </div>
        </div>
        """)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("I'm Impacted", use_container_width=True, type="primary",
                         key=f"aff_{notif_id}"):
                add_response(inc_id, username, True)
                mark_notification_responded(username, inc_id)
                st.session_state.open_notif    = None
                st.session_state.responded_msg = "confirmed_impacted"
                st.rerun()
        with c2:
            if st.button("Not Impacted", use_container_width=True,
                         key=f"not_{notif_id}"):
                add_response(inc_id, username, False)
                mark_notification_responded(username, inc_id)
                st.session_state.open_notif    = None
                st.session_state.responded_msg = "confirmed_not_impacted"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# OVERFLOW INBOX DIALOG — interactive list for when >2 notifications are pending
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("Notification Inbox")
def _show_overflow_dialog(all_pending: list):
    """List every pending notification as a clickable row that opens the detail dialog."""
    st.caption(f"{len(all_pending)} notifications awaiting your response.")
    st.divider()
    for i, notif in enumerate(all_pending):
        ntype = notif.get("type", "new_incident")
        title = notif.get("title", "—")
        market = notif.get("market", "—")
        ts = notif.get("created_at", "")[:16].replace("T", " ")

        if ntype == "news":
            rl     = notif.get("risk_level", "Medium")
            icon   = "📢"
            sub    = f"News · {rl} Risk · {market} · {ts}"
        elif ntype == "status_check":
            icon   = "📡"
            sub    = f"Status Check · {market} · {ts}"
        else:
            sev    = notif.get("severity", "Unknown")
            icon   = SEVERITY_ICONS.get(sev, "⚪")
            sub    = f"Incident · {sev} · {market} · {ts}"

        col_txt, col_btn = st.columns([4, 1])
        with col_txt:
            st.markdown(f"**{icon} {title}**")
            st.caption(sub)
        with col_btn:
            if st.button("Open", key=f"ovf_open_{i}", type="primary"):
                st.session_state._pending_open_notif = notif
                st.rerun()

        if i < len(all_pending) - 1:
            st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN BODY
# ══════════════════════════════════════════════════════════════════════════════

def _dispatch_dialog(notif: dict):
    """Route a notification dict to the correct @st.dialog handler."""
    ntype = notif.get("type", "new_incident")
    if ntype == "news":
        _show_news_dialog(notif)
    elif ntype == "status_check":
        _show_status_check_dialog(notif)
    else:
        _show_incident_dialog(notif)


def render_body():
    username = st.session_state.rev_username or ""
    if not username:
        return

    # ── Response confirmation banner ──────────────────────────────────────────
    if st.session_state.responded_msg:
        msg = st.session_state.responded_msg
        if msg == "confirmed_impacted":
            st.success("Response submitted — marked as **Impacted**.")
        elif msg == "confirmed_not_impacted":
            st.success("Response submitted — marked as **Not Impacted**.")
        elif msg == "sc_resolved":
            st.success("Status Check submitted — marked as **Resolved**.")
        elif msg == "sc_still_impacted":
            st.info("Status Check submitted — marked as **Still Impacted**.")
        elif msg == "acknowledged_news":
            st.success("News alert acknowledged.")
        st.session_state.responded_msg = None

    pending = _pending(username)
    # Priority order: incidents and status checks first (more urgent), then news
    incident_pending = [n for n in pending if n.get("type") != "news"]
    news_pending     = [n for n in pending if n.get("type") == "news"]
    priority_pending = incident_pending + news_pending

    if not priority_pending:
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.html("""
            <div style="text-align:center;padding:50px 20px 36px;
                        font-family:'Poppins',sans-serif;">
                <div style="width:56px;height:56px;border-radius:50%;
                            background:linear-gradient(135deg,#F0FDF4,#DCFCE7);
                            border:2px solid #BBF7D0;
                            display:flex;align-items:center;justify-content:center;
                            font-size:1.5rem;margin:0 auto 16px;">✓</div>
                <div style="font-size:0.95rem;font-weight:700;color:#111827;
                            margin-bottom:6px;">
                    All Caught Up
                </div>
                <div style="font-size:0.72rem;color:#6B7280;line-height:1.6;">
                    No pending alerts require your response right now.<br>
                    You will be notified when a new alert is broadcasted.
                </div>
            </div>
            """)
        return

    # ── Slot assignments ──────────────────────────────────────────────────────
    slot0          = priority_pending[0]
    slot1          = priority_pending[1] if len(priority_pending) >= 2 else None
    overflow_count = max(0, len(priority_pending) - 2)

    # ── Hidden trigger buttons (invisible to user; clicked by iframe JS) ──────
    # Each uses a distinct Braille character so the JS can target them precisely.
    if st.button(_TRIG0, key="notif_trig_slot0"):
        st.session_state._slot0_triggered = slot0
    if slot1 is not None:
        if st.button(_TRIG1, key="notif_trig_slot1"):
            st.session_state._slot1_triggered = slot1
    if overflow_count > 0:
        if st.button(_TRIG2, key="notif_trig_overflow"):
            st.session_state._overflow_triggered = True

    # ── Dialog dispatch (elif chain — only one dialog may open per render) ────
    # Priority: inbox-routed open > slot 0 click > slot 1 click > overflow pill.
    pending_open = st.session_state.pop("_pending_open_notif", None)
    triggered0   = st.session_state.pop("_slot0_triggered",    None)
    triggered1   = st.session_state.pop("_slot1_triggered",    None)
    triggered_ov = st.session_state.pop("_overflow_triggered", False)

    if pending_open:
        _dispatch_dialog(pending_open)
    elif triggered0:
        _dispatch_dialog(triggered0)
    elif triggered1:
        _dispatch_dialog(triggered1)
    elif triggered_ov:
        _show_overflow_dialog(priority_pending)

    # ── Main body: read-only card for the primary (slot 0) notification ───────
    if slot0.get("type") == "news":
        _render_news_readonly(slot0)
    else:
        _render_incident_readonly(slot0)

    # ── Floating notification stack (bottom-right corner) ─────────────────────
    stack = [slot0] + ([slot1] if slot1 else [])
    render_notification_stack(stack, overflow_count=overflow_count)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT (called by app.py)
# ══════════════════════════════════════════════════════════════════════════════

def run_reviewer_portal():
    fix_sidebar_padding()
    st.html("""
<style>
section[data-testid="stMain"] {
    margin-left: var(--sidebar-w, 320px) !important;
    width: calc(100vw - var(--sidebar-w, 320px)) !important;
    max-width: calc(100vw - var(--sidebar-w, 320px)) !important;
}
[data-testid="stMainBlockContainer"],
.block-container {
    padding-top: 88px !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 100% !important;
}
</style>
""")
    for key, default in [
        ("rev_market",              MARKETS[0]),
        ("rev_username",            None),
        ("open_notif",              None),
        ("responded_msg",           None),
        ("popup_expanded",          False),
        ("incident_popup_expanded", None),
        ("navbar_open",             False),
        ("_slot0_triggered",        None),
        ("_slot1_triggered",        None),
        ("_overflow_triggered",     False),
        ("_pending_open_notif",     None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    if st.session_state.rev_username is None:
        first = MARKET_REVIEWERS.get(st.session_state.rev_market, [])
        if first:
            st.session_state.rev_username = first[0]

    render_navbar()
    render_sidebar()
    render_body()
    render_nav_dropdown()
