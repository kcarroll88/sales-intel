import streamlit as st
import os
from agent import index_documents, build_agent
from evals import run_evals

st.set_page_config(
    page_title="Apex CRM — Sales Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── AUTH ──────────────────────────────────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("""
<style>
[data-testid="stSidebar"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
header { display: none !important; }

[data-testid="stAppViewContainer"] {
    background: #fafafa !important;
    min-height: 100vh;
}

.main .block-container {
    padding-top: 15vh !important;
}

.login-header {
    text-align: center;
    margin-bottom: 2rem;
}
.login-logo {
    width: 40px; height: 40px;
    background: #18181b;
    border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    margin-bottom: 1.25rem;
}
.login-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #18181b;
    letter-spacing: -0.02em;
    margin-bottom: 0.25rem;
}
.login-subtitle {
    font-size: 0.8125rem;
    color: #71717a;
}

.stTextInput input {
    background: #ffffff !important;
    border: 1px solid #e4e4e7 !important;
    border-radius: 8px !important;
    font-size: 0.9375rem !important;
    color: #18181b !important;
    padding: 0.6rem 0.75rem !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease !important;
}
.stTextInput input:focus {
    border-color: #a1a1aa !important;
    box-shadow: 0 0 0 3px rgba(24,24,27,0.06) !important;
    outline: none !important;
}
.stTextInput input::placeholder { color: #a1a1aa !important; }

.stFormSubmitButton > button {
    background: #18181b !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1rem !important;
    width: 100% !important;
    box-shadow: none !important;
    transition: background 0.15s ease !important;
    margin-top: 0.25rem !important;
    letter-spacing: -0.01em !important;
}
.stFormSubmitButton > button:hover {
    background: #27272a !important;
    color: #ffffff !important;
    box-shadow: none !important;
    transform: none !important;
}
.stFormSubmitButton > button:active {
    background: #3f3f46 !important;
    transform: none !important;
    box-shadow: none !important;
}
small[data-testid="InputInstructions"],
[data-testid="InputInstructions"],
.stTextInput div[data-testid="InputInstructions"],
.stForm small { display: none !important; }

[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
}

[data-testid="stAlert"] {
    background: #fff1f2 !important;
    border: 1px solid #fecdd3 !important;
    border-radius: 8px !important;
    font-size: 0.8125rem !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

        login_container = st.empty()
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.markdown("""
<div class="login-header">
  <div class="login-logo">
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
         fill="none" stroke="white" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/>
    </svg>
  </div>
  <div class="login-title">Apex CRM</div>
  <div class="login-subtitle">Enter your password to continue</div>
</div>
""", unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=True):
                password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                submitted = st.form_submit_button("Continue", use_container_width=True)

            if submitted:
                if password == os.getenv("APP_PASSWORD", "apex2026"):
                    st.session_state.authenticated = True
                    login_container.empty()
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")

        st.stop()

check_password()

# ── RATE LIMITING ─────────────────────────────────────────────────────────────
if "request_count" not in st.session_state:
    st.session_state.request_count = 0

MAX_REQUESTS = 20

if st.session_state.request_count >= MAX_REQUESTS:
    st.error("You've reached the demo limit of 20 questions. Contact me at hello@keenancarroll.com for full access.")
    st.stop()

# ── SVG ICONS ─────────────────────────────────────────────────────────────────
def icon(name, size=16, color="currentColor"):
    paths = {
        "target": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
        "brain": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>',
        "book": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>',
        "globe": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>',
        "zap": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
        "flask": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2v17.5c0 1.4-1.1 2.5-2.5 2.5s-2.5-1.1-2.5-2.5V2"/><path d="M8.5 2h7"/><path d="M14.5 16h-5"/><path d="M8.5 12c-1.5 0-2 1-2 2.5s.5 2.5 2 2.5h7c1.5 0 2-1 2-2.5S17 12 15.5 12"/></svg>',
        "sword": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polyline points="14.5 17.5 3 6 3 3 6 3 17.5 14.5"/><line x1="13" y1="19" x2="19" y2="13"/><line x1="16" y1="16" x2="20" y2="20"/><line x1="19" y1="21" x2="21" y2="19"/></svg>',
        "newspaper": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 0-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6z"/></svg>',
        "bar_chart": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>',
        "check_circle": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        "alert_triangle": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "x_circle": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>',
        "arrow_right": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
        "sparkles": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>',
        "layers": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    }
    return paths.get(name, "")


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Use system Inter if available, fall back to system-ui which is visually identical on macOS/Windows */
@font-face {
    font-family: 'Inter';
    src: local('Inter'), local('Inter-Regular');
    font-weight: 100 900;
    font-display: swap;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* ── RESET ─────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── BACKGROUND ────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: #f0f2ff !important;
    background-image:
        radial-gradient(ellipse 80% 60% at 15% 20%, rgba(99,102,241,0.09) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 85% 75%, rgba(139,92,246,0.07) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 50% 50%, rgba(59,130,246,0.04) 0%, transparent 70%) !important;
    min-height: 100vh;
}

/* Subtle animated mesh orbs */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: -20%;
    left: -10%;
    width: 55vw;
    height: 55vw;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 65%);
    animation: orbDrift 25s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

[data-testid="stAppViewContainer"]::after {
    content: '';
    position: fixed;
    bottom: -10%;
    right: -10%;
    width: 50vw;
    height: 50vw;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(139,92,246,0.05) 0%, transparent 65%);
    animation: orbDrift 30s ease-in-out infinite alternate-reverse;
    pointer-events: none;
    z-index: 0;
}

@keyframes orbDrift {
    0%   { transform: translate(0,   0)   scale(1);    }
    50%  { transform: translate(3%,  2%)  scale(1.04); }
    100% { transform: translate(-2%, 4%)  scale(0.97); }
}

/* ── HEADER ────────────────────────────────────────────────── */
[data-testid="stHeader"] {
    background: rgba(248,249,255,0.75) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-bottom: 1px solid rgba(226,232,255,0.5) !important;
    box-shadow: 0 1px 12px rgba(99,102,241,0.06) !important;
}

/* ── SIDEBAR ────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.62) !important;
    backdrop-filter: blur(28px) !important;
    -webkit-backdrop-filter: blur(28px) !important;
    border-right: 1px solid rgba(226,232,255,0.55) !important;
    box-shadow: 4px 0 32px rgba(99,102,241,0.07) !important;
}

[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {
    background: transparent !important;
}

/* ── MAIN BLOCK ─────────────────────────────────────────────── */
.main .block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 880px !important;
    position: relative;
    z-index: 1;
    animation: pageFadeIn 0.45s cubic-bezier(0.16,1,0.3,1) both;
}

@keyframes pageFadeIn {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0);    }
}

/* ── TYPOGRAPHY ─────────────────────────────────────────────── */
h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
    letter-spacing: -0.025em !important;
}

/* ── GLASS CARD (reusable) ──────────────────────────────────── */
.gc {
    background: rgba(255,255,255,0.62);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255,255,255,0.65);
    border-radius: 16px;
    box-shadow: 0 2px 16px rgba(99,102,241,0.07), 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.22s ease, transform 0.22s ease;
}
.gc:hover {
    box-shadow: 0 6px 28px rgba(99,102,241,0.13), 0 2px 6px rgba(0,0,0,0.05);
    transform: translateY(-2px);
}

/* ── PAGE TITLE BLOCK ───────────────────────────────────────── */
.page-title {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 0.2rem;
}
.title-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 14px rgba(79,70,229,0.3);
    flex-shrink: 0;
}
.title-text {
    font-family: 'Inter', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    background: linear-gradient(135deg, #1e1b4b 0%, #4f46e5 55%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    line-height: 1.15;
}
.title-caption {
    font-family: 'Inter', sans-serif;
    font-size: 0.875rem;
    color: #6b7280;
    margin-top: 0.35rem;
    margin-bottom: 1.5rem;
    font-weight: 400;
}

/* ── QUICK ACTION BUTTONS ───────────────────────────────────── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.8125rem !important;
    color: #374151 !important;
    background: rgba(255,255,255,0.7) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(226,232,255,0.7) !important;
    border-radius: 12px !important;
    padding: 0.55rem 0.9rem !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.06), 0 1px 2px rgba(0,0,0,0.04) !important;
    transition: all 0.18s cubic-bezier(0.16,1,0.3,1) !important;
    width: 100% !important;
    text-align: left !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
}
.stButton > button:hover {
    background: rgba(255,255,255,0.92) !important;
    border-color: rgba(99,102,241,0.35) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.14), 0 2px 6px rgba(0,0,0,0.05) !important;
    transform: translateY(-2px) !important;
    color: #1e1b4b !important;
}
.stButton > button:active {
    transform: translateY(0px) scale(0.98) !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.08) !important;
}

/* Eval run button — distinct primary style */
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, rgba(79,70,229,0.12) 0%, rgba(124,58,237,0.08) 100%) !important;
    border-color: rgba(99,102,241,0.25) !important;
    color: #3730a3 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, rgba(79,70,229,0.2) 0%, rgba(124,58,237,0.15) 100%) !important;
    border-color: rgba(99,102,241,0.45) !important;
    color: #1e1b4b !important;
}

/* ── CHAT MESSAGES ──────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.65) !important;
    backdrop-filter: blur(18px) !important;
    -webkit-backdrop-filter: blur(18px) !important;
    border: 1px solid rgba(255,255,255,0.65) !important;
    border-radius: 18px !important;
    box-shadow: 0 2px 14px rgba(99,102,241,0.07), 0 1px 3px rgba(0,0,0,0.04) !important;
    margin-bottom: 0.875rem !important;
    padding: 1rem 1.25rem !important;
    animation: msgIn 0.3s cubic-bezier(0.16,1,0.3,1) both;
    transition: box-shadow 0.2s ease !important;
}
[data-testid="stChatMessage"]:hover {
    box-shadow: 0 4px 20px rgba(99,102,241,0.1), 0 2px 6px rgba(0,0,0,0.05) !important;
}

/* User messages get a subtle tint */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: rgba(240,242,255,0.75) !important;
    border-color: rgba(226,232,255,0.6) !important;
}

@keyframes msgIn {
    from { opacity: 0; transform: translateY(10px) scale(0.98); }
    to   { opacity: 1; transform: translateY(0)   scale(1);    }
}

/* ── CHAT INPUT ─────────────────────────────────────────────── */
[data-testid="stChatInputContainer"] {
    background: rgba(255,255,255,0.78) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border: 1.5px solid rgba(226,232,255,0.7) !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 24px rgba(99,102,241,0.1), 0 2px 8px rgba(0,0,0,0.04) !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="stChatInputContainer"]:focus-within {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 4px 28px rgba(99,102,241,0.15), 0 0 0 3px rgba(99,102,241,0.07) !important;
}
[data-testid="stChatInputContainer"] textarea {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9375rem !important;
    color: #1e1b4b !important;
    background: transparent !important;
}
[data-testid="stChatInputContainer"] textarea::placeholder {
    color: #9ca3af !important;
}

/* ── SIDEBAR CUSTOM HTML ────────────────────────────────────── */
.sb-section {
    margin-bottom: 0.5rem;
}
.sb-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9ca3af;
    margin: 1.25rem 0 0.6rem;
    display: flex;
    align-items: center;
    gap: 6px;
}
.sb-card {
    background: rgba(255,255,255,0.5);
    border: 1px solid rgba(255,255,255,0.7);
    border-radius: 14px;
    padding: 0.875rem 1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 2px 10px rgba(99,102,241,0.05);
    transition: all 0.2s ease;
}
.sb-card:hover {
    background: rgba(255,255,255,0.72);
    box-shadow: 0 4px 18px rgba(99,102,241,0.1);
    transform: translateY(-1px);
}
.sb-card-head {
    font-family: 'Inter', sans-serif;
    font-size: 0.8125rem;
    font-weight: 600;
    color: #374151;
    display: flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 4px;
}
.sb-card-body {
    font-family: 'Inter', sans-serif;
    font-size: 0.78125rem;
    color: #6b7280;
    line-height: 1.55;
    padding-left: 23px;
}
.sb-how-item {
    font-family: 'Inter', sans-serif;
    font-size: 0.78125rem;
    color: #6b7280;
    display: flex;
    align-items: flex-start;
    gap: 7px;
    padding: 3px 0;
    line-height: 1.5;
}
.sb-how-item .arrow { color: #4f46e5; flex-shrink: 0; margin-top: 1px; }
.sb-stack {
    font-family: 'Inter', sans-serif;
    font-size: 0.71875rem;
    color: #9ca3af;
    text-align: center;
    padding: 0.75rem 0 0.25rem;
    letter-spacing: 0.01em;
}
.sb-stack strong { color: #6b7280; }

/* ── QUICK ACTIONS LABEL ────────────────────────────────────── */
.qa-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9ca3af;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── EVAL RESULT BADGES ─────────────────────────────────────── */
.eval-badge {
    font-family: 'Inter', sans-serif;
    font-size: 0.875rem;
    font-weight: 600;
    padding: 0.625rem 1rem;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: msgIn 0.3s cubic-bezier(0.16,1,0.3,1) both;
}
.eval-pass {
    background: rgba(16,185,129,0.1);
    color: #065f46;
    border: 1px solid rgba(16,185,129,0.2);
}
.eval-warn {
    background: rgba(245,158,11,0.1);
    color: #92400e;
    border: 1px solid rgba(245,158,11,0.22);
}
.eval-fail {
    background: rgba(239,68,68,0.1);
    color: #991b1b;
    border: 1px solid rgba(239,68,68,0.2);
}

/* ── DIVIDER ────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid rgba(0,0,0,0.07) !important;
    margin: 1rem 0 !important;
}

/* ── STREAMLIT ALERTS ───────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
}

/* ── SPINNER ────────────────────────────────────────────────── */
[data-testid="stSpinner"] > div {
    border-top-color: #4f46e5 !important;
}

/* ── SCROLLBAR ──────────────────────────────────────────────── */
::-webkit-scrollbar            { width: 5px; height: 5px; }
::-webkit-scrollbar-track      { background: transparent; }
::-webkit-scrollbar-thumb      { background: rgba(99,102,241,0.18); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover{ background: rgba(99,102,241,0.32); }

/* ── HIDE STREAMLIT CHROME ──────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── AGENT INIT ────────────────────────────────────────────────────────────────
@st.cache_resource
def initialize():
    index_documents()
    return build_agent()

agent_executor = initialize()


# ── PAGE TITLE ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-title">
    <div class="title-icon">{icon("target", 22, "white")}</div>
    <div class="title-text">Apex CRM Sales Intelligence</div>
</div>
<div class="title-caption">
    Competitive insights from internal battlecards and live market data — powered by AI
</div>
""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 1.25rem 0 0.5rem;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.25rem;">
            <div style="width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#4f46e5,#7c3aed);display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(79,70,229,0.3);">
                {icon("sparkles", 16, "white")}
            </div>
            <span style="font-family:'Inter',sans-serif;font-size:1rem;font-weight:700;color:#1e1b4b;letter-spacing:-0.02em;">Intelligence Hub</span>
        </div>
        <div style="font-family:'Inter',sans-serif;font-size:0.75rem;color:#9ca3af;padding-left:42px;">Apex CRM · Sales AI</div>
    </div>

    <hr/>

    <div class="sb-label">{icon("layers", 13, "#9ca3af")} Sources</div>

    <div class="sb-card">
        <div class="sb-card-head">{icon("book", 14, "#4f46e5")} Internal Knowledge Base</div>
        <div class="sb-card-body">Battlecards, playbooks, positioning guides, win/loss analysis</div>
    </div>

    <div class="sb-card">
        <div class="sb-card-head">{icon("globe", 14, "#7c3aed")} Live Web Search</div>
        <div class="sb-card-body">Current competitor news, announcements, pricing changes</div>
    </div>

    <hr/>

    <div class="sb-label">{icon("zap", 13, "#9ca3af")} How it works</div>

    <div class="sb-card">
        <div class="sb-how-item"><span class="arrow">{icon("arrow_right", 12, "#4f46e5")}</span><span>Internal question? Searches battlecards</span></div>
        <div class="sb-how-item"><span class="arrow">{icon("arrow_right", 12, "#4f46e5")}</span><span>Current news? Searches the web</span></div>
        <div class="sb-how-item"><span class="arrow">{icon("arrow_right", 12, "#4f46e5")}</span><span>Both needed? Uses both sources</span></div>
    </div>

    <hr/>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="sb-label">{icon("flask", 13, "#9ca3af")} Eval Suite</div>', unsafe_allow_html=True)

    if st.button("Run LLM-as-Judge Evals"):
        with st.spinner("Running evals..."):
            score = run_evals(agent_executor)
        if score == 1.0:
            st.markdown(f'<div class="eval-badge eval-pass">{icon("check_circle", 16, "#10b981")} All evals passed — {score:.0%}</div>', unsafe_allow_html=True)
        elif score >= 0.75:
            st.markdown(f'<div class="eval-badge eval-warn">{icon("alert_triangle", 16, "#f59e0b")} {score:.0%} evals passed</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="eval-badge eval-fail">{icon("x_circle", 16, "#ef4444")} {score:.0%} evals passed</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sb-stack">
        Built with <strong>LangChain</strong> · <strong>Claude</strong> · <strong>Tavily</strong> · <strong>ChromaDB</strong> · <strong>Voyage AI</strong>
    </div>
    """, unsafe_allow_html=True)


# ── QUICK ACTIONS ─────────────────────────────────────────────────────────────
st.markdown(f'<div class="qa-label">{icon("zap", 12, "#9ca3af")} Quick actions</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button(f"Beat Salesforce"):
        st.session_state.query = "How do we beat Salesforce in a competitive deal?"
with col2:
    if st.button(f"HubSpot news"):
        st.session_state.query = "What has HubSpot announced recently in 2026?"
with col3:
    if st.button(f"Win / Loss stats"):
        st.session_state.query = "What is our win rate and top reasons we lose deals?"

st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)


# ── CHAT ──────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

query = st.chat_input("Ask anything about competitors, strategy, or market intelligence...")

if "query" in st.session_state and st.session_state.query:
    query = st.session_state.query
    st.session_state.query = None

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            try:
                answer = agent_executor(query)
            except Exception as e:
                answer = f"Something went wrong: {str(e)}"
        st.write(answer)
        st.session_state.request_count += 1
        st.session_state.messages.append({"role": "assistant", "content": answer})
