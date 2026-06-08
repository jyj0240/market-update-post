import streamlit as st
import time
import re
import plotly.graph_objects as go
from utils import (load_latest, load_sentiment_history, score_to_color,
                   score_to_label, clean_keywords, render_sidebar, render_nav, inject_css)

st.set_page_config(
    page_title="Market Briefing",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get help": None, "Report a Bug": None, "About": None},
)
inject_css()

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if time.time() - st.session_state.last_refresh > 300:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()

render_sidebar()
render_nav()

report = load_latest()

if report is None:
    st.title("Market Briefing")
    st.info("No briefings available yet.")
    st.stop()

# Header
gen_at = report.get("generated_at", "")
updated_label = ""
if gen_at:
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(gen_at)
        updated_label = dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        updated_label = gen_at[:16].replace("T", " ")

st.html(f"""
<div style="
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white; padding: 1.2rem 1.5rem; border-radius: 12px; border: 1px solid #334155;
">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1 style="margin:0; font-size:1.5rem; font-weight:700;">Market Briefing</h1>
            <p style="color:#a8b2d1; font-size:0.8rem; margin:0.2rem 0 0 0;">AI-Generated Market Intelligence</p>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.65rem; color:#a8b2d1; text-transform:uppercase;">Updated</div>
            <div style="font-size:0.85rem; font-weight:600;">{updated_label}</div>
        </div>
    </div>
</div>
""")

# Sentiment bar
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
    rat_html = f'<div style="color:#64748b;font-size:0.7rem;margin-top:4px;">{rationale}</div>' if rationale else ""

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
        {rat_html}
    </div>
    """)

# Asset direction chart
def parse_asset_directions(text):
    """리포트에서 자산별 방향 추출"""
    assets = {}
    patterns = {
        "US Equities": r"(?:미국 주식|US Equities?|주식).*?\[(.*?)\]",
        "Bonds": r"(?:채권|금리|Bonds?|Rates?).*?\[(.*?)\]",
        "Commodities": r"(?:원자재|Commodit).*?\[(.*?)\]",
        "FX/USD": r"(?:달러|환율|FX|USD).*?\[(.*?)\]",
        "Crypto": r"(?:암호화폐|Crypto|BTC).*?\[(.*?)\]",
    }
    for asset, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            direction = m.group(1).strip()
            if any(w in direction for w in ["상승", "강세", "Up", "상"]):
                assets[asset] = 1
            elif any(w in direction for w in ["하락", "약세", "Down", "하"]):
                assets[asset] = -1
            else:
                assets[asset] = 0
    return assets

report_md = report.get("report_markdown", "")
assets = parse_asset_directions(report_md)
if assets:
    names = list(assets.keys())
    values = list(assets.values())
    colors = ["#22c55e" if v > 0 else "#ef4444" if v < 0 else "#64748b" for v in values]
    symbols = ["\u25b2" if v > 0 else "\u25bc" if v < 0 else "\u25b6" for v in values]

    asset_html = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;">'
    for name, val, col, sym in zip(names, values, colors, symbols):
        asset_html += f'''
        <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;
                    padding:6px 12px;flex:1;min-width:100px;text-align:center;">
            <div style="color:#94a3b8;font-size:0.65rem;">{name}</div>
            <div style="color:{col};font-size:1.1rem;font-weight:700;">{sym}</div>
        </div>'''
    asset_html += '</div>'
    st.html(asset_html)

st.divider()

# Language toggle
has_en = bool(report.get("report_markdown_en"))
if has_en:
    lang = st.toggle("English", value=False)
    content_md = report.get("report_markdown_en", "") if lang else report_md
else:
    content_md = report_md

if content_md:
    st.markdown(content_md)
else:
    st.warning("Report body is empty.")

# Keywords
keywords = clean_keywords(report.get("keywords", []))
if keywords:
    st.divider()
    st.markdown(" ".join([f"`{k}`" for k in keywords]))
