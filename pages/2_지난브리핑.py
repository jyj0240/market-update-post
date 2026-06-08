import streamlit as st
from utils import (list_available_dates, list_reports_for_date, load_report,
                   format_time_label, score_to_color, score_to_label, clean_keywords, render_sidebar)
from style import inject_css

st.set_page_config(page_title="History", page_icon="\U0001F4C8", layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={"Get help": None, "Report a Bug": None, "About": None})
inject_css()
render_sidebar()

st.title("Past Briefings")

dates = list_available_dates()
if not dates:
    st.info("No saved briefings.")
    st.stop()

selected_date = st.selectbox("Date", dates)
reports = list_reports_for_date(selected_date)

if not reports:
    st.warning(f"No briefings for {selected_date}.")
    st.stop()

time_labels = [format_time_label(r) for r in reports]
tabs = st.tabs(time_labels)

for tab, filename in zip(tabs, reports):
    with tab:
        report = load_report(selected_date, filename)
        if report is None:
            st.error("Failed to load report.")
            continue

        # Sentiment card
        sentiment = report.get("sentiment")
        if sentiment and sentiment.get("total") is not None:
            score = sentiment["total"]
            color = score_to_color(score)
            label = score_to_label(score)
            st.html(f"""
            <div style="display:flex; align-items:center; gap:1rem; background:#1e293b;
                        border-radius:10px; padding:12px 16px; border:1px solid #334155;
                        margin-bottom:1rem;">
                <span style="font-size:1.6rem; font-weight:700; color:{color};">{score:.1f}</span>
                <span style="color:#64748b; font-size:0.85rem;">/10 {label}</span>
                <span style="color:#475569; font-size:0.8rem; margin-left:auto;">
                    {sentiment.get("rationale", "")}
                </span>
            </div>
            """)

        # Keywords
        keywords = clean_keywords(report.get("keywords", []))
        if keywords:
            st.markdown(" ".join([f"`{k}`" for k in keywords]))

        # Full briefing
        report_md = report.get("report_markdown", "")
        if report_md:
            with st.expander("Full Briefing", expanded=False):
                st.markdown(report_md)
