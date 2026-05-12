import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import sys, os, time, io, html as _html
import datetime as dt
import markdown as md_lib
from xhtml2pdf import pisa

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    MARKETS, LOCATIONS, FLOWS, METRICS, METRIC_CRITICALITY,
    MARKET_REVIEWERS, REVIEWER_FLOWS, SEVERITY_COLORS, SEVERITY_ICONS
)
from storage import (
    load_incidents, create_incident, get_incident,
    update_incident, add_response, broadcast_to_market,
    log_broadcast, load_broadcast_log,
    create_news_broadcast, broadcast_news_to_market, load_news_broadcasts,
    create_tl_account, authenticate_tl,
    get_impacted_now, log_rebroadcast, broadcast_status_check,
    update_broadcast_log_entries,
)
from agents.classification import classify_incident
from agents.news_classification import classify_news
from agents.impact import analyze_impact
from agents.report import generate_report
from styles import inject_styles, render_navbar, render_footer, fix_sidebar_padding, _logo_base64

# ── Page config ────────────────────────────────────────────────────────────────
_logo_img = Image.open(os.path.join(os.path.dirname(__file__), "Air.png"))
st.set_page_config(
    page_title="Incident Response System",
    page_icon=_logo_img,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

inject_styles()
render_footer()

# ── Session state init ─────────────────────────────────────────────────────────
for key, default in [
    ("role", None), ("username", None), ("tl_display_name", None),
    ("active_page", "incidents"), ("selected_incident_id", None),
    ("_news_result", None), ("auth_mode", "signin"),
    ("broadcast_policy_ack", False), ("impact_5plus", None),
    ("incidents_tab", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Restore session from URL params on refresh ─────────────────────────────────
def _restore_session():
    params = st.query_params
    if st.session_state.role is None and "role" in params:
        username = params.get("username", "")
        st.session_state.role               = params.get("role")
        st.session_state.username           = username
        st.session_state.tl_display_name    = params.get("display_name", "")
        st.session_state.active_page        = params.get("page", "incidents")
        st.session_state.incidents_tab      = int(params.get("tab", 0))
        st.session_state.broadcast_policy_ack = params.get("policy_ack") == "1"

def _save_session():
    if st.session_state.role:
        st.query_params["role"]         = st.session_state.role
        st.query_params["username"]     = st.session_state.username or ""
        st.query_params["display_name"] = st.session_state.tl_display_name or ""
        st.query_params["page"]         = st.session_state.active_page or "incidents"
        st.query_params["policy_ack"]   = "1" if st.session_state.get("broadcast_policy_ack") else "0"
    else:
        st.query_params.clear()

_restore_session()


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — UI Components
# ══════════════════════════════════════════════════════════════════════════════

def severity_badge(severity: str) -> str:
    cls_map = {
        "Critical": "badge-critical",
        "High":     "badge-high",
        "Medium":   "badge-medium",
        "Low":      "badge-low",
        "Unknown":  "badge-unknown",
    }
    dot_map = {
        "Critical": "●", "High": "●",
        "Medium": "●", "Low": "●", "Unknown": "●",
    }
    cls = cls_map.get(severity, "badge-unknown")
    dot = dot_map.get(severity, "●")
    return f'<span class="badge {cls}">{dot} {severity}</span>'


def page_header(title: str, subtitle: str = "") -> str:
    sub_html = f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ""
    return f"""
    <div class="page-header">
        <h1 class="page-title">{title}</h1>
        {sub_html}
    </div>
    """


def metric_card(value, label: str, variant: str = "accent") -> str:
    return f"""
    <div class="metric-card {variant}">
        <div class="metric-card-value">{value}</div>
        <div class="metric-card-label">{label}</div>
    </div>
    """


# ══════════════════════════════════════════════════════════════════════════════
# LANDING — Authentication (Sign In / Sign Up)
# ══════════════════════════════════════════════════════════════════════════════
def show_login():
    air_src = _logo_base64()

    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }

    /* ── Root cause fix: constrain height, kill Streamlit's phantom padding/scroll ──
       margin-top: 76px pushes the section below the fixed navbar (global styles set
       padding-top:0 / margin-top:0 on stMain; block-container's padding-top:78px was
       the only spacer — but we zero it for flex-centering, so we must shift the section
       itself down instead).
    ── */
    section[data-testid="stMain"] {
        margin-left: 0 !important;
        margin-top:  76px !important;
        width:       100vw !important;
        max-width:   100vw !important;
        height:      calc(100vh - 76px) !important;
        overflow:    hidden !important;
    }
    [data-testid="stMainBlockContainer"],
    .block-container {
        height:          100% !important;
        padding-top:     0 !important;
        padding-bottom:  0 !important;
        padding-left:    2rem !important;
        padding-right:   2rem !important;
        max-width:       100% !important;
        display:         flex !important;
        flex-direction:  column !important;
        justify-content: center !important;
    }

    /* ── Animations ── */
    @keyframes authFadeUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes authLogoFloat {
        from { transform: scale(0.80); opacity: 0; }
        to   { transform: scale(1);    opacity: 1; }
    }

    /* ── Auth card via :has() marker ── */
    [data-testid="stVerticalBlock"]:has(> .element-container #auth-card-marker) {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 18px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.10);
        padding: 26px 34px 22px !important;
        gap: 10px !important;
        animation: authFadeUp 0.4s cubic-bezier(0.4,0,0.2,1) both;
    }

    /* Hide the zero-content marker container so it takes no space */
    .element-container:has(#auth-card-marker) { display: none !important; }

    /* ── Logo ── */
    .auth-logo-wrap {
        text-align: center; margin-bottom: 8px;
        animation: authLogoFloat 0.45s cubic-bezier(0.4,0,0.2,1) 0.05s both;
    }
    .auth-air-logo { height: 34px; width: auto; object-fit: contain; display: inline-block; }

    /* ── Divider ── */
    .auth-divider { height: 1px; background: #E5E7EB; margin: 8px 0 4px; }

    /* ── Compact inputs & labels inside auth card ──
       Reduces Streamlit's default ~42px input height → ~32px.
       Safe for an internal tool; does not affect inputs on other pages. */
    [data-testid="stVerticalBlock"]:has(> .element-container #auth-card-marker) .stTextInput input {
        padding: 4px 10px !important;
        min-height: 32px !important;
        height: 32px !important;
        font-size: 0.81rem !important;
    }
    [data-testid="stVerticalBlock"]:has(> .element-container #auth-card-marker) .stTextInput label p {
        font-size: 0.73rem !important;
        margin-bottom: 3px !important;
        line-height: 1.3 !important;
    }
    /* Strip st.form's border/background — the card already provides the container.
       Target both the outer [data-testid="stForm"] AND its inner div child, which is
       where Streamlit actually applies the visible border and background.
       overflow:visible fixes the username input's bottom border being clipped. */
    [data-testid="stVerticalBlock"]:has(> .element-container #auth-card-marker) [data-testid="stForm"],
    [data-testid="stVerticalBlock"]:has(> .element-container #auth-card-marker) [data-testid="stForm"] > div {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
        overflow: visible !important;
    }
    /* Compact submit button */
    [data-testid="stVerticalBlock"]:has(> .element-container #auth-card-marker) [data-testid="stFormSubmitButton"] button {
        padding: 5px 12px !important;
        min-height: 34px !important;
        font-size: 0.82rem !important;
    }

    /* ── Notification banners (appear above form fields via st.empty slot) ── */
    .auth-msg {
        display: flex; align-items: center; gap: 8px;
        border-radius: 8px; padding: 8px 12px;
        font-size: 0.79rem; font-family: Poppins, sans-serif; font-weight: 500;
        animation: authFadeUp 0.28s ease both;
    }
    .auth-msg-error  { background: #FEF2F2; border: 1px solid #FECACA; color: #DC2626; }
    .auth-msg-success{ background: #F0FDF4; border: 1px solid #BBF7D0; color: #15803D; }
    .auth-msg-icon   { font-size: 1rem; flex-shrink: 0; }

    /* ── Footer ── */
    .ir-login-footer {
        position: fixed; bottom: 0; left: 0; right: 0;
        text-align: center; padding: 10px;
        font-size: 0.70rem; color: #9CA3AF;
        font-family: Poppins, sans-serif;
        border-top: 1px solid #F3F4F6; background: #FAFAFA;
    }
    </style>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        # Marker — CSS uses :has() on this to apply card styling to the column block
        st.markdown('<span id="auth-card-marker"></span>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="auth-logo-wrap">'
            f'<img src="{air_src}" class="auth-air-logo" alt="Air">'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Mode toggle (Sign In / Sign Up) ──────────────────────────────────
        mode = st.session_state.auth_mode
        tc1, tc2 = st.columns(2)
        with tc1:
            if st.button("Sign In", key="btn_mode_signin", use_container_width=True,
                         type="primary" if mode == "signin" else "secondary"):
                st.session_state.auth_mode = "signin"
                st.rerun()
        with tc2:
            if st.button("Sign Up", key="btn_mode_signup", use_container_width=True,
                         type="primary" if mode == "signup" else "secondary"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        st.markdown('<div class="auth-divider"></div>', unsafe_allow_html=True)

        # ── SIGN IN ──────────────────────────────────────────────────────────
        if mode == "signin":
            # Notification slot — created BEFORE the form so it renders above all fields
            msg = st.empty()

            with st.form("signin_form"):
                si_user = st.text_input("Username", placeholder="your username", key="si_user")
                si_pass = st.text_input("Password", placeholder="••••••••",
                                        type="password", key="si_pass")
                si_submit = st.form_submit_button("Sign In →", type="primary",
                                                  use_container_width=True)

            if si_submit:
                if not si_user.strip() or not si_pass:
                    msg.markdown(
                        '<div class="auth-msg auth-msg-error">'
                        '<span class="auth-msg-icon">⚠</span>Please fill in all fields.</div>',
                        unsafe_allow_html=True)
                else:
                    account = authenticate_tl(si_user.strip(), si_pass)
                    if account:
                        st.session_state.role                = "team_lead"
                        st.session_state.username            = account["username"]
                        st.session_state.tl_display_name     = account["display_name"]
                        st.session_state.active_page         = "incidents"
                        st.session_state.broadcast_policy_ack = False
                        st.session_state.impact_5plus         = None
                        _save_session()
                        st.rerun()
                    else:
                        msg.markdown(
                            '<div class="auth-msg auth-msg-error">'
                            '<span class="auth-msg-icon">⚠</span>Invalid username or password.</div>',
                            unsafe_allow_html=True)

        # ── SIGN UP ──────────────────────────────────────────────────────────
        else:
            # Notification slot — created BEFORE the form so it renders above all fields
            msg = st.empty()

            with st.form("signup_form"):
                su_name  = st.text_input("Display Name", placeholder="e.g. Sarah Lim", key="su_name")
                su_user  = st.text_input("Username", placeholder="e.g. sarah.lim", key="su_user")
                su_pass  = st.text_input("Password", placeholder="••••••••",
                                         type="password", key="su_pass")
                su_pass2 = st.text_input("Confirm Password", placeholder="••••••••",
                                         type="password", key="su_pass2")
                su_submit = st.form_submit_button("Create Account →", type="primary",
                                                  use_container_width=True)

            if su_submit:
                if not all([su_name.strip(), su_user.strip(), su_pass, su_pass2]):
                    msg.markdown(
                        '<div class="auth-msg auth-msg-error">'
                        '<span class="auth-msg-icon">⚠</span>Please fill in all fields.</div>',
                        unsafe_allow_html=True)
                elif su_pass != su_pass2:
                    msg.markdown(
                        '<div class="auth-msg auth-msg-error">'
                        '<span class="auth-msg-icon">⚠</span>Passwords do not match.</div>',
                        unsafe_allow_html=True)
                elif len(su_pass) < 6:
                    msg.markdown(
                        '<div class="auth-msg auth-msg-error">'
                        '<span class="auth-msg-icon">⚠</span>'
                        'Password must be at least 6 characters.</div>',
                        unsafe_allow_html=True)
                else:
                    account = create_tl_account(su_user.strip(), su_name.strip(), su_pass)
                    if account is None:
                        msg.markdown(
                            '<div class="auth-msg auth-msg-error">'
                            '<span class="auth-msg-icon">⚠</span>'
                            'Username already taken. Choose another.</div>',
                            unsafe_allow_html=True)
                    else:
                        msg.markdown(
                            '<div class="auth-msg auth-msg-success">'
                            '<span class="auth-msg-icon">✓</span>'
                            'Account created! Switch to Sign In to continue.</div>',
                            unsafe_allow_html=True)

    st.markdown("""
    <div class="ir-login-footer">
        Powered by AI Agents &nbsp;·&nbsp; Multi-Market Operations
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
_TL_SECTION_LABEL = (
    'font-size:0.62rem;font-weight:700;color:#111827;'
    'text-transform:uppercase;letter-spacing:0.1em;'
    'padding-bottom:8px;font-family:Poppins,sans-serif;'
)

def show_sidebar():
    display_name = st.session_state.tl_display_name or st.session_state.username or ""

    with st.sidebar:
        # ── Header ──────────────────────────────────────────
        st.markdown(
            '<div style="padding:24px 0 20px;border-bottom:1px solid #E5E7EB;">'
            '<div style="font-size:1.25rem;font-weight:700;color:#111827;'
            'text-align:left;font-family:Poppins,sans-serif;">Team Lead Portal</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── NAV SECTION (body) ──────────────────────────────
        with st.container():
            st.markdown(
                f'<div style="height:24px;"></div>'
                f'<div style="{_TL_SECTION_LABEL}">Main Menu</div>',
                unsafe_allow_html=True
            )
            active = st.session_state.active_page
            if st.button("🗂️  Incidents", use_container_width=True, key="nav_incidents"):
                st.session_state.active_page = "incidents"
                _save_session()
                st.rerun()
            if st.button("📈  Trends & News", use_container_width=True, key="nav_trends"):
                st.session_state.active_page = "trends"
                _save_session()
                st.rerun()

        # ── FOOTER SECTION ──────────────────────────────────
        with st.container():
            st.markdown(
                '<div style="height:1px;'
                'background:linear-gradient(to right,transparent,#D1D5DB 25%,#A100FF44 50%,#D1D5DB 75%,transparent);'
                'margin:32px 0 14px;border:none;"></div>',
                unsafe_allow_html=True
            )
            if st.button("← Logout", use_container_width=True, key="nav_logout"):
                for k in ["role", "username", "tl_display_name", "active_page", "selected_incident_id"]:
                    st.session_state[k] = None
                st.session_state.auth_mode = "signin"
                st.query_params.clear()
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TEAM LEAD — Create Incident
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("Dispatch Guidelines", dismissible=False)
def _broadcast_policy_dialog():
    st.markdown("""
    <div style="text-align:center;padding:8px 0 22px;font-family:'Poppins',sans-serif;">
        <div style="font-size:2rem;margin-bottom:10px;">📋</div>
        <div style="font-size:1rem;font-weight:700;color:#111827;">Incident Reporting Policy</div>
        <div style="font-size:0.72rem;color:#9CA3AF;margin-top:5px;">
            Review before proceeding</div>
    </div>
    <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:22px;
                font-family:'Poppins',sans-serif;">
        <div style="background:#FAF5FF;border-radius:8px;padding:13px 16px;">
            <div style="font-size:0.68rem;font-weight:700;color:#A100FF;
                        text-transform:uppercase;letter-spacing:0.07em;margin-bottom:5px;">
                📣 Broadcast</div>
            <div style="font-size:0.78rem;color:#374151;line-height:1.5;">
                Use when <strong>5 or more reviewers</strong> are impacted.
                Sends notifications to all selected markets.</div>
        </div>
        <div style="background:#F9FAFB;border-radius:8px;padding:13px 16px;">
            <div style="font-size:0.68rem;font-weight:700;color:#6B7280;
                        text-transform:uppercase;letter-spacing:0.07em;margin-bottom:5px;">
                📋 Log Only</div>
            <div style="font-size:0.78rem;color:#374151;line-height:1.5;">
                Use for low-impact issues. Recorded internally —
                no reviewer notifications sent.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Acknowledge", type="primary", use_container_width=True):
        st.session_state.broadcast_policy_ack = True
        _save_session()
        st.rerun()


@st.dialog("Confirm Broadcast")
def _confirm_broadcast_dialog():
    data     = st.session_state.get("_pending_broadcast", {})
    title    = data.get("title", "")
    task_no  = data.get("task_number", "")
    markets  = data.get("markets", [])
    flows    = data.get("flows", [])
    metric   = data.get("metric", "")

    inc_flows = set(flows)
    reviewers = list({
        r
        for mkt in markets
        for r in MARKET_REVIEWERS.get(mkt, [])
        if not inc_flows or any(f in inc_flows for f in REVIEWER_FLOWS.get(r, []))
    })

    markets_str = ", ".join(markets) if markets else "—"
    flows_str   = ", ".join(flows) if flows else "—"

    st.markdown(f"""
    <p style="color:var(--muted-text);font-size:0.875rem;margin-bottom:16px;">
        You are about to broadcast this incident to
        <strong style="color:var(--foreground);">{len(reviewers)} reviewers</strong>
        across <strong style="color:var(--foreground);">{len(markets)} market(s)</strong>.
        This action cannot be undone.
    </p>
    <div style="background:var(--muted);border:1px solid var(--border);border-radius:8px;
                padding:14px 16px;margin-bottom:20px;">
        <div style="font-size:11px;color:var(--muted-text);font-weight:700;
                    text-transform:uppercase;letter-spacing:0.07em;margin-bottom:6px;">
            Incident to Broadcast</div>
        <div style="font-size:0.9375rem;font-weight:600;color:var(--foreground);
                    line-height:1.4;">{title}</div>
        {"<div style='font-size:12px;color:var(--muted-text);margin-top:4px;'>Task No: " + task_no + "</div>" if task_no else ""}
        <div style='font-size:12px;color:var(--muted-text);margin-top:4px;'>Markets: {markets_str}</div>
        <div style='font-size:12px;color:var(--muted-text);margin-top:2px;'>Flows: {flows_str}</div>
        {"<div style='font-size:12px;color:var(--muted-text);margin-top:2px;'>Metric Impact: " + (", ".join(metric) if isinstance(metric, list) else metric) + "</div>" if metric else ""}
    </div>
    """, unsafe_allow_html=True)

    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            del st.session_state["_pending_broadcast"]
            st.rerun()
    with col_confirm:
        if st.button("Broadcast", type="primary", use_container_width=True):
            st.session_state["_broadcast_confirmed"] = True
            st.rerun()


def _field_label(text, key, errors, optional=False):
    """Render a field label — red + asterisk on error, muted optional tag."""
    is_err   = key in errors
    err_cls  = "ir-field-error" if is_err else ""
    suffix   = (
        f' <span style="color:#DC2626;font-weight:700;">*</span>'
        if not optional else
        ' <span style="color:#9CA3AF;font-size:12px;font-weight:400;">(optional)</span>'
    )
    st.markdown(
        f'<div class="{err_cls}" style="font-size:0.875rem;font-weight:500;'
        f'color:{"#DC2626" if is_err else "#111827"};margin-bottom:4px;line-height:1.4;">'
        f'{text}{suffix}</div>',
        unsafe_allow_html=True
    )


def _inject_field_errors(errors):
    """Apply red border to error fields — targets the exact element each field's CSS styles."""
    err_list = list(errors)
    components.html(f"""
        <script>
        (function() {{
            function redBorder(el) {{
                if (!el) return;
                el.style.setProperty('border-top',    '1px solid #DC2626', 'important');
                el.style.setProperty('border-right',  '1px solid #DC2626', 'important');
                el.style.setProperty('border-bottom', '1px solid #DC2626', 'important');
                el.style.setProperty('border-left',   '1px solid #DC2626', 'important');
                el.style.setProperty('border-radius', '6px', 'important');
                el.style.setProperty('box-shadow',    'none', 'important');
            }}

            function apply() {{
                var doc = window.parent.document;
                var errors = {err_list};

                /* text inputs — CSS border is on the <input> element itself */
                if (errors.indexOf('task_number') > -1)
                    redBorder(doc.querySelector('input[aria-label="Task Number"]'));

                if (errors.indexOf('title') > -1)
                    redBorder(doc.querySelector('input[placeholder="e.g. Job not loading in the dashboard"]'));

                /* date input — CSS border is on [data-baseweb="base-input"] */
                if (errors.indexOf('task_date') > -1)
                    redBorder(doc.querySelector('[data-testid="stDateInput"] [data-baseweb="base-input"]'));

                /* selectboxes — CSS border is on [data-baseweb="select"] > div */
                if (errors.indexOf('task_time') > -1) {{
                    doc.querySelectorAll('[data-testid="stForm"] label').forEach(function(lbl) {{
                        if (lbl.textContent.trim() === 'Hour' || lbl.textContent.trim() === 'Minute') {{
                            var box = lbl.closest('[data-testid="stSelectbox"]');
                            if (box) redBorder(box.querySelector('[data-baseweb="select"] > div'));
                        }}
                    }});
                }}

                /* metric impact multiselect */
                if (errors.indexOf('metric') > -1) {{
                    doc.querySelectorAll('[data-testid="stForm"] label').forEach(function(lbl) {{
                        if (lbl.textContent.trim() === 'Metric Impact') {{
                            var box = lbl.closest('[data-testid="stMultiSelect"]');
                            if (box) redBorder(box.querySelector('[data-baseweb="select"] > div'));
                        }}
                    }});
                }}
            }}

            apply();
            setTimeout(apply, 150);
            setTimeout(apply, 400);
        }})();
        </script>
    """, height=0, scrolling=False)


@st.dialog("Submitted Successfully", dismissible=True)
def _submission_success_dialog():
    info           = st.session_state.pop("_submission_success", {})
    kind           = info.get("kind", "broadcast")
    incident_id    = info.get("incident_id", "")
    title          = info.get("title", "")
    reviewer_count = info.get("reviewer_count", 0)
    markets        = info.get("markets", [])
    is_broadcast   = kind == "broadcast"

    st.markdown(f"""
    <style>
    @keyframes ir-pop {{
        0%   {{ transform: scale(0.4); opacity: 0; }}
        65%  {{ transform: scale(1.15); }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}
    .ir-success-icon {{ animation: ir-pop 0.45s cubic-bezier(.22,.68,0,1.2) both; }}
    </style>
    <div style="text-align:center;padding:10px 0 20px;font-family:'Poppins',sans-serif;">
        <div class="ir-success-icon" style="font-size:3rem;line-height:1;margin-bottom:10px;">✅</div>
        <div style="font-size:1.2rem;font-weight:700;color:var(--foreground);">
            {"Incident Broadcasted!" if is_broadcast else "Incident Logged!"}
        </div>
        <div style="font-size:0.83rem;color:var(--muted-text);margin-top:5px;">
            {"Reviewers have been notified." if is_broadcast else "Saved internally — no reviewers notified."}
        </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
        <div style="background:var(--muted);border:1px solid var(--border);border-radius:8px;
                    padding:12px;text-align:center;">
            <div style="font-size:10px;color:var(--muted-text);text-transform:uppercase;
                        letter-spacing:0.07em;margin-bottom:4px;">Incident ID</div>
            <div style="font-size:1.05rem;font-weight:700;color:var(--foreground);
                        font-family:'Courier New',monospace;">{incident_id}</div>
        </div>
        <div style="background:var(--muted);border:1px solid var(--border);border-radius:8px;
                    padding:12px;text-align:center;">
            <div style="font-size:10px;color:var(--muted-text);text-transform:uppercase;
                        letter-spacing:0.07em;margin-bottom:4px;">
                {"Reviewers Notified" if is_broadcast else "Status"}
            </div>
            <div style="font-size:1.05rem;font-weight:700;color:var(--foreground);">
                {str(reviewer_count) if is_broadcast else "Logged"}
            </div>
        </div>
    </div>
    {"" if not title else f'<div style="background:var(--muted);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:12px;"><div style="font-size:10px;color:var(--muted-text);text-transform:uppercase;letter-spacing:0.07em;margin-bottom:3px;">Title</div><div style="font-size:0.875rem;font-weight:600;color:var(--foreground);">{title}</div></div>'}
    {"" if not markets else f'<div style="font-size:0.78rem;color:var(--muted-text);text-align:center;margin-bottom:14px;">Markets: {", ".join(markets)}</div>'}
    """, unsafe_allow_html=True)

    if st.button("Done", type="primary", use_container_width=True, key="success_dlg_done"):
        st.rerun()


def page_tl_create():
    if "_submission_success" in st.session_state:
        _submission_success_dialog()

    errors = st.session_state.get("_form_errors", set())
    form_v = st.session_state.get("_form_version", 0)
    impact_5plus = st.session_state.get("impact_5plus")


    # ── Broadcast Impact Check ────────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:0.7rem;font-weight:700;color:#A100FF;text-transform:uppercase;
                letter-spacing:0.1em;margin-bottom:8px;font-family:Poppins,sans-serif;">
        Broadcast Impact Check</div>
    <div style="font-size:0.85rem;color:#374151;margin-bottom:12px;
                font-family:'Poppins',sans-serif;">
        Did this incident affect <strong>5 or more reviewers</strong>?</div>
    """, unsafe_allow_html=True)

    radio_index = None if impact_5plus is None else (0 if impact_5plus else 1)
    impact_choice = st.radio(
        "impact_q",
        options=["✓  Yes — 5 or more affected", "✕  No — fewer than 5"],
        index=radio_index,
        horizontal=True,
        key=f"impact_radio_{form_v}",
        label_visibility="collapsed",
    )
    if impact_choice is not None:
        impact_5plus = impact_choice.startswith("✓")
        st.session_state.impact_5plus = impact_5plus

    if impact_5plus is None:
        st.markdown('<p class="impact-hint impact-hint-none">Select an option above to enable the submit buttons.</p>', unsafe_allow_html=True)
    elif impact_5plus:
        st.markdown('<p class="impact-hint impact-hint-broadcast">📣 Broadcast will notify reviewers across selected markets.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="impact-hint impact-hint-log">📋 Log Only will record this incident without notifying reviewers.</p>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    with st.form(f"create_form_{form_v}", clear_on_submit=False):

        # ── Broadcast Targeting ─────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:0.7rem;font-weight:700;color:#A100FF;'
            'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;'
            'font-family:Poppins,sans-serif;">Broadcast Targeting</div>',
            unsafe_allow_html=True
        )

        loc_col, ms_col = st.columns(2)
        with loc_col:
            _field_label("Locations", "locations", errors)
            sel_locations = st.multiselect(
                "Locations", LOCATIONS, placeholder="Select locations…",
                label_visibility="collapsed", key="form_locations"
            )
        with ms_col:
            _field_label("Markets", "markets", errors)
            sel_markets = st.multiselect(
                "Markets", MARKETS, placeholder="Select markets…",
                label_visibility="collapsed", key="form_markets"
            )

        fl_col, mt_col = st.columns(2)
        with fl_col:
            _field_label("Flows", "flows", errors)
            sel_flows = st.multiselect(
                "Flows", FLOWS, placeholder="Select flows…",
                label_visibility="collapsed", key="form_flows"
            )
        with mt_col:
            _field_label("Metric Impact", "metric", errors)
            sel_metric = st.multiselect(
                "Metric Impact", METRICS, placeholder="Select metrics…",
                label_visibility="collapsed", key="form_metric"
            )

        st.markdown(
            '<div style="height:1px;background:#E5E7EB;margin:14px 0;"></div>',
            unsafe_allow_html=True
        )

        # ── Incident Details ────────────────────────────────────────────────
        tc1, tc2 = st.columns([1.2, 1])
        with tc1:
            _field_label("Task Number", "task_number", errors)
            task_number = st.text_input(
                "Task Number", placeholder="e.g. TASK-1042",
                label_visibility="collapsed"
            )
        with tc2:
            _field_label("Task Date", "task_date", errors)
            task_date = st.date_input(
                "Task Date", value=None, max_value=dt.date.today(),
                label_visibility="collapsed"
            )

        _field_label("Incident Start Time", "task_time", errors)
        th, tm, tap = st.columns([1, 1, 1])
        with th:
            task_hour = st.selectbox(
                "Hour", ["—"] + [f"{h:02d}" for h in range(1, 13)],
                label_visibility="collapsed"
            )
        with tm:
            task_min = st.selectbox(
                "Minute", ["—"] + [f"{m:02d}" for m in range(0, 60)],
                label_visibility="collapsed"
            )
        with tap:
            task_ampm = st.selectbox("AM/PM", ["AM", "PM"], label_visibility="collapsed")

        _field_label("Incident Title", "title", errors)
        title = st.text_input(
            "Incident Title", placeholder="e.g. Job not loading in the dashboard",
            label_visibility="collapsed"
        )

        _field_label("Description", "description", errors, optional=True)
        description = st.text_area(
            "Description",
            placeholder="Describe what's happening, which system, who is affected…",
            height=120, label_visibility="collapsed"
        )

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        _, btn_col1, btn_col2, _ = st.columns([1, 1.3, 1.3, 1])
        with btn_col1:
            submitted = st.form_submit_button(
                "📣  Broadcast", type="primary", use_container_width=True,
                disabled=(impact_5plus is not True)
            )
        with btn_col2:
            submitted_log = st.form_submit_button(
                "📋  Log Only", use_container_width=True,
                disabled=(impact_5plus is not False)
            )

    if errors:
        _inject_field_errors(errors)

    # Step 1 — validate
    if submitted:
        missing = set()
        if not task_number.strip():              missing.add("task_number")
        if not task_date:                        missing.add("task_date")
        if task_hour == "—" or task_min == "—": missing.add("task_time")
        if not title.strip():                    missing.add("title")
        if not sel_markets:                      missing.add("markets")
        if not sel_locations:                    missing.add("locations")
        if not sel_flows:                        missing.add("flows")
        if not sel_metric:                         missing.add("metric")

        if missing:
            st.session_state["_form_errors"] = missing
            st.rerun()
            return

        st.session_state.pop("_form_errors", None)
        task_time_str = (
            f"{task_date.strftime('%d %b %Y')} {task_hour}:{task_min} {task_ampm}"
            if task_date else f"{task_hour}:{task_min} {task_ampm}"
        )
        st.session_state["_pending_broadcast"] = {
            "task_number":   task_number,
            "task_time_str": task_time_str,
            "title":         title,
            "description":   description,
            "markets":       sel_markets,
            "locations":     sel_locations,
            "flows":         sel_flows,
            "metric":        sel_metric,
            "team_lead":     st.session_state.tl_display_name or st.session_state.username,
        }
        st.rerun()

    # Step 2 — confirmation dialog
    if "_pending_broadcast" in st.session_state and not st.session_state.get("_broadcast_confirmed"):
        _confirm_broadcast_dialog()

    # Step 3 — confirmed: run agents + broadcast
    if st.session_state.get("_broadcast_confirmed"):
        data      = st.session_state["_pending_broadcast"]
        markets   = data["markets"]
        metric    = data["metric"]
        team_lead = data["team_lead"]

        with st.spinner("Creating incident…"):
            incident = create_incident(
                data["title"], data["description"],
                markets, data["locations"], data["flows"], metric,
                team_lead,
                task_number=data["task_number"],
                task_time=data["task_time_str"],
            )

        with st.spinner("🤖 Classification Agent is analysing the incident…"):
            try:
                metrics_list = data.get("metric", [])
                metric_crits = [METRIC_CRITICALITY.get(m) for m in metrics_list]
                classification = classify_incident(
                    data["title"], data["description"],
                    metrics=metrics_list, metric_criticalities=metric_crits
                )
                update_incident(incident["id"], {"classification": classification})
                incident["classification"] = classification
                sev                 = classification.get("severity", "Unknown")
                category            = classification.get("category", "—")
                priority            = classification.get("priority", "—")
                reasoning           = classification.get("reasoning", "")
                remediation_actions = classification.get("remediation_actions", [])
                update_incident(incident["id"], {"remediation_actions": remediation_actions})
                incident["remediation_actions"] = remediation_actions
                st.markdown(f"""
                <div class="ai-card">
                    <div class="ai-card-label">🤖 AI Classification Result</div>
                    <div class="ai-stat-row">
                        <div class="ai-stat">
                            <div class="ai-stat-label">Category</div>
                            <div class="ai-stat-value">{category}</div>
                        </div>
                        <div class="ai-stat">
                            <div class="ai-stat-label">Severity</div>
                            <div class="ai-stat-value">{severity_badge(sev)}</div>
                        </div>
                        <div class="ai-stat">
                            <div class="ai-stat-label">Priority</div>
                            <div class="ai-stat-value">{priority}</div>
                        </div>
                    </div>
                    <div class="ai-reasoning">
                        <strong style="color:var(--foreground);">AI Reasoning</strong><br>
                        {reasoning}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Classification Agent error: {e}")

        # Gather reviewers matching both selected markets and selected flows
        _inc_flows = set(data.get("flows", []))
        reviewers = list({
            r
            for mkt in markets
            for r in MARKET_REVIEWERS.get(mkt, [])
            if not _inc_flows or any(f in _inc_flows for f in REVIEWER_FLOWS.get(r, []))
        })
        broadcast_to_market(incident, reviewers, update=False)
        log_broadcast(incident, reviewers, update=False)
        update_incident(incident["id"], {"last_broadcast_at": dt.datetime.now().isoformat()})
        st.session_state["_submission_success"] = {
            "kind":           "broadcast",
            "incident_id":    incident["id"],
            "title":          incident["title"],
            "reviewer_count": len(reviewers),
            "markets":        markets,
            "severity":       (incident.get("classification") or {}).get("severity", "Unknown"),
        }
        st.session_state["_form_version"] = form_v + 1
        st.session_state.impact_5plus = None
        st.session_state.pop("_pending_broadcast", None)
        st.session_state.pop("_broadcast_confirmed", None)
        st.session_state.pop("_form_errors", None)
        st.rerun()

    # Step 4 — Log Only: store incident without broadcasting
    if submitted_log:
        missing = set()
        if not task_number.strip():              missing.add("task_number")
        if not task_date:                        missing.add("task_date")
        if task_hour == "—" or task_min == "—": missing.add("task_time")
        if not title.strip():                    missing.add("title")
        if not sel_markets:                      missing.add("markets")
        if not sel_locations:                    missing.add("locations")
        if not sel_flows:                        missing.add("flows")
        if not sel_metric:                         missing.add("metric")

        if missing:
            st.session_state["_form_errors"] = missing
            st.rerun()
            return

        st.session_state.pop("_form_errors", None)
        task_time_str = (
            f"{task_date.strftime('%d %b %Y')} {task_hour}:{task_min} {task_ampm}"
            if task_date else f"{task_hour}:{task_min} {task_ampm}"
        )
        team_lead = st.session_state.tl_display_name or st.session_state.username

        with st.spinner("Logging incident internally…"):
            incident = create_incident(
                title, description, sel_markets, sel_locations, sel_flows, sel_metric,
                team_lead, task_number=task_number, task_time=task_time_str,
            )
            update_incident(incident["id"], {
                "log_only": True,
                "status":   "logged",
                "classification": {
                    "severity":  "Low",
                    "category":  "Operational",
                    "priority":  "Low",
                    "reasoning": "Logged without broadcast — fewer than 5 reviewers impacted.",
                },
            })

        st.session_state["_submission_success"] = {
            "kind":           "log",
            "incident_id":    incident["id"],
            "title":          incident["title"],
            "reviewer_count": 0,
            "markets":        sel_markets,
            "severity":       "Low",
        }
        st.session_state["_form_version"] = form_v + 1
        st.session_state.impact_5plus = None
        st.session_state.pop("_form_errors", None)
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TEAM LEAD — Incidents (table view)
# ══════════════════════════════════════════════════════════════════════════════

def _kpi_tile(col, value: str, label: str, accent: str, bg: str):
    """Render a KPI summary card inside a Streamlit column."""
    with col:
        st.markdown(
            f'<div class="ir-animate-in" style="background:{bg};border:1px solid #E5E7EB;'
            f'border-left:4px solid {accent};border-radius:10px;'
            f'padding:18px 22px 16px;box-shadow:0 1px 4px rgba(0,0,0,.05);">'
            f'<div style="font-size:30px;font-weight:800;color:#111827;line-height:1;">{value}</div>'
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.09em;margin-top:7px;color:{accent};">{label}</div>'
            f'</div>',
            unsafe_allow_html=True
        )


def _incident_status(inc: dict) -> str:
    """Derive display status from incident data."""
    if inc.get("log_only"):
        return "Logged"
    if inc.get("status") == "resolved":
        return "Resolved"
    responses  = inc.get("responses", {})
    yes_count  = sum(1 for v in responses.values() if v)
    total_resp = len(responses)
    sev = (inc.get("classification") or {}).get("severity", "Unknown")
    if total_resp == 0:
        return "Open"
    if sev in ("Critical", "High") and yes_count > 0:
        return "Critical Active"
    return "Under Review"


def _status_html(status: str) -> str:
    css_map = {
        "Open":           "ir-status ir-status-open",
        "Under Review":   "ir-status ir-status-under-review",
        "Critical Active":"ir-status ir-status-critical-active",
        "Resolved":       "ir-status ir-status-resolved",
        "Logged":         "ir-status ir-status-logged",
    }
    icon_map = {
        "Open":           "○",
        "Under Review":   "◔",
        "Critical Active":"●",
        "Resolved":       "✓",
        "Logged":         "📋",
    }
    cls  = css_map.get(status, "ir-status")
    icon = icon_map.get(status, "·")
    return f'<span class="{cls}">{icon} {status}</span>'


def page_tl_incidents():
    all_incidents = load_incidents()

    # ── KPI metrics (global) ──────────────────────────────────────────────────
    total      = len(all_incidents)
    logged_c   = sum(1 for i in all_incidents if i.get("log_only"))
    resolved_c = sum(1 for i in all_incidents if i.get("status") == "resolved")
    open_c     = total - resolved_c - logged_c
    critical_c = sum(
        1 for i in all_incidents
        if (i.get("classification") or {}).get("severity") == "Critical"
        and i.get("status") != "resolved" and not i.get("log_only")
    )

    k1, k2, k3, k4, k5 = st.columns(5, gap="small")
    _kpi_tile(k1, str(total),      "Total",           "#6B7280", "#F9FAFB")
    _kpi_tile(k2, str(open_c),     "Open",            "#EA580C", "#FFF7ED")
    _kpi_tile(k3, str(resolved_c), "Resolved",        "#16A34A", "#F0FDF4")
    _kpi_tile(k4, str(critical_c), "Critical Active", "#DC2626", "#FEF2F2")
    _kpi_tile(k5, str(logged_c),   "Logged Only",     "#6B7280", "#F3F4F6")

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    if not all_incidents:
        st.info("No incidents yet. Create one in the **Create Incident** tab.")
        return

    # ── Search + filters ──────────────────────────────────────────────────────
    f_search = st.text_input(
        "", placeholder="🔍  Search by title or task number…",
        key="inc_f_search", label_visibility="collapsed"
    )

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    filt1, filt2, filt3 = st.columns(3)
    with filt1:
        f_location = st.multiselect("Location", LOCATIONS, placeholder="All locations",
                                    key="inc_f_location", label_visibility="collapsed")
    with filt2:
        f_market = st.multiselect("Market", MARKETS, placeholder="All markets",
                                  key="inc_f_market", label_visibility="collapsed")
    with filt3:
        f_flow = st.multiselect("Flow", FLOWS, placeholder="All flows",
                                key="inc_f_flow", label_visibility="collapsed")

    filt4, filt5, filt6 = st.columns(3)
    with filt4:
        sev_present = [s for s in ["Critical", "High", "Medium", "Low", "Unknown"]
                       if any((i.get("classification") or {}).get("severity", "Unknown") == s
                              for i in all_incidents)]
        f_severity = st.selectbox("Severity", ["All"] + sev_present, key="inc_f_severity")
    with filt5:
        f_status = st.selectbox(
            "Status", ["All", "Open", "Under Review", "Critical Active", "Resolved", "Logged"],
            key="inc_f_status"
        )
    with filt6:
        DATE_OPTS = ["All", "Today", "Last 7 Days", "Last 30 Days"]
        f_date = st.selectbox("Date Range", DATE_OPTS, key="inc_f_date")

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    # ── Column proportions ────────────────────────────────────────────────────
    COL = [1.1, 1.5, 3.8, 1.7, 1.5, 1.8, 1.2]
    h1, h2, h3, h4, h5, h6, h7 = st.columns(COL, gap="small")

    def _plain_hdr(col_obj, label):
        with col_obj:
            st.markdown(
                f'<div class="ir-col-header">{label}</div>'
                f'<div style="height:8px;"></div>',
                unsafe_allow_html=True
            )

    _plain_hdr(h1, "Task #")
    _plain_hdr(h2, "Date & Time")
    _plain_hdr(h3, "Title")
    _plain_hdr(h4, "Markets")
    _plain_hdr(h5, "Severity")
    _plain_hdr(h6, "Status")
    _plain_hdr(h7, "Detail")

    st.markdown(
        '<hr style="margin:2px 0 10px;border:none;border-top:2px solid #E5E7EB;">',
        unsafe_allow_html=True
    )

    # Date cutoff logic
    today = dt.date.today()
    date_cutoffs = {
        "Today":       today,
        "Last 7 Days": today - dt.timedelta(days=7),
        "Last 30 Days":today - dt.timedelta(days=30),
    }

    # ── Apply filters ─────────────────────────────────────────────────────────
    today = dt.date.today()
    date_cutoffs = {
        "Today":        today,
        "Last 7 Days":  today - dt.timedelta(days=7),
        "Last 30 Days": today - dt.timedelta(days=30),
    }

    rows = []
    for inc in all_incidents:
        sev      = (inc.get("classification") or {}).get("severity", "Unknown")
        status   = _incident_status(inc)
        inc_id   = inc.get("id", "—")
        task_num = inc.get("task_number", inc_id)
        title    = inc.get("title", "")
        # Support both old (string) and new (list) market field
        inc_markets   = inc.get("markets", [inc.get("market", "")] if inc.get("market") else [])
        inc_flows     = inc.get("flows", [])
        inc_locations = inc.get("locations", [])

        if f_search:
            q = f_search.lower()
            if q not in title.lower() and q not in str(task_num).lower():
                continue

        if f_market and not any(m in inc_markets for m in f_market):
            continue
        if f_flow and not any(fl in inc_flows for fl in f_flow):
            continue
        if f_location and not any(loc in inc_locations for loc in f_location):
            continue
        if f_severity != "All" and sev != f_severity:
            continue
        if f_status != "All" and status != f_status:
            continue

        if f_date != "All":
            cutoff = date_cutoffs.get(f_date)
            if cutoff:
                dt_raw = inc.get("created_at", "")
                try:
                    inc_date = dt.date.fromisoformat(dt_raw[:10])
                except (ValueError, TypeError):
                    inc_date = None
                if inc_date is None or inc_date < cutoff:
                    continue

        rows.append(inc)

    # Default order: newest first
    rows.sort(key=lambda i: i.get("created_at", ""), reverse=True)

    # ── Incident rows ─────────────────────────────────────────────────────────
    if not rows:
        st.markdown(
            '<div style="text-align:center;padding:48px 20px;'
            'color:#9CA3AF;font-size:13px;">'
            'No incidents match the selected filters.</div>',
            unsafe_allow_html=True
        )
        return

    accent_map = {
        "Critical": "#DC2626",
        "High":     "#EA580C",
        "Medium":   "#D97706",
        "Low":      "#16A34A",
    }

    for inc in rows:
        cls      = inc.get("classification") or {}
        sev      = cls.get("severity", "Unknown")
        dt_raw   = inc.get("created_at", "")
        date_str = dt_raw[:10] if len(dt_raw) >= 10 else "—"
        time_str = dt_raw[11:16] if len(dt_raw) >= 16 else ""
        status   = _incident_status(inc)
        title    = inc.get("title", "—")
        inc_id   = inc.get("id", "—")
        task_num = inc.get("task_number", inc_id)
        row_accent = "#2563EB" if status == "Resolved" else accent_map.get(sev, "#9CA3AF")
        inc_markets = inc.get("markets", [inc.get("market", "")] if inc.get("market") else [])
        mkts_str = ", ".join(inc_markets) if inc_markets else "—"

        with st.container(border=True):
            r1, r2, r3, r4, r5, r6, r7 = st.columns(COL, gap="small")

            with r1:
                st.markdown(
                    f'<div style="border-left:3px solid {row_accent};'
                    f'padding:6px 4px 6px 8px;">'
                    f'<span class="ir-table-id">{task_num}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with r2:
                st.markdown(
                    f'<div style="padding:4px 2px;">'
                    f'<div style="font-size:12px;font-weight:600;color:#111827;">'
                    f'{date_str}</div>'
                    f'<div style="font-size:10px;color:#9CA3AF;margin-top:2px;">'
                    f'{time_str}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with r3:
                log_badge = (
                    '<span style="display:inline-block;background:#F3F4F6;color:#6B7280;'
                    'font-size:0.6rem;font-weight:700;text-transform:uppercase;'
                    'letter-spacing:0.06em;padding:1px 6px;border-radius:4px;'
                    'margin-left:6px;vertical-align:middle;">Log Only</span>'
                    if inc.get("log_only") else ""
                )
                st.markdown(
                    f'<div style="padding:4px 2px;font-size:12px;font-weight:600;'
                    f'color:#111827;white-space:nowrap;overflow:hidden;'
                    f'text-overflow:ellipsis;" title="{title}">'
                    f'{title}{log_badge}</div>',
                    unsafe_allow_html=True
                )
            with r4:
                st.markdown(
                    f'<div style="padding:4px 2px;font-size:11px;color:#374151;">'
                    f'{mkts_str}</div>',
                    unsafe_allow_html=True
                )
            with r5:
                st.markdown(
                    f'<div style="padding:4px 2px;">{severity_badge(sev)}</div>',
                    unsafe_allow_html=True
                )
            with r6:
                st.markdown(
                    f'<div style="padding:4px 2px;">{_status_html(status)}</div>',
                    unsafe_allow_html=True
                )
            with r7:
                if st.button("View →", key=f"view_{inc_id}",
                             use_container_width=True):
                    st.session_state.selected_incident_id = inc_id
                    st.session_state.active_page = "incident_detail"
                    _save_session()
                    st.rerun()

    st.markdown(
        f'<div style="padding:10px 2px 4px;font-size:11px;color:#9CA3AF;">'
        f'Showing {len(rows)} of {total} incidents</div>',
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# IMPACT ANALYTICS — market-scoped data visualization dashboard
# ══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    import plotly.graph_objects as go

    _SEV_COLORS = {
        "Critical": "#DC2626",
        "High":     "#EA580C",
        "Medium":   "#B45309",
        "Low":      "#16A34A",
        "Unknown":  "#6B7280",
    }
    _CHART_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Poppins, sans-serif"),
        height=300,
    )

    def _parse_dt(s: str) -> dt.datetime:
        return dt.datetime.fromisoformat(s.replace("Z", "").split("+")[0])

    # ── Filters ───────────────────────────────────────────────────────────────
    loc_col, mkt_col, tf_col, _ = st.columns([3, 3, 3, 1])
    with loc_col:
        dash_locations = st.multiselect(
            "Locations", LOCATIONS, placeholder="All locations",
            key="dashboard_locations", label_visibility="collapsed",
        )
    with mkt_col:
        dash_markets = st.multiselect(
            "Markets", MARKETS, placeholder="All markets",
            key="dashboard_markets", label_visibility="collapsed",
        )
    with tf_col:
        timeframe = st.selectbox(
            "Timeframe",
            ["Last 7 days", "Last 30 days", "All time"],
            key="dashboard_timeframe",
            label_visibility="collapsed",
        )

    now = dt.datetime.utcnow()
    if timeframe == "Last 7 days":
        cutoff = now - dt.timedelta(days=7)
    elif timeframe == "Last 30 days":
        cutoff = now - dt.timedelta(days=30)
    else:
        cutoff = None

    all_incidents = load_incidents()

    market_incidents = []
    for i in all_incidents:
        if cutoff and _parse_dt(i["created_at"]) < cutoff:
            continue
        if dash_locations:
            if not any(loc in i.get("locations", []) for loc in dash_locations):
                continue
        if dash_markets:
            inc_mkts = i.get("markets", [i.get("market", "")] if i.get("market") else [])
            if not any(m in inc_mkts for m in dash_markets):
                continue
        market_incidents.append(i)

    if not market_incidents:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:3rem;margin-bottom:16px;">📭</div>
            <div style="font-size:1rem;font-weight:600;color:var(--foreground);margin-bottom:8px;">
                No incidents in this timeframe</div>
            <div style="font-size:0.875rem;color:var(--muted-text);">
                Try selecting a wider timeframe or wait for new incidents.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    reviewer_count = sum(len(v) for v in MARKET_REVIEWERS.values())

    # ── Compute metrics ───────────────────────────────────────────────────────
    affected_users = sum(
        sum(1 for v in inc.get("responses", {}).values() if v)
        for inc in market_incidents
    )

    total_responses  = sum(len(inc.get("responses", {})) for inc in market_incidents)
    expected_responses = len(market_incidents) * reviewer_count
    response_rate = (
        round(total_responses / expected_responses * 100)
        if expected_responses > 0 else 0
    )

    needs_followup = sum(
        1 for inc in market_incidents
        if inc["status"] == "open"
        and sum(1 for v in inc.get("responses", {}).values() if v) == 0
    )

    # ── Metric cards ──────────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(metric_card(affected_users, "Affected Users", "critical"), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_card(f"{response_rate}%", "Response Rate", "resolved"), unsafe_allow_html=True)
    with m3:
        st.markdown(metric_card(needs_followup, "Needs Follow-up", "high"), unsafe_allow_html=True)

    st.markdown('<hr class="ir-divider">', unsafe_allow_html=True)

    # ── Row 1: Severity donut  +  Category horizontal bar ────────────────────
    row1_left, row1_right = st.columns(2, gap="large")

    with row1_left:
        st.markdown('<div class="section-label">Severity Distribution</div>', unsafe_allow_html=True)

        sev_counts: dict = {}
        for inc in market_incidents:
            sev = (inc.get("classification") or {}).get("severity", "Unknown")
            sev_counts[sev] = sev_counts.get(sev, 0) + 1

        labels = list(sev_counts.keys())
        values = list(sev_counts.values())

        fig_donut = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(
                colors=[_SEV_COLORS.get(l, "#6B7280") for l in labels],
                line=dict(color="#FFFFFF", width=2),
            ),
            textinfo="label+percent",
            textfont=dict(family="Poppins, sans-serif", size=11, color="#374151"),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            **_CHART_LAYOUT,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom", y=-0.25,
                xanchor="center", x=0.5,
                font=dict(family="Poppins, sans-serif", size=10, color="#374151"),
            ),
            margin=dict(l=10, r=10, t=10, b=50),
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    with row1_right:
        st.markdown('<div class="section-label">Incident Type Breakdown</div>', unsafe_allow_html=True)

        cat_counts: dict = {}
        for inc in market_incidents:
            cat = (inc.get("classification") or {}).get("category", "Uncategorized")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        sorted_cats  = sorted(cat_counts.items(), key=lambda x: x[1])
        cat_labels   = [c[0] for c in sorted_cats]
        cat_values   = [c[1] for c in sorted_cats]

        fig_cat = go.Figure(go.Bar(
            y=cat_labels,
            x=cat_values,
            orientation="h",
            marker=dict(
                color=cat_values,
                colorscale=[[0, "#D8B4FE"], [1, "#A100FF"]],
                showscale=False,
                line=dict(color="rgba(0,0,0,0)"),
            ),
            text=cat_values,
            textposition="outside",
            textfont=dict(family="Poppins, sans-serif", size=11, color="#374151"),
            hovertemplate="<b>%{y}</b><br>Incidents: %{x}<extra></extra>",
        ))
        fig_cat.update_layout(
            **_CHART_LAYOUT,
            xaxis=dict(
                showgrid=True, gridcolor="#F3F4F6", zeroline=False,
                tickfont=dict(family="Poppins, sans-serif", size=10, color="#6B7280"),
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(family="Poppins, sans-serif", size=11, color="#374151"),
            ),
            margin=dict(l=10, r=40, t=10, b=20),
        )
        st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<hr class="ir-divider">', unsafe_allow_html=True)

    # ── Row 2: Severity breakdown  +  Volume over time ───────────────────────
    row2_left, row2_right = st.columns(2, gap="large")

    with row2_left:
        st.markdown('<div class="section-label">Severity Breakdown</div>', unsafe_allow_html=True)

        severities  = ["Critical", "High", "Medium", "Low", "Unknown"]
        sev_counts  = [
            sum(
                1 for i in market_incidents
                if (i.get("classification") or {}).get("severity", "Unknown") == sev
            )
            for sev in severities
        ]
        sev_colors  = [_SEV_COLORS[s] for s in severities]

        fig_sev = go.Figure(go.Bar(
            x=severities,
            y=sev_counts,
            marker_color=sev_colors,
            hovertemplate="<b>%{x}</b><br>Incidents: %{y}<extra></extra>",
            showlegend=False,
        ))
        fig_sev.update_layout(
            **_CHART_LAYOUT,
            xaxis=dict(
                showgrid=False,
                tickfont=dict(family="Poppins, sans-serif", size=11, color="#374151"),
            ),
            yaxis=dict(
                showgrid=True, gridcolor="#F3F4F6", zeroline=False,
                tickfont=dict(family="Poppins, sans-serif", size=10, color="#6B7280"),
            ),
            margin=dict(l=10, r=10, t=10, b=40),
        )
        st.plotly_chart(fig_sev, use_container_width=True, config={"displayModeBar": False})

    with row2_right:
        st.markdown('<div class="section-label">Incident Volume Over Time</div>', unsafe_allow_html=True)

        date_counts: dict = {}
        for inc in market_incidents:
            date_str = inc["created_at"][:10]
            date_counts[date_str] = date_counts.get(date_str, 0) + 1

        sorted_dates  = sorted(date_counts.keys())
        volume_values = [date_counts[d] for d in sorted_dates]

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=sorted_dates,
            y=volume_values,
            marker=dict(color="#A100FF", opacity=0.25, line=dict(color="rgba(0,0,0,0)")),
            hovertemplate="<b>%{x}</b><br>Incidents: %{y}<extra></extra>",
            showlegend=False,
        ))
        fig_trend.add_trace(go.Scatter(
            x=sorted_dates,
            y=volume_values,
            mode="lines+markers",
            line=dict(color="#A100FF", width=2.5),
            marker=dict(color="#A100FF", size=7, line=dict(color="#FFFFFF", width=1.5)),
            hoverinfo="skip",
            showlegend=False,
        ))
        fig_trend.update_layout(
            **_CHART_LAYOUT,
            xaxis=dict(
                showgrid=False, tickangle=-15,
                tickfont=dict(family="Poppins, sans-serif", size=10, color="#374151"),
            ),
            yaxis=dict(
                showgrid=True, gridcolor="#F3F4F6", zeroline=False,
                tickfont=dict(family="Poppins, sans-serif", size=10, color="#6B7280"),
                title=dict(
                    text="Incidents",
                    font=dict(family="Poppins, sans-serif", size=10, color="#6B7280"),
                ),
            ),
            margin=dict(l=10, r=10, t=10, b=40),
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
# TEAM LEAD — Broadcast Log  (rebroadcast / resolve dialogs)
# ══════════════════════════════════════════════════════════════════════════════

@st.dialog("Edit Incident")
def _edit_incident_dialog():
    data     = st.session_state.get("_pending_edit", {})
    incident = data.get("incident", {})
    inc_id   = data.get("incident_id", "")

    st.markdown(
        '<p style="font-size:0.8rem;color:var(--muted-text);margin-bottom:16px;">'
        'Update the incident title or task number. Changes will appear in the broadcast log '
        'and in the next rebroadcast sent to reviewers.</p>',
        unsafe_allow_html=True,
    )

    new_title   = st.text_input("Title", value=incident.get("title", ""), max_chars=120)
    new_task_no = st.text_input("Task Number", value=incident.get("task_number", ""),
                                placeholder="e.g. TASK-1042")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    col_cancel, col_save = st.columns(2)
    with col_cancel:
        if st.button("Cancel", use_container_width=True, key="edit_dlg_cancel"):
            st.session_state.pop("_pending_edit", None)
            st.rerun()
    with col_save:
        if st.button("Save Changes", type="primary", use_container_width=True,
                     key="edit_dlg_save"):
            if not new_title.strip():
                st.error("Title cannot be empty.")
            else:
                tl_name = st.session_state.tl_display_name or st.session_state.username
                update_incident(inc_id, {
                    "title":           new_title.strip(),
                    "task_number":     new_task_no.strip(),
                    "last_edited_by":  tl_name,
                    "last_edited_at":  dt.datetime.now().isoformat(),
                })
                update_broadcast_log_entries(inc_id, {"incident_title": new_title.strip()})
                st.session_state.pop("_pending_edit", None)
                st.toast("✓ Incident updated successfully.")
                st.rerun()


@st.dialog("Send Status Check")
def _confirm_rebroadcast_dialog():
    data   = st.session_state.get("_pending_rebroadcast", {})
    count  = data.get("target_count", 0)
    title  = data.get("title", "")
    st.markdown(f"""
    <p style="color:var(--muted-text);font-size:0.875rem;margin-bottom:16px;">
        Re-notify <strong style="color:var(--foreground);">{count} impacted reviewer{"s" if count != 1 else ""}</strong>
        with a <strong style="color:var(--foreground);">Status Check</strong> — asking whether
        the issue is now resolved.
    </p>
    <div style="background:var(--muted);border:1px solid var(--border);border-radius:8px;
                padding:12px 16px;margin-bottom:20px;">
        <div style="font-size:11px;color:var(--muted-text);font-weight:700;
                    text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">
            Incident</div>
        <div style="font-size:0.9rem;font-weight:600;color:var(--foreground);">{title}</div>
        <div style="font-size:12px;color:var(--muted-text);margin-top:4px;">
            Only reviewers who previously reported impact will be notified.</div>
    </div>
    """, unsafe_allow_html=True)
    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancel", use_container_width=True, key="rb_dlg_cancel"):
            st.session_state.pop("_pending_rebroadcast", None)
            st.rerun()
    with col_confirm:
        if st.button("Send Status Check", type="primary", use_container_width=True,
                     key="rb_dlg_confirm"):
            st.session_state["_rebroadcast_confirmed"] = True
            st.rerun()


@st.dialog("Resolve Incident")
def _confirm_resolve_dialog():
    data   = st.session_state.get("_pending_resolve", {})
    inc_id = data.get("incident_id", "")
    title  = data.get("title", "")
    st.markdown(f"""
    <p style="color:var(--muted-text);font-size:0.875rem;margin-bottom:16px;">
        Mark this incident as <strong style="color:#16A34A;">Resolved</strong>?
        This will close it and disable further rebroadcasts.
    </p>
    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
                padding:12px 16px;margin-bottom:20px;">
        <div style="font-size:0.9rem;font-weight:600;color:#111827;">{title}</div>
    </div>
    """, unsafe_allow_html=True)
    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancel", use_container_width=True, key="res_dlg_cancel"):
            st.session_state.pop("_pending_resolve", None)
            st.rerun()
    with col_confirm:
        if st.button("✓ Mark Resolved", type="primary", use_container_width=True,
                     key="res_dlg_confirm"):
            update_incident(inc_id, {"status": "resolved"})
            st.session_state.pop("_pending_resolve", None)
            st.rerun()


def page_broadcast_log():
    st.markdown(
        '<p class="page-subtitle">Every notification dispatch sent to reviewers — live response tracking.</p>',
        unsafe_allow_html=True
    )

    all_log       = list(reversed(load_broadcast_log()))
    all_incidents = load_incidents()

    # ── Handle pending rebroadcast confirmation ───────────────────────────────
    if st.session_state.get("_rebroadcast_confirmed"):
        rb_data   = st.session_state.pop("_pending_rebroadcast", {})
        inc_id_rb = rb_data.get("incident_id", "")
        incident_rb = get_incident(inc_id_rb)
        if incident_rb:
            tl_name    = st.session_state.tl_display_name or st.session_state.username
            targets    = get_impacted_now(incident_rb)
            broadcast_status_check(incident_rb, targets)
            log_rebroadcast(inc_id_rb, targets, sent_by=tl_name)
        st.session_state.pop("_rebroadcast_confirmed", None)
        st.rerun()

    if not all_log:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:3rem;margin-bottom:16px;">📭</div>
            <div style="font-size:1rem;font-weight:600;color:var(--foreground);
                        margin-bottom:8px;">No broadcasts yet</div>
            <div style="font-size:0.875rem;color:var(--muted-text);">
                Create an incident and submit it — the broadcast will appear here.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Filters ───────────────────────────────────────────────────────────────
    bf0, bf1, bf2 = st.columns([1.2, 1.6, 1.2])
    with bf0:
        bl_locations = st.multiselect("Location", LOCATIONS, placeholder="All locations",
                                      key="bl_f_location", label_visibility="collapsed")
    with bf1:
        bl_markets = st.multiselect("Market", MARKETS, placeholder="All markets",
                                    key="bl_f_market", label_visibility="collapsed")
    with bf2:
        bl_status = st.selectbox(
            "Status", ["Open", "Resolved", "All"],
            index=0, key="bl_f_status", label_visibility="collapsed"
        )

    # Apply filters
    log = []
    for entry in all_log:
        e_markets   = entry.get("markets", [entry.get("market", "")] if entry.get("market") else [])
        e_locations = entry.get("locations", [])
        if bl_markets and not any(m in e_markets for m in bl_markets):
            continue
        if bl_locations and not any(loc in e_locations for loc in bl_locations):
            continue
        if bl_status != "All":
            inc = next((i for i in all_incidents if i["id"] == entry["incident_id"]), None)
            inc_s = (inc or {}).get("status", "open")
            if bl_status == "Open" and inc_s != "open":
                continue
            if bl_status == "Resolved" and inc_s != "resolved":
                continue
        log.append(entry)

    # ── Summary stats ─────────────────────────────────────────────────────────
    total_broadcasts  = len(log)
    total_notifs_sent = sum(e["reviewer_count"] for e in log)

    total_responded = 0
    total_reviewers = 0
    for entry in log:
        inc = next((i for i in all_incidents if i["id"] == entry["incident_id"]), None)
        responses = (inc or {}).get("responses", {})
        total_responded += len(responses)
        total_reviewers += entry.get("reviewer_count", 0)

    overall_response_rate = round(total_responded / total_reviewers * 100) if total_reviewers else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card(total_broadcasts, "Total Broadcasts", "primary"),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(total_notifs_sent, "Notifications Sent", "low"),
                    unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(f"{overall_response_rate}%", "Overall Response Rate", "high"),
                    unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card(len(all_log), "All Broadcasts (Global)", "resolved"),
                    unsafe_allow_html=True)

    st.markdown('<hr class="ir-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-label">Dispatch History</div>',
        unsafe_allow_html=True
    )

    # ── Per-broadcast cards ───────────────────────────────────────────────────
    _now_ts = dt.datetime.now()

    for idx, entry in enumerate(log):
        incident    = next((i for i in all_incidents if i["id"] == entry["incident_id"]), None)
        sev         = entry.get("severity", "Unknown")
        label       = entry.get("label", "NEW")
        label_cls   = "badge-new" if label == "NEW" else "badge-medium"
        ts          = entry["broadcast_at"][:16].replace("T", " at ")
        reviewers   = entry.get("reviewers", [])
        e_markets   = entry.get("markets", [entry.get("market", "")] if entry.get("market") else [])
        markets_str = ", ".join(e_markets) if e_markets else "—"
        e_locations = entry.get("locations", [])
        locs_str    = ", ".join(e_locations) if e_locations else "—"
        inc_id      = entry.get("incident_id", "")

        responses            = (incident or {}).get("responses", {})
        resolution_responses = (incident or {}).get("resolution_responses", {})
        resp_affected        = [u for u, v in responses.items() if v]
        resp_not_affected    = [u for u, v in responses.items() if not v]
        resp_total           = len(responses)
        resp_yes             = len(resp_affected)
        resp_no              = len(resp_not_affected)
        pending_count        = len([r for r in reviewers if r not in responses])
        resolved_count       = sum(1 for v in resolution_responses.values() if v)
        still_impacted_count = resp_yes - resolved_count

        pct_responded = round(resp_total / len(reviewers) * 100) if reviewers else 0

        inc_status = _incident_status(incident) if incident else "Unknown"
        status_dot = (
            "#16A34A" if inc_status == "Resolved"
            else "#DC2626" if inc_status == "Critical Active"
            else "#D97706"
        )

        # ── Rebroadcast eligibility ───────────────────────────────────────────
        impacted_now_list = get_impacted_now(incident) if incident else []
        is_resolved       = inc_status == "Resolved"
        is_log_only       = (incident or {}).get("log_only", False)
        can_edit          = not is_resolved and not is_log_only

        # Cooldown: 120s from last_broadcast_at (fallback to created_at)
        _last_bc = (incident or {}).get("last_broadcast_at") or (incident or {}).get("created_at", "")
        try:
            _last_bc_dt  = dt.datetime.fromisoformat(_last_bc[:26])
            _elapsed     = (_now_ts - _last_bc_dt).total_seconds()
            cooldown_rem = max(0, int(120 - _elapsed))
        except (ValueError, TypeError):
            cooldown_rem = 0

        can_rebroadcast = (
            not is_resolved
            and not is_log_only
            and len(impacted_now_list) > 0
            and cooldown_rem == 0
        )
        can_resolve = not is_resolved and not is_log_only

        rb_label = (
            f"📡  {cooldown_rem}s"
            if (not is_resolved and not is_log_only and len(impacted_now_list) > 0 and cooldown_rem > 0)
            else "📡  Rebroadcast"
        )

        # ── Reviewer pills (pending first, then responded; limit 6 visible) ──
        _PILL_LIMIT = 6
        sorted_reviewers = sorted(reviewers, key=lambda r: (r in responses, r.lower()))

        def _reviewer_pill(r: str) -> str:
            return (
                f'<span style="display:inline-flex;align-items:center;gap:5px;'
                f'background:var(--card-bg);border:1px solid var(--border);'
                f'border-radius:999px;padding:3px 9px;font-size:0.68rem;'
                f'color:var(--foreground);font-family:\'Poppins\',sans-serif;">'
                f'{"✅" if r in responses else "⏳"} {r} '
                f'{_flow_badge(REVIEWER_FLOWS.get(r, ["—"])[0])}'
                f'</span>'
            )

        visible_pills = "".join(_reviewer_pill(r) for r in sorted_reviewers[:_PILL_LIMIT])
        hidden_count  = len(sorted_reviewers) - _PILL_LIMIT

        if hidden_count > 0:
            hidden_pills = "".join(_reviewer_pill(r) for r in sorted_reviewers[_PILL_LIMIT:])
            reviewer_pills = (
                f'<style>details.rp-expand>summary{{list-style:none;cursor:pointer;}}'
                f'details.rp-expand>summary::-webkit-details-marker{{display:none;}}</style>'
                f'<div style="display:flex;flex-wrap:wrap;gap:5px;">{visible_pills}</div>'
                f'<details class="rp-expand" style="margin-top:6px;">'
                f'<summary style="font-size:0.65rem;color:var(--accent);font-weight:600;'
                f'font-family:Poppins,sans-serif;padding:2px 0;">'
                f'View more ({hidden_count})</summary>'
                f'<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:6px;">{hidden_pills}</div>'
                f'</details>'
            )
        else:
            reviewer_pills = f'<div style="display:flex;flex-wrap:wrap;gap:5px;">{visible_pills}</div>'

        # ── Rebroadcast history badge ─────────────────────────────────────────
        rb_history = (incident or {}).get("rebroadcast_history", [])
        history_html = ""
        if rb_history:
            history_html = (
                f'<span style="font-size:0.65rem;background:#FFF7ED;color:#EA580C;'
                f'border:1px solid #FED7AA;border-radius:4px;padding:1px 7px;'
                f'font-weight:700;font-family:Poppins,sans-serif;margin-left:6px;">'
                f'📡 {len(rb_history)}× rebroadcast</span>'
            )

        # ── Render: outer container, then header (cols), then body (HTML) ─────
        with st.container(border=True):
            # Header row
            hcol, acol = st.columns([3.2, 2.2])
            with hcol:
                st.markdown(
                    f'<div style="padding:6px 2px 2px;">'
                    f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">'
                    f'<span style="font-size:0.68rem;font-weight:700;color:var(--muted-text);'
                    f'font-family:Poppins,sans-serif;letter-spacing:0.07em;'
                    f'background:var(--muted);padding:2px 8px;border-radius:4px;">'
                    f'{inc_id}</span>'
                    f'{severity_badge(sev)}'
                    f'<span class="badge {label_cls}">{label}</span>'
                    f'{history_html}'
                    f'<span style="display:inline-flex;align-items:center;gap:5px;'
                    f'font-size:0.7rem;color:var(--muted-text);font-family:Poppins,sans-serif;">'
                    f'<span style="width:7px;height:7px;border-radius:50%;'
                    f'background:{status_dot};display:inline-block;"></span>'
                    f'{inc_status}</span>'
                    f'<span style="font-size:0.72rem;color:var(--muted-text);'
                    f'font-family:Poppins,sans-serif;">🕒 {ts} &nbsp;·&nbsp; 📍 {locs_str}</span>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
            with acol:
                btn_edit, btn_rb, btn_res = st.columns([0.8, 1.2, 1.2])
                with btn_edit:
                    if st.button(
                        "✏️", key=f"edit_{inc_id}_{idx}",
                        use_container_width=True,
                        disabled=not can_edit,
                        help="Edit title / task number",
                    ):
                        st.session_state["_pending_edit"] = {
                            "incident_id": inc_id,
                            "incident":    incident or {},
                        }
                        st.rerun()
                with btn_rb:
                    if st.button(
                        rb_label, key=f"rb_{inc_id}_{idx}",
                        use_container_width=True,
                        disabled=not can_rebroadcast,
                    ):
                        st.session_state["_pending_rebroadcast"] = {
                            "incident_id":  inc_id,
                            "title":        entry.get("incident_title", ""),
                            "target_count": len(impacted_now_list),
                        }
                        st.rerun()
                with btn_res:
                    if st.button(
                        "✓  Resolve", key=f"res_{inc_id}_{idx}",
                        use_container_width=True,
                        disabled=not can_resolve,
                        type="primary" if can_resolve else "secondary",
                    ):
                        st.session_state["_pending_resolve"] = {
                            "incident_id": inc_id,
                            "title":       entry.get("incident_title", ""),
                        }
                        st.rerun()

            # Incident title + sender
            _edited_by = (incident or {}).get("last_edited_by")
            _edited_at = (incident or {}).get("last_edited_at", "")
            _edited_ts = _edited_at[:16].replace("T", " at ") if _edited_at else ""
            _audit_html = (
                f'<div style="font-size:0.68rem;color:var(--muted-text);'
                f'font-family:Poppins,sans-serif;margin-top:3px;'
                f'display:flex;align-items:center;gap:4px;">'
                f'<span style="opacity:0.6;">✏</span>'
                f'<span>Edited by <strong style="color:var(--foreground);">{_edited_by}</strong>'
                f' · {_edited_ts}</span></div>'
                if _edited_by else ""
            )
            st.markdown(
                f'<div style="padding:2px 2px 10px;">'
                f'<div style="font-size:0.95rem;font-weight:600;color:var(--foreground);'
                f'margin-bottom:2px;font-family:\'Poppins\',sans-serif;">'
                f'{entry["incident_title"]}</div>'
                f'{_audit_html}'
                f'<div style="font-size:0.78rem;color:var(--muted-text);'
                f'font-family:\'Poppins\',sans-serif;display:flex;align-items:center;'
                f'flex-wrap:wrap;gap:6px;margin-top:4px;">'
                f'Sent by <strong style="color:var(--foreground);">{entry["team_lead"]}</strong>'
                f'&nbsp;·&nbsp; {len(reviewers)} reviewers notified &nbsp;·&nbsp;'
                + "".join(
                    f'<span style="font-size:0.65rem;font-weight:700;'
                    f'background:var(--muted);border:1px solid var(--border);'
                    f'border-radius:4px;padding:1px 7px;color:var(--muted-text);'
                    f'font-family:Poppins,sans-serif;letter-spacing:0.03em;">{m}</span>'
                    for m in e_markets
                )
                + f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # ── 4-stat row ────────────────────────────────────────────────────
            _total_notified = len(reviewers) if reviewers else 1
            _pct_imp  = round(resp_yes      / _total_notified * 100)
            _pct_res  = round(resolved_count / _total_notified * 100)
            _pct_no   = round(resp_no        / _total_notified * 100)
            _pct_pend = round(pending_count  / _total_notified * 100)
            st.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;'
                f'margin-bottom:14px;">'
                # Impacted
                f'<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;'
                f'padding:10px 12px;text-align:center;">'
                f'<div style="font-size:1.3rem;font-weight:800;color:#D97706;line-height:1;">'
                f'{resp_yes}</div>'
                f'<div style="font-size:0.65rem;color:#D97706;margin-top:2px;">{_pct_imp}%</div>'
                f'<div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:#D97706;margin-top:3px;'
                f'font-family:Poppins,sans-serif;">Impacted</div></div>'
                # Resolved
                f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;'
                f'padding:10px 12px;text-align:center;">'
                f'<div style="font-size:1.3rem;font-weight:800;color:#2563EB;line-height:1;">'
                f'{resolved_count}</div>'
                f'<div style="font-size:0.65rem;color:#2563EB;margin-top:2px;">{_pct_res}%</div>'
                f'<div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:#2563EB;margin-top:3px;'
                f'font-family:Poppins,sans-serif;">Resolved</div></div>'
                # Not Impacted
                f'<div style="background:#F3F4F6;border:1px solid #E5E7EB;border-radius:8px;'
                f'padding:10px 12px;text-align:center;">'
                f'<div style="font-size:1.3rem;font-weight:800;color:#6B7280;line-height:1;">'
                f'{resp_no}</div>'
                f'<div style="font-size:0.65rem;color:#6B7280;margin-top:2px;">{_pct_no}%</div>'
                f'<div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:#6B7280;margin-top:3px;'
                f'font-family:Poppins,sans-serif;">Not Impacted</div></div>'
                # Pending
                f'<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;'
                f'padding:10px 12px;text-align:center;">'
                f'<div style="font-size:1.3rem;font-weight:800;color:#9CA3AF;line-height:1;">'
                f'{pending_count}</div>'
                f'<div style="font-size:0.65rem;color:#9CA3AF;margin-top:2px;">{_pct_pend}%</div>'
                f'<div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:#9CA3AF;margin-top:3px;'
                f'font-family:Poppins,sans-serif;">Pending</div></div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # ── Split progress bar (impacted breakdown) ───────────────────────
            if resp_yes > 0:
                resolved_pct      = round(resolved_count / resp_yes * 100)
                still_imp_pct     = round(still_impacted_count / resp_yes * 100)
                pct_responded_bar = pct_responded
                st.markdown(
                    f'<div style="margin-bottom:14px;">'
                    f'<div style="font-size:0.65rem;color:var(--muted-text);'
                    f'font-family:Poppins,sans-serif;margin-bottom:5px;">'
                    f'Of impacted — '
                    f'<span style="color:#2563EB;font-weight:600;">{resolved_count} resolved</span> · '
                    f'<span style="color:#D97706;font-weight:600;">{still_impacted_count} still impacted</span>'
                    f'</div>'
                    f'<div style="background:#F3F4F6;border-radius:999px;height:7px;'
                    f'overflow:hidden;display:flex;">'
                    f'<div style="height:100%;background:#2563EB;width:{resolved_pct}%;'
                    f'transition:width 0.6s ease;"></div>'
                    f'<div style="height:100%;background:#D97706;width:{still_imp_pct}%;'
                    f'transition:width 0.6s ease;"></div>'
                    f'</div>'
                    f'<div style="font-size:0.65rem;color:var(--muted-text);'
                    f'font-family:Poppins,sans-serif;margin-top:5px;">'
                    f'Overall response rate — {resp_total}/{len(reviewers)} ({pct_responded}%)'
                    f'</div></div>',
                    unsafe_allow_html=True
                )

            # ── Delivered To + Flow Breakdown ─────────────────────────────────
            st.markdown(
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">'
                f'<div style="background:var(--muted);border:1px solid var(--border);'
                f'border-radius:10px;padding:12px 14px;">'
                f'<div style="font-size:0.65rem;font-weight:700;color:var(--accent);'
                f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'
                f'font-family:Poppins,sans-serif;">📬 Delivered To</div>'
                f'{reviewer_pills}'
                f'</div>'
                f'<div style="background:var(--muted);border:1px solid var(--border);'
                f'border-radius:10px;padding:12px 14px;">'
                f'<div style="font-size:0.65rem;font-weight:700;color:var(--muted-text);'
                f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;'
                f'font-family:Poppins,sans-serif;">📊 Flow Breakdown</div>'
                + _flow_breakdown_rows_html(reviewers, responses, resolution_responses) +
                f'</div></div>',
                unsafe_allow_html=True
            )

            st.markdown("<div style='height:2px;'></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── Trigger dialogs ───────────────────────────────────────────────────────
    if "_pending_edit" in st.session_state:
        _edit_incident_dialog()
    if "_pending_rebroadcast" in st.session_state and not st.session_state.get("_rebroadcast_confirmed"):
        _confirm_rebroadcast_dialog()
    if "_pending_resolve" in st.session_state:
        _confirm_resolve_dialog()


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENTS HUB — tabs on top of body
# ══════════════════════════════════════════════════════════════════════════════
def page_incidents():
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝  Create Incident",
        "📡  Broadcast Log",
        "📋  All Incidents",
        "📊  Impact Analytics",
    ])

    target_tab = st.session_state.get("incidents_tab", 0)
    if target_tab > 0:
        st.session_state.incidents_tab = 0
        components.html(f"""<script>
        setTimeout(function() {{
            var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
            if (tabs.length > {target_tab}) tabs[{target_tab}].click();
        }}, 120);
        </script>""", height=0)

    with tab1: page_tl_create()
    with tab2: page_broadcast_log()
    with tab3: page_tl_incidents()
    with tab4: page_dashboard()


# ══════════════════════════════════════════════════════════════════════════════
# TRENDS & NEWS PAGE
# ══════════════════════════════════════════════════════════════════════════════
_NEWS_RL_BG = {"Critical": "#FEF2F2", "High": "#FFF7ED", "Medium": "#FFFBEB", "Low": "#F0FDF4"}
_NEWS_RL_FG = {"Critical": "#DC2626", "High": "#EA580C", "Medium": "#B45309", "Low": "#16A34A"}


def _page_news_broadcast():
    username = st.session_state.username
    tl_name  = st.session_state.tl_display_name or username

    # ── Success banner ────────────────────────────────────────────────────────
    if st.session_state.get("_news_result"):
        result = st.session_state._news_result
        cls    = result.get("classification", {})
        rl     = cls.get("risk_level", "Medium")
        cat    = cls.get("category", "Other")
        rsn    = cls.get("reasoning", "")
        count  = result.get("reviewer_count", 0)
        mkts   = result.get("markets", [])
        bg     = _NEWS_RL_BG.get(rl, "#F3F4F6")
        fg     = _NEWS_RL_FG.get(rl, "#6B7280")
        st.markdown(f"""
        <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;
                    padding:18px 22px;margin-bottom:24px;font-family:'Poppins',sans-serif;
                    animation:fadeInDown 0.4s ease;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <span style="font-size:1rem;">✅</span>
                <span style="font-size:0.9rem;font-weight:700;color:#15803D;">
                    Broadcasted to {count} reviewer{"s" if count != 1 else ""} across {", ".join(mkts)}
                </span>
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                <span style="background:{bg};color:{fg};padding:2px 10px;border-radius:20px;
                             font-size:0.68rem;font-weight:700;text-transform:uppercase;
                             letter-spacing:0.5px;">⚡ {rl} Risk</span>
                <span style="background:#F3F4F6;color:#374151;padding:2px 10px;border-radius:20px;
                             font-size:0.68rem;font-weight:600;">{cat}</span>
                <span style="font-size:0.78rem;color:#6B7280;">{rsn}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state._news_result = None

    # ── Section header ────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-label" style="margin-bottom:6px;">Broadcast News Alert</div>'
        '<div style="font-size:0.8rem;color:#6B7280;font-family:Poppins,sans-serif;'
        'margin-bottom:20px;">Alert reviewers about a high-risk event. '
        'Risk level and category are auto-assessed by AI.</div>',
        unsafe_allow_html=True,
    )

    # ── Form ──────────────────────────────────────────────────────────────────
    with st.form("news_broadcast_form", clear_on_submit=True):
        title = st.text_input(
            "Alert Title",
            placeholder="e.g. Regulatory change affecting reporting deadlines",
        )
        description = st.text_area(
            "Details",
            placeholder="Briefly describe the event, its impact, and any immediate actions required…",
            height=120,
        )
        news_markets = st.multiselect(
            "Target Markets", MARKETS, placeholder="Select markets to broadcast to…"
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        _, btn_col, _ = st.columns([2, 1.6, 2])
        with btn_col:
            submitted = st.form_submit_button(
                "Analyse & Broadcast", type="primary", use_container_width=True,
            )

    if submitted:
        t = title.strip()
        d = description.strip()
        if not t or not d or not news_markets:
            st.error("Title, details, and at least one target market are required.")
        else:
            reviewers = list({r for mkt in news_markets for r in MARKET_REVIEWERS.get(mkt, [])})
            with st.spinner("Analysing risk level and broadcasting to reviewers…"):
                try:
                    cls = classify_news(t, d)
                except Exception:
                    cls = {"risk_level": "Medium", "category": "Other",
                           "reasoning": "Classification unavailable."}
                # Store market as comma-joined string for backwards compat
                news = create_news_broadcast(t, d, ", ".join(news_markets), tl_name, cls)
                broadcast_news_to_market(news, reviewers)
                st.session_state._news_result = {
                    "classification": cls,
                    "reviewer_count": len(reviewers),
                    "markets":        news_markets,
                }
                st.rerun()

    # ── Recent broadcasts ─────────────────────────────────────────────────────
    all_news    = load_news_broadcasts()
    market_news = list(reversed(all_news))

    st.markdown('<hr class="ir-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Recent Broadcasts</div>', unsafe_allow_html=True)

    if not market_news:
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#6B7280;
                    font-size:0.85rem;font-family:'Poppins',sans-serif;">
            No news broadcasts yet.
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, item in enumerate(market_news[:10]):
            cls        = item.get("classification") or {}
            rl         = cls.get("risk_level", "Medium")
            cat        = cls.get("category", "Other")
            bg         = _NEWS_RL_BG.get(rl, "#F3F4F6")
            fg         = _NEWS_RL_FG.get(rl, "#6B7280")
            ack        = len(item.get("acknowledged_by", []))
            ts         = item["created_at"][:16].replace("T", " at ")
            desc       = item.get("description", "")
            desc_short = (desc[:120] + "…") if len(desc) > 120 else desc

            st.markdown(f"""
            <div class="incident-row" style="animation-delay:{idx * 0.04}s;">
                <div style="width:100%;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        <span style="background:{bg};color:{fg};padding:2px 9px;border-radius:20px;
                                     font-size:0.65rem;font-weight:700;text-transform:uppercase;
                                     letter-spacing:0.4px;">⚡ {rl}</span>
                        <span style="background:#F3F4F6;color:#374151;padding:2px 9px;
                                     border-radius:20px;font-size:0.65rem;font-weight:600;">{cat}</span>
                        <span style="font-size:0.65rem;color:#9CA3AF;">📍 {item.get("market","")}</span>
                    </div>
                    <div style="font-size:0.875rem;font-weight:600;color:#111827;
                                margin-bottom:4px;line-height:1.4;">{item["title"]}</div>
                    <div style="font-size:0.76rem;color:#6B7280;margin-bottom:6px;
                                line-height:1.5;">{desc_short}</div>
                    <div style="font-size:0.73rem;color:#9CA3AF;display:flex;gap:14px;">
                        <span>🕐 {ts}</span>
                        <span>✓ {ack} acknowledged</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)


def _page_trends_content():
    import plotly.graph_objects as go

    all_news    = load_news_broadcasts()
    market_news = all_news  # show all markets

    # ── Empty state ───────────────────────────────────────────────────────────
    if not market_news:
        st.markdown(f"""
        <div style="text-align:center;padding:80px 20px;">
            <div style="font-size:3rem;margin-bottom:16px;">📰</div>
            <div style="font-size:1rem;font-weight:600;color:#111827;margin-bottom:8px;">
                No news alerts broadcast yet</div>
            <div style="font-size:0.875rem;color:#6B7280;font-family:'Poppins',sans-serif;">
                Switch to the Broadcast tab to send the first news alert
                to <strong style="color:#111827;">{market}</strong> reviewers.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _time_ago(iso_str: str) -> str:
        try:
            ts   = dt.datetime.fromisoformat(iso_str.replace("Z", "").split("+")[0])
            diff = dt.datetime.now() - ts
            secs = int(diff.total_seconds())
            if secs < 60:    return "Just now"
            if secs < 3600:  return f"{secs // 60}m ago"
            if secs < 86400: return f"{secs // 3600}h ago"
            return f"{diff.days}d ago"
        except Exception:
            return "—"

    # ── Compute metrics ───────────────────────────────────────────────────────
    total_alerts    = len(market_news)
    high_risk_count = sum(
        1 for n in market_news
        if (n.get("classification") or {}).get("risk_level") in ("High", "Critical")
    )
    total_acks     = sum(len(n.get("acknowledged_by", [])) for n in market_news)
    latest_ts      = max((n["created_at"] for n in market_news), default=None)
    last_alert_str = _time_ago(latest_ts) if latest_ts else "—"
    acks_display   = str(total_acks)

    # ── 4 metric cards ────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric_card(total_alerts,    "Total Alerts Sent",        "primary"),  unsafe_allow_html=True)
    with c2: st.markdown(metric_card(high_risk_count, "High-Risk Alerts",         "critical"), unsafe_allow_html=True)
    with c3: st.markdown(metric_card(acks_display,    "Reviewer Acknowledgements","resolved"), unsafe_allow_html=True)
    with c4: st.markdown(metric_card(last_alert_str,  "Last Alert Sent",          "accent"),   unsafe_allow_html=True)

    st.markdown('<hr class="ir-divider">', unsafe_allow_html=True)

    # ── 2-column layout: categories (left) + risk donut (right) ──────────────
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.markdown('<div class="section-label">News Alert Categories</div>', unsafe_allow_html=True)

        # Tally categories, track highest risk per category
        cat_map: dict = {}
        _rl_order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
        for n in market_news:
            cls = n.get("classification") or {}
            cat = cls.get("category", "Other")
            rl  = cls.get("risk_level", "Medium")
            if cat not in cat_map:
                cat_map[cat] = {"count": 0, "highest": "Low"}
            cat_map[cat]["count"] += 1
            if _rl_order.get(rl, 0) > _rl_order.get(cat_map[cat]["highest"], 0):
                cat_map[cat]["highest"] = rl

        # Inject bar-grow animation once
        st.markdown("""
        <style>
        @keyframes barGrow {
            from { transform: scaleX(0); }
            to   { transform: scaleX(1); }
        }
        </style>
        """, unsafe_allow_html=True)

        for cat, data in sorted(cat_map.items(), key=lambda x: -x[1]["count"]):
            count   = data["count"]
            highest = data["highest"]
            pct     = round(count / total_alerts * 100)
            bg      = _NEWS_RL_BG.get(highest, "#F3F4F6")
            fg      = _NEWS_RL_FG.get(highest, "#6B7280")
            st.markdown(f"""
            <div style="margin-bottom:16px;">
                <div style="display:flex;align-items:center;justify-content:space-between;
                            margin-bottom:6px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:0.8rem;font-weight:600;color:#111827;
                                     font-family:'Poppins',sans-serif;">{cat}</span>
                        <span style="background:{bg};color:{fg};padding:1px 8px;
                                     border-radius:20px;font-size:0.6rem;font-weight:700;
                                     text-transform:uppercase;letter-spacing:0.4px;">{highest}</span>
                    </div>
                    <span style="font-size:0.8rem;font-weight:700;color:#374151;
                                 font-family:'Poppins',sans-serif;">{count}</span>
                </div>
                <div style="background:#F3F4F6;border-radius:999px;height:7px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;border-radius:999px;background:{fg};
                                transform-origin:left;
                                animation:barGrow 0.75s cubic-bezier(.4,0,.2,1) forwards;">
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="section-label">Risk Level Distribution</div>', unsafe_allow_html=True)

        _RL_COLORS = {
            "Critical": "#DC2626", "High": "#EA580C",
            "Medium":   "#B45309", "Low":  "#16A34A",
        }
        rl_counts: dict = {}
        for n in market_news:
            rl = (n.get("classification") or {}).get("risk_level", "Medium")
            rl_counts[rl] = rl_counts.get(rl, 0) + 1

        labels = list(rl_counts.keys())
        values = list(rl_counts.values())

        fig = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(
                colors=[_RL_COLORS.get(l, "#6B7280") for l in labels],
                line=dict(color="#FFFFFF", width=2),
            ),
            textinfo="label+percent",
            textfont=dict(family="Poppins, sans-serif", size=11, color="#374151"),
            hovertemplate="<b>%{label}</b><br>Alerts: %{value}<br>%{percent}<extra></extra>",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Poppins, sans-serif"),
            height=300,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom", y=-0.3,
                xanchor="center", x=0.5,
                font=dict(family="Poppins, sans-serif", size=10, color="#374151"),
            ),
            margin=dict(l=10, r=10, t=10, b=70),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def page_trends():
    tab1, tab2 = st.tabs(["📢  Broadcast", "📊  Trends"])
    with tab1:
        _page_news_broadcast()
    with tab2:
        _page_trends_content()


# ══════════════════════════════════════════════════════════════════════════════
# PDF REPORT HELPER
# ══════════════════════════════════════════════════════════════════════════════
def _build_pdf(incident: dict, report_md: str) -> bytes:
    cls       = incident.get("classification") or {}
    impact    = incident.get("impact_analysis") or {}
    sev       = cls.get("severity", "Unknown")
    priority  = cls.get("priority", "—")
    imp_level = impact.get("impact_level", "—")
    status_val = incident.get("status", "open").title()

    pct_raw = impact.get("percentage_affected")
    pct     = f"{int(round(pct_raw))}%" if pct_raw is not None else "—"

    sev_colors = {"Critical": "#DC2626", "High": "#EA580C", "Medium": "#D97706", "Low": "#16A34A"}
    sev_color  = sev_colors.get(sev, "#6B7280")
    imp_color  = sev_colors.get(imp_level, "#6B7280")
    stat_color = "#16A34A" if status_val == "Resolved" else "#EA580C"

    body_html = md_lib.markdown(report_md, extensions=["tables", "fenced_code"])

    def _tile(value, label, color):
        return (
            f'<td style="background:#F9FAFB;border:1px solid #E5E7EB;'
            f'padding:14px 10px;text-align:center;">'
            f'<div style="font-size:16px;font-weight:700;color:{color};'
            f'font-family:Helvetica,Arial,sans-serif;">{value}</div>'
            f'<div style="font-size:8px;color:#6B7280;text-transform:uppercase;'
            f'letter-spacing:0.08em;margin-top:6px;font-weight:600;">{label}</div>'
            f'</td>'
        )

    tiles_html = (
        '<table width="100%" cellspacing="8" cellpadding="0" style="margin-bottom:24px;">'
        '<tr>'
        + _tile(sev,        "Severity",     sev_color)
        + _tile(priority,   "Priority",     "#A100FF")
        + _tile(pct,        "% Affected",   "#A100FF")
        + _tile(imp_level,  "Impact Level", imp_color)
        + _tile(status_val, "Status",       stat_color)
        + '</tr></table>'
    )

    generated_time = dt.datetime.now().strftime("%B %d, %Y · %H:%M")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{
      margin-top: 44px;
      margin-left: 50px;
      margin-right: 50px;
      margin-bottom: 52px;
      @frame footer_frame {{
          -pdf-frame-content: pdf_footer;
          bottom: 14px;
          left: 50px;
          right: 50px;
          height: 32px;
      }}
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10.5px;
          color: #1F2937; background: #fff; }}

  .hdr {{ margin-bottom: 26px; padding-bottom: 18px; border-bottom: 3px solid #A100FF; }}
  .hdr-eyebrow {{ font-size: 9px; font-weight: 700; color: #A100FF;
                  text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 6px; }}
  .hdr-title {{ font-size: 22px; font-weight: 700; color: #111827; line-height: 1.25; }}
  .hdr-meta {{ font-size: 10px; color: #6B7280; margin-top: 10px; line-height: 1.7; }}
  .hdr-meta strong {{ color: #374151; font-weight: 600; }}

  .section {{ font-size: 11px; font-weight: 700; color: #111827;
              margin: 24px 0 10px; padding-left: 10px;
              border-left: 3px solid #A100FF; }}

  .report h1, .report h2 {{ font-size: 13px; font-weight: 700;
                             margin: 14px 0 6px; color: #111827; }}
  .report h3 {{ font-size: 11px; font-weight: 600; margin: 10px 0 4px; color: #374151; }}
  .report p  {{ margin-bottom: 8px; line-height: 1.7; color: #374151; }}
  .report ul, .report ol {{ margin: 6px 0 10px 18px; line-height: 1.8; color: #374151; }}
  .report table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10px; }}
  .report th {{ background: #F9FAFB; color: #111827; padding: 8px 10px;
                text-align: left; font-weight: 600; border-bottom: 2px solid #A100FF; }}
  .report td {{ padding: 7px 10px; border-bottom: 1px solid #E5E7EB; color: #374151; }}
  .report tr:nth-child(even) td {{ background: #F9FAFB; }}
  .report code {{ background: #F3F4F6; padding: 1px 5px; font-size: 10px; color: #1F2937; }}
  .report strong {{ font-weight: 700; color: #111827; }}

  #pdf_footer {{ border-top: 1px solid #E5E7EB; padding-top: 10px;
                 font-size: 9px; color: #9CA3AF;
                 font-family: Helvetica, Arial, sans-serif; }}
</style>
</head>
<body>

  <div id="pdf_footer">
    <table width="100%"><tr>
      <td>Accenture Incident Response — Confidential</td>
      <td style="text-align:right;">Generated {generated_time}</td>
    </tr></table>
  </div>

  <div class="hdr">
    <div class="hdr-eyebrow">Incident Report</div>
    <div class="hdr-title">{_html.escape(incident.get("title", "Untitled"))}</div>
    <div class="hdr-meta">
      <strong>ID</strong> {incident.get("id","—")} &nbsp;·&nbsp;
      <strong>Market</strong> {incident.get("market","—")} &nbsp;·&nbsp;
      <strong>Lead</strong> {incident.get("team_lead","—")} &nbsp;·&nbsp;
      <strong>Created</strong> {incident.get("created_at","")[:16].replace("T"," ")}
    </div>
  </div>

  <div class="section">Key Metrics</div>
  {tiles_html}

  <div class="section">Report</div>
  <div class="report">{body_html}</div>

</body>
</html>"""

    buf = io.BytesIO()
    pisa.CreatePDF(html, dest=buf)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# FLOW HELPERS — used in incident detail + broadcast log
# ══════════════════════════════════════════════════════════════════════════════

def _flow_badge(flow: str) -> str:
    return (
        f'<span style="background:#EDE9FE;color:#7C3AED;border-radius:4px;'
        f'padding:1px 5px;font-size:0.58rem;font-weight:700;'
        f'letter-spacing:0.02em;font-family:Poppins,sans-serif;">{flow}</span>'
    )


def _flow_breakdown_rows_html(
    reviewers: list, responses: dict, resolution_responses: dict = None
) -> str:
    """Return inner row HTML for flow breakdown (no outer container)."""
    resolution_responses = resolution_responses or {}
    flow_data: dict = {}
    for r in reviewers:
        flow = REVIEWER_FLOWS.get(r, ["—"])[0]
        if flow not in flow_data:
            flow_data[flow] = {"still_impacted": 0, "resolved": 0, "pending": 0}
        if r not in responses:
            flow_data[flow]["pending"] += 1
        elif responses[r]:
            if resolution_responses.get(r):
                flow_data[flow]["resolved"] += 1
            else:
                flow_data[flow]["still_impacted"] += 1

    def _row_html(flow: str, c: dict) -> str:
        imp_html = (
            f'<span style="font-size:0.68rem;color:#D97706;font-weight:600;">'
            f'🟠 {c["still_impacted"]} impacted</span>'
            if c["still_impacted"] else ""
        )
        res_html = (
            f'<span style="font-size:0.68rem;color:#2563EB;font-weight:600;">'
            f'🔵 {c["resolved"]} resolved</span>'
            if c["resolved"] else ""
        )
        pend_html = (
            f'<span style="font-size:0.68rem;color:#9CA3AF;font-weight:600;">'
            f'⏳ {c["pending"]} pending</span>'
            if c["pending"] else ""
        )
        return (
            f'<div style="display:flex;align-items:center;gap:14px;'
            f'padding:7px 0;border-bottom:1px solid #F3F4F6;">'
            f'<div style="min-width:100px;">{_flow_badge(flow)}</div>'
            f'{imp_html}{res_html}{pend_html}'
            f'</div>'
        )

    _FLOW_LIMIT = 3
    sorted_flows = sorted(flow_data)
    visible_rows = "".join(_row_html(f, flow_data[f]) for f in sorted_flows[:_FLOW_LIMIT])
    hidden_count = len(sorted_flows) - _FLOW_LIMIT

    if hidden_count <= 0:
        return visible_rows

    hidden_rows = "".join(_row_html(f, flow_data[f]) for f in sorted_flows[_FLOW_LIMIT:])
    return (
        f'<style>details.fb-expand>summary{{list-style:none;cursor:pointer;}}'
        f'details.fb-expand>summary::-webkit-details-marker{{display:none;}}</style>'
        f'{visible_rows}'
        f'<details class="fb-expand" style="margin-top:2px;">'
        f'<summary style="font-size:0.65rem;color:var(--accent);font-weight:600;'
        f'font-family:Poppins,sans-serif;padding:6px 0 2px;">'
        f'View more ({hidden_count})</summary>'
        f'<div>{hidden_rows}</div>'
        f'</details>'
    )


def _flow_breakdown_html(reviewers: list, responses: dict) -> str:
    """Return a full HTML block grouping reviewer responses by flow."""
    return (
        f'<div style="margin-top:14px;">'
        f'<div style="font-size:0.62rem;font-weight:700;color:#A100FF;'
        f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;'
        f'font-family:Poppins,sans-serif;">Flow Breakdown</div>'
        f'<div style="background:var(--muted);border:1px solid var(--border);'
        f'border-radius:10px;padding:10px 14px;">'
        + _flow_breakdown_rows_html(reviewers, responses) +
        f'</div></div>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# TEAM LEAD — Incident Detail View
# ══════════════════════════════════════════════════════════════════════════════
def page_incident_detail():
    inc_id = st.session_state.get("selected_incident_id")
    if not inc_id:
        st.session_state.active_page = "incidents"
        _save_session()
        st.rerun()
        return

    incident = get_incident(inc_id)
    if not incident:
        st.error("Incident not found.")
        if st.button("← Back to Incidents"):
            st.session_state.active_page = "incidents"
            _save_session()
            st.rerun()
        return

    inc_markets = incident.get("markets", [incident.get("market", "")] if incident.get("market") else [])
    _inc_flows  = set(incident.get("flows", []))
    reviewers   = list({
        r
        for mkt in inc_markets
        for r in MARKET_REVIEWERS.get(mkt, [])
        if not _inc_flows or any(f in _inc_flows for f in REVIEWER_FLOWS.get(r, []))
    })
    cls         = incident.get("classification") or {}
    responses = incident.get("responses", {})
    resp_total = len(responses)
    total_rev  = len(reviewers)
    all_responded = resp_total >= total_rev

    # ── Back button ───────────────────────────────────────────────────────────
    sev    = cls.get("severity", "Unknown")
    status = _incident_status(incident)
    col_back, _ = st.columns([2, 8])
    with col_back:
        if st.button("← Back to All Incidents", use_container_width=True):
            st.session_state.active_page = "incidents"
            st.session_state.incidents_tab = 2
            _save_session()
            st.rerun()

    # ── Incident title heading ────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:1.6rem;font-weight:700;color:#111827;'
        f'font-family:Poppins,sans-serif;margin:14px 0 8px 0;line-height:1.3;">'
        f'{incident["title"]}</div>'
        f'<div style="display:flex;gap:8px;align-items:center;margin-bottom:4px;">'
        f'{severity_badge(sev)}{_status_html(status)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="ir-divider" style="margin:12px 0 16px;">', unsafe_allow_html=True)

    # ── Meta row ──────────────────────────────────────────────────────────────
    mkts_disp = ", ".join(inc_markets) if inc_markets else "—"
    locs_disp = ", ".join(incident.get("locations", [])) or "—"
    fls_disp  = ", ".join(incident.get("flows", [])) or "—"
    mt_raw    = incident.get("metric", [])
    mt_disp   = ", ".join(mt_raw) if isinstance(mt_raw, list) else (mt_raw or "—")
    st.markdown(
        f'<div style="font-size:0.78rem;color:var(--muted-text);font-family:Poppins,sans-serif;'
        f'margin-bottom:16px;line-height:1.8;">'
        f'<strong style="color:var(--foreground);">ID</strong> {incident["id"]}'
        f'&nbsp;·&nbsp; <strong style="color:var(--foreground);">Lead</strong> {incident["team_lead"]}'
        f'&nbsp;·&nbsp; <strong style="color:var(--foreground);">Created</strong> {incident["created_at"][:16].replace("T"," ")}'
        f'<br>'
        f'<strong style="color:var(--foreground);">Markets</strong> {mkts_disp}'
        f'&nbsp;·&nbsp; <strong style="color:var(--foreground);">Locations</strong> {locs_disp}'
        f'&nbsp;·&nbsp; <strong style="color:var(--foreground);">Flows</strong> {fls_disp}'
        f'&nbsp;·&nbsp; <strong style="color:var(--foreground);">Metric Impact</strong> {mt_disp}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Description ───────────────────────────────────────────────────────────
    desc_text = _html.escape(incident.get("description", "") or "—")
    st.markdown(
        f'<details class="custom-details">'
        f'<summary class="custom-summary">'
        f'<span class="custom-summary-label">Description</span>'
        f'<span class="custom-summary-arrow"></span>'
        f'</summary>'
        f'<div class="custom-details-body">{desc_text}</div>'
        f'</details>',
        unsafe_allow_html=True,
    )

    # ── Classification card ───────────────────────────────────────────────────
    st.markdown('<div class="section-label" style="margin-top:8px;">Classification</div>',
                unsafe_allow_html=True)
    if cls:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(metric_card(cls.get("category", "—"), "Category", "primary"),
                        unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card(cls.get("severity", "—"), "Severity", "high"),
                        unsafe_allow_html=True)
        with c3:
            st.markdown(metric_card(cls.get("priority", "—"), "Priority", "resolved"),
                        unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.78rem;color:var(--muted-text);font-family:Poppins,sans-serif;'
            f'margin-top:8px;margin-bottom:16px;">Reasoning: {cls.get("reasoning","—")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Classification not available.")

    # ── Reviewer responses ────────────────────────────────────────────────────
    st.markdown('<div class="section-label" style="margin-top:4px;">Reviewer Responses</div>',
                unsafe_allow_html=True)
    resp_yes = sum(1 for v in responses.values() if v)
    resp_no  = sum(1 for v in responses.values() if not v)
    pending  = [r for r in reviewers if r not in responses]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card(f"{resp_total}/{total_rev}", "Responded", "primary"),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(resp_yes, "Affected", "high"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(resp_no, "Not Affected", "resolved"), unsafe_allow_html=True)

    reviewer_pills = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:var(--muted);border:1px solid var(--border);'
        f'border-radius:999px;padding:4px 12px;font-size:0.7rem;'
        f'color:var(--foreground);font-family:Poppins,sans-serif;margin:3px;">'
        f'{"🔴" if responses.get(r) == True else "🟢" if responses.get(r) == False else "⏳"}'
        f' {r} {_flow_badge(REVIEWER_FLOWS.get(r, ["—"])[0])}'
        f'</span>'
        for r in reviewers
    )
    st.markdown(
        f'<div style="margin-top:10px;margin-bottom:4px;">{reviewer_pills}</div>'
        + _flow_breakdown_html(reviewers, responses)
        + '<div style="height:16px;"></div>',
        unsafe_allow_html=True,
    )

    # ── Lazy Agent 2 + 3 ──────────────────────────────────────────────────────
    should_generate = all_responded or incident.get("status") == "resolved"

    if should_generate and not incident.get("impact_analysis"):
        with st.spinner("Analyzing impact across reviewer responses…"):
            try:
                impact = analyze_impact(incident)
                incident = update_incident(inc_id, {"impact_analysis": impact})
            except Exception as e:
                st.error(f"Impact analysis failed: {type(e).__name__}: {e}")

    if should_generate and incident.get("impact_analysis") and not incident.get("report"):
        with st.spinner("Generating incident report…"):
            try:
                report_md = generate_report(incident)
                incident = update_incident(inc_id, {"report": report_md})
            except Exception as e:
                st.error(f"Report generation failed: {type(e).__name__}: {e}")

    # ── Impact Analysis ───────────────────────────────────────────────────────
    impact = incident.get("impact_analysis")
    if impact:
        st.markdown('<div class="section-label" style="margin-top:4px;">Impact Analysis</div>',
                    unsafe_allow_html=True)
        ia1, ia2, ia3 = st.columns(3)
        with ia1:
            pct = int(round(impact.get("percentage_affected", 0)))
            st.markdown(metric_card(f"{pct}%", "% Affected", "high"), unsafe_allow_html=True)
        with ia2:
            st.markdown(metric_card(impact.get("impact_level", "—"), "Impact Level", "primary"),
                        unsafe_allow_html=True)
        with ia3:
            st.markdown(metric_card(
                f"{impact.get('affected_count',0)}/{impact.get('total_users',0)}",
                "Affected / Total", "resolved"), unsafe_allow_html=True)
        if impact.get("insights"):
            st.markdown(
                '<div style="margin-top:8px;margin-bottom:16px;">'
                + "".join(
                    f'<div style="font-size:0.78rem;color:var(--muted-text);'
                    f'font-family:Poppins,sans-serif;padding:2px 0;">• {ins}</div>'
                    for ins in impact["insights"]
                )
                + "</div>",
                unsafe_allow_html=True,
            )
    elif not all_responded and incident.get("status") != "resolved":
        st.info(f"Impact analysis will run automatically when all {total_rev} reviewers respond "
                f"({resp_total}/{total_rev} so far).")

    # ── Incident Report ───────────────────────────────────────────────────────
    report = incident.get("report")
    if report:
        col_label, col_dl = st.columns([7, 3])
        with col_label:
            st.markdown('<div class="section-label" style="margin-top:6px;">Incident Report</div>',
                        unsafe_allow_html=True)
        with col_dl:
            pdf_bytes = _build_pdf(incident, report)
            filename  = f"incident_{incident['id']}_{incident.get('created_at','')[:10]}.pdf"
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                key="dl_pdf",
            )
        st.markdown(report)
    elif not all_responded and incident.get("status") != "resolved":
        st.info("Report will be generated once all reviewers have responded.")

    # ── Resolve / Reopen ──────────────────────────────────────────────────────
    st.markdown('<hr class="ir-divider" style="margin:20px 0 12px;">', unsafe_allow_html=True)
    current_status = incident.get("status", "open")
    col_btn, _ = st.columns([2, 8])
    with col_btn:
        if current_status != "resolved":
            if st.button("✅ Resolve Incident", use_container_width=True, type="primary"):
                # Force-generate report if still missing
                if not incident.get("impact_analysis"):
                    with st.spinner("Running impact analysis…"):
                        try:
                            impact = analyze_impact(incident)
                            incident = update_incident(inc_id, {"impact_analysis": impact})
                        except Exception as e:
                            st.error(f"Impact analysis failed: {type(e).__name__}: {e}")
                if not incident.get("report"):
                    with st.spinner("Generating report…"):
                        try:
                            report_md = generate_report(incident)
                            incident = update_incident(inc_id, {"report": report_md})
                        except Exception as e:
                            st.error(f"Report generation failed: {type(e).__name__}: {e}")
                update_incident(inc_id, {"status": "resolved"})
                st.rerun()
        else:
            if st.button("↩ Reopen Incident", use_container_width=True):
                update_incident(inc_id, {"status": "open"})
                st.rerun()



# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
_REFRESH_JS = """
<script>
// ── Shared helper: find the hidden content-refresh button via its anchor span ──
// Walks up from the anchor through Streamlit's wrapper divs to find the sibling
// container that holds the hidden st.button, then returns the <button> inside it.
(function() {
    var doc = window.parent.document;

    function findHiddenBtn() {
        var anchor = doc.getElementById('_ir_rfr_anchor');
        if (!anchor) return null;
        var node = anchor;
        for (var i = 0; i < 6; i++) {
            node = node.parentElement;
            if (!node) break;
            var sib = node.nextElementSibling;
            if (sib) {
                var b = sib.querySelector('button');
                if (b) return { btn: b, container: sib };
            }
        }
        return null;
    }

    // Hide the trigger element so it's invisible but still clickable by JS
    function hideTrigger() {
        var found = findHiddenBtn();
        if (!found) return false;
        found.container.style.cssText =
            'position:fixed!important;left:-9999px!important;top:0;' +
            'opacity:0!important;pointer-events:none!important;' +
            'width:0!important;height:0!important;overflow:hidden!important;';
        return true;
    }

    // Retry hiding until the anchor + button appear in the DOM (they render after the iframe)
    var hideAttempts = 0;
    var hideIv = setInterval(function() {
        if (hideTrigger() || ++hideAttempts > 20) clearInterval(hideIv);
    }, 100);

    // ── Navbar refresh button ──────────────────────────────────────────────────
    if (!doc.querySelector('.ir-navbar-refresh')) {
        var NS = 'http://www.w3.org/2000/svg';
        var svg = doc.createElementNS(NS, 'svg');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('width', '17'); svg.setAttribute('height', '17');
        svg.style.cssText = 'display:block;transition:transform 0.55s cubic-bezier(0.4,0,0.2,1);';
        var path = doc.createElementNS(NS, 'path');
        path.setAttribute('d', 'M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z');
        path.setAttribute('fill', '#9CA3AF');
        svg.appendChild(path);
        var btn = doc.createElement('button');
        btn.className = 'ir-navbar-refresh';
        btn.title = 'Refresh';
        btn.appendChild(svg);
        btn.addEventListener('mouseenter', function() {
            btn.style.background = '#EDE9FE'; btn.style.borderColor = '#A100FF';
            path.setAttribute('fill', '#A100FF');
            svg.style.transform = 'rotate(180deg)';
        });
        btn.addEventListener('mouseleave', function() {
            btn.style.background = ''; btn.style.borderColor = '';
            path.setAttribute('fill', '#9CA3AF');
            svg.style.transform = 'rotate(0deg)';
        });
        btn.addEventListener('click', function() {
            svg.style.transform = 'rotate(360deg)';
            setTimeout(function() {
                var found = findHiddenBtn();
                if (found) { found.btn.click(); } else { window.parent.location.reload(); }
            }, 300);
        });
        var userEl = doc.querySelector('.ir-navbar-user');
        if (userEl) userEl.parentNode.insertBefore(btn, userEl);
    }
})();

// ── Tab → URL sync (keeps ?tab=N current at all times so Ctrl+R / F5 works) ──
(function() {
    var doc = window.parent.document;
    function attach() {
        var tablist = doc.querySelector('[role="tablist"]');
        if (!tablist || tablist.dataset.tabUrlSync === '1') return;
        tablist.dataset.tabUrlSync = '1';
        function syncUrl() {
            var tabs = tablist.querySelectorAll('[data-baseweb="tab"]');
            for (var i = 0; i < tabs.length; i++) {
                if (tabs[i].getAttribute('aria-selected') === 'true') {
                    var url = new URL(window.parent.location.href);
                    if (url.searchParams.get('tab') !== String(i)) {
                        url.searchParams.set('tab', i);
                        window.parent.history.replaceState({}, '', url.href);
                    }
                    return;
                }
            }
        }
        new MutationObserver(syncUrl).observe(tablist, {
            attributes: true, subtree: true, attributeFilter: ['aria-selected']
        });
        syncUrl();
    }
    var tries = 0;
    var iv = setInterval(function() {
        attach();
        if (++tries > 20) clearInterval(iv);
    }, 150);
})();
</script>
"""

if not st.session_state.role:
    render_navbar()
    show_login()
else:
    fix_sidebar_padding()
    render_navbar(
        display_name=st.session_state.tl_display_name or "",
        role=st.session_state.role,
    )
    components.html(_REFRESH_JS, height=0, scrolling=False)
    st.markdown('<span id="_ir_rfr_anchor"></span>', unsafe_allow_html=True)
    if st.button("↻", key="_ir_content_refresh"):
        st.rerun()
    show_sidebar()

    if not st.session_state.get("broadcast_policy_ack"):
        _broadcast_policy_dialog()

    page = st.session_state.active_page

    if page == "incidents":
        page_incidents()
    elif page == "incident_detail":
        page_incident_detail()
    elif page == "trends":
        page_trends()
    else:
        st.session_state.active_page = "incidents"
        _save_session()
        st.rerun()
