import json
from pathlib import Path
from datetime import datetime

import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = DATA_DIR / "reports"


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
def load_report(date_str: str, filename: str):
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
def list_reports_for_date(date_str: str):
    date_dir = REPORTS_DIR / date_str
    if not date_dir.exists():
        return []
    return sorted([f.name for f in date_dir.glob("*_briefing.json")])


def format_time_label(filename: str) -> str:
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
    else:
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
    else:
        return "Very Bullish"


def clean_keywords(keywords):
    return [k for k in keywords
            if not any(k.startswith(f"{i}.") for i in range(1, 7))
            and len(k) < 30 and len(k) > 2]


def render_nav():
    """모든 페이지 상단에 표시되는 네비게이션 바"""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.page_link("app.py", label="Briefing", icon="\U0001F4F0")
    with c2:
        st.page_link("pages/1_시장심리.py", label="Sentiment", icon="\U0001F4C8")
    with c3:
        st.page_link("pages/2_지난브리핑.py", label="History", icon="\U0001F4CB")
    with c4:
        st.page_link("pages/3_관리.py", label="Request", icon="\u2699\ufe0f")


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:1rem 0;">
            <h2 style="margin:0; font-size:1.3rem; font-weight:700; color:#e2e8f0;">
                Market Briefing
            </h2>
            <p style="color:#64748b; font-size:0.8rem; margin:0.25rem 0 0 0;">
                AI-Powered Intelligence
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        history = load_sentiment_history()
        if history:
            latest = history[-1]
            total = latest.get("total", 0)
            prev = history[-2].get("total") if len(history) >= 2 else None
            delta = f"{total - prev:+.1f}" if prev is not None else None
            st.metric("Sentiment", f"{total:.1f}/10", delta=delta)

        st.divider()
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption("Auto-refreshes every 5 min.")
