import streamlit as st
import time
from datetime import datetime
from utils import load_latest, load_sentiment_history, score_to_color, score_to_label, clean_keywords, render_sidebar
from style import inject_css

st.set_page_config(
    page_title="Market Briefing",
    page_icon="\U0001F4C8",
    layout="wide",
    initial_sidebar_state="collapsed",
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

# Sentiment metric cards
sentiment = report.get("sentiment")
if sentiment and sentiment.get("total") is not None:
    history = load_sentiment_history()
    prev = history[-2] if len(history) >= 2 else None

    st.markdown("")
    cols = st.columns([1.5, 1, 1, 1, 1, 1])

    total = sentiment["total"]
    delta_total = round(total - prev["total"], 1) if prev else None
    with cols[0]:
        st.metric("Overall Sentiment", f"{total:.1f} / 10",
                  delta=f"{delta_total:+.1f}" if delta_total is not None else None)

    component_map = {
        "Equity": "equity_direction",
        "Volatility": "volatility",
        "Risk Appetite": "risk_appetite",
        "Geopolitical": "geopolitical_macro",
        "Tone": "participant_tone",
    }
    for col, (name, key) in zip(cols[1:], component_map.items()):
        val = sentiment.get(key)
        prev_val = prev.get(key) if prev else None
        delta = round(val - prev_val, 1) if val is not None and prev_val is not None else None
        delta_color = "inverse" if key == "volatility" else "normal"
        with col:
            st.metric(name, f"{val:.1f}" if val is not None else "--",
                      delta=f"{delta:+.1f}" if delta is not None else None,
                      delta_color=delta_color)

    if sentiment.get("rationale"):
        st.caption(sentiment["rationale"])

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
