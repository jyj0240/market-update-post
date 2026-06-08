import json
from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = DATA_DIR / "reports"

CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
.block-container {padding-top: 1rem !important; max-width: 900px !important;}
div[data-testid="stMetric"] {
    background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 0.5rem 0.75rem;
}
div[data-testid="stMetric"] label {
    font-size: 0.65rem !important; text-transform: uppercase; letter-spacing: 0.04em;
    font-weight: 600 !important; color: #94a3b8 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1rem !important; font-weight: 700 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.7rem !important;
}
.stMarkdown code {
    background: #312e81 !important; color: #a5b4fc !important;
    border: 1px solid #4338ca !important; border-radius: 12px !important;
    padding: 2px 10px !important; font-size: 0.8rem !important;
}
hr {border-color: #334155 !important; margin: 1rem 0 !important;}
section[data-testid="stSidebar"] {background: #0f172a;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def render_nav():
    st.html("""
    <div style="display:flex;gap:12px;padding:4px 0 8px 0;font-size:0.8rem;">
        <a href="/" target="_self" style="color:#94a3b8;text-decoration:none;">Briefing</a>
        <a href="/Sentiment" target="_self" style="color:#94a3b8;text-decoration:none;">Sentiment</a>
        <a href="/History" target="_self" style="color:#94a3b8;text-decoration:none;">History</a>
        <a href="/Request" target="_self" style="color:#94a3b8;text-decoration:none;">Request</a>
    </div>
    """)


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:1rem 0;">
            <h2 style="margin:0; font-size:1.3rem; font-weight:700; color:#e2e8f0;">Market Briefing</h2>
            <p style="color:#64748b; font-size:0.8rem; margin:0.25rem 0 0 0;">AI-Powered Intelligence</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        history = load_sentiment_history()
        if history:
            latest = history[-1]
            total = latest.get("total", 0)
            prev = history[-2].get("total") if len(history) >= 2 else None
            delta = None
            if prev is not None:
                delta = f"{total - prev:+.1f}"
            st.metric("Sentiment", f"{total:.1f}/10", delta=delta)
        st.divider()
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption("Auto-refreshes every 5 min.")


@st.cache_data(ttl=300)
def load_latest():
    latest_path = DATA_DIR / "latest.json"
    if not latest_path.exists():
        return None
    with open(latest_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    report_path = Path(__file__).parent / meta.get("latest_report", "")
    if not report_path.exists():
        return None
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    report["_meta"] = meta
    return report


@st.cache_data(ttl=300)
def load_report(date_str, filename):
    path = REPORTS_DIR / date_str / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def load_sentiment_history():
    path = DATA_DIR / "sentiment.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def list_available_dates():
    if not REPORTS_DIR.exists():
        return []
    return sorted([d.name for d in REPORTS_DIR.iterdir() if d.is_dir()], reverse=True)


@st.cache_data(ttl=300)
def list_reports_for_date(date_str):
    date_dir = REPORTS_DIR / date_str
    if not date_dir.exists():
        return []
    return sorted([f.name for f in date_dir.glob("*_briefing.json")])


def format_time_label(filename):
    base = filename.replace("_briefing.json", "")
    if len(base) == 4 and base.isdigit():
        return f"{base[:2]}:{base[2:]}"
    return base


def score_to_color(score):
    if score is None:
        return "#64748b"
    if score <= 3:
        return "#ef4444"
    elif score <= 5:
        return "#eab308"
    elif score <= 7:
        return "#22c55e"
    return "#10b981"


def score_to_label(score):
    if score is None:
        return "-"
    if score <= 3:
        return "Bearish"
    elif score <= 5:
        return "Neutral"
    elif score <= 7:
        return "Bullish"
    return "Very Bullish"


def clean_keywords(keywords):
    return [k for k in keywords
            if not any(k.startswith(f"{i}.") for i in range(1, 7))
            and 2 < len(k) < 30]
