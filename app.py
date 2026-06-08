import streamlit as st
import time
from datetime import datetime
from utils import load_latest, load_sentiment_history, score_to_color, score_to_label, clean_keywords, render_sidebar
from style import inject_css

st.set_page_config(
    page_title="Market Briefing",
    page_icon="\U0001F4C8",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get help": None, "Report a Bug": None, "About": None},
)
inject_css()

# Auto-refresh every 5 minutes
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if time.time() - st.session_state.last_refresh > 300:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()

render_sidebar()
report = load_latest()

# Header banner
if report:
    gen_at = report.get("generated_at", "")
    updated_label = ""
    if gen_at:
        try:
            dt = datetime.fromisoformat(gen_at)
            updated_label = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            updated_label = gen_at[:16].replace("T", " ")

    st.html(f"""
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white; padding: 1.5rem 2rem; border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        border: 1px solid #334155;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h1 style="margin:0; font-size:1.8rem; font-weight:700; letter-spacing:-0.02em;">
                    Market Briefing
                </h1>
                <p style="color:#a8b2d1; font-size:0.85rem; margin:0.25rem 0 0 0;">
                    AI-Generated Market Intelligence
                </p>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.7rem; color:#a8b2d1; text-transform:uppercase; letter-spacing:0.05em;">
                    Updated
                </div>
                <div style="font-size:0.95rem; font-weight:600;">{updated_label}</div>
            </div>
        </div>
    </div>
    """)
else:
    st.html("""
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white; padding: 1.5rem 2rem; border-radius: 12px;
        border: 1px solid #334155;
    ">
        <h1 style="margin:0; font-size:1.8rem; font-weight:700;">Market Briefing</h1>
        <p style="color:#a8b2d1; font-size:0.85rem; margin:0.25rem 0 0 0;">
            AI-Generated Market Intelligence
        </p>
    </div>
    """)
    st.info("No briefings available yet.")
    st.stop()

# Sentiment - compact inline
sentiment = report.get("sentiment")
if sentiment and sentiment.get("total") is not None:
    history = load_sentiment_history()
    prev = history[-2] if len(history) >= 2 else None
    total = sentiment["total"]
    color = score_to_color(total)
    label = score_to_label(total)
    pct = total * 10

    delta_html = ""
    if prev:
        diff = total - prev["total"]
        if diff > 0:
            delta_html = f'<span style="color:#22c55e;font-size:0.8rem;margin-left:6px;">&#9650;{diff:.1f}</span>'
        elif diff < 0:
            delta_html = f'<span style="color:#ef4444;font-size:0.8rem;margin-left:6px;">&#9660;{abs(diff):.1f}</span>'

    rationale = sentiment.get("rationale", "")

    st.html(f"""
    <div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:10px 16px;margin:8px 0;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="color:#94a3b8;font-size:0.75rem;font-weight:600;">SENTIMENT</span>
            <span style="font-size:1.1rem;font-weight:700;color:{color};">{total:.1f}<span style="color:#475569;font-size:0.75rem;">/10</span> {delta_html}</span>
        </div>
        <div style="background:#0f172a;border-radius:4px;height:6px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:4px;">
            <span style="font-size:0.65rem;color:#475569;">Bearish</span>
            <span style="font-size:0.65rem;color:{color};font-weight:500;">{label}</span>
            <span style="font-size:0.65rem;color:#475569;">Bullish</span>
        </div>
        {"<div style='color:#64748b;font-size:0.7rem;margin-top:4px;'>" + rationale + "</div>" if rationale else ""}
    </div>
    """)

st.divider()

# Report body
report_md = report.get("report_markdown", "")
if report_md:
    st.markdown(report_md)
else:
    st.warning("Report body is empty.")

# Keywords
keywords = clean_keywords(report.get("keywords", []))
if keywords:
    st.divider()
    st.markdown(" ".join([f"`{k}`" for k in keywords]))

# Page navigation
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/1_시장심리.py", label="시장심리", icon="\U0001F4C8")
with col2:
    st.page_link("pages/2_지난브리핑.py", label="지난 브리핑", icon="\U0001F4CB")
with col3:
    st.page_link("pages/3_관리.py", label="새 브리핑 요청", icon="\u2699\ufe0f")
