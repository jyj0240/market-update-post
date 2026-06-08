import streamlit as st
from utils import load_latest, load_sentiment_history, format_sentiment_gauge

st.set_page_config(
    page_title="Market Update",
    page_icon="\U0001F4C8",
    layout="wide",
)

st.title("Market Briefing")

report = load_latest()

if report is None:
    st.info("아직 등록된 브리핑이 없습니다. 첫 브리핑이 생성되면 자동으로 표시됩니다.")
    st.stop()

# 업데이트 시각만 간결하게 표시
gen_at = report.get("generated_at", "")
if gen_at:
    gen_at = gen_at[:16].replace("T", " ")
    st.caption(f"Updated: {gen_at}")

# 센티멘트 게이지
sentiment = report.get("sentiment")
if sentiment and sentiment.get("total") is not None:
    history = load_sentiment_history()
    prev_score = history[-2]["total"] if len(history) >= 2 else None
    gauge = format_sentiment_gauge(sentiment["total"], prev_score)
    st.markdown(f"**시장 심리** `{gauge}`")
    if sentiment.get("rationale"):
        st.caption(sentiment["rationale"])

st.divider()

# 본문
report_md = report.get("report_markdown", "")
if report_md:
    st.markdown(report_md)
else:
    st.warning("리포트 본문이 비어있습니다.")

# 키워드
keywords = report.get("keywords", [])
if keywords:
    st.divider()
    st.subheader("Keywords")
    st.write(" ".join([f"`{k}`" for k in keywords]))
