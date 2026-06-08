import streamlit as st
from utils import (
    list_available_dates,
    list_reports_for_date,
    load_report,
    format_time_label,
    format_sentiment_gauge,
)

st.set_page_config(page_title="히스토리", page_icon="\U0001F4CB")
st.title("브리핑 히스토리")

dates = list_available_dates()

if not dates:
    st.info("저장된 브리핑이 없습니다.")
    st.stop()

selected_date = st.selectbox("날짜 선택", dates, format_func=lambda d: d)

reports = list_reports_for_date(selected_date)

if not reports:
    st.warning(f"{selected_date}에 생성된 브리핑이 없습니다.")
    st.stop()

# 시간별 탭
time_labels = [format_time_label(r) for r in reports]
tabs = st.tabs(time_labels)

for tab, filename in zip(tabs, reports):
    with tab:
        report = load_report(selected_date, filename)
        if report is None:
            st.error("리포트를 불러올 수 없습니다.")
            continue

        # 센티멘트
        sentiment = report.get("sentiment")
        if sentiment and sentiment.get("total") is not None:
            gauge = format_sentiment_gauge(sentiment["total"])
            st.markdown(f"`{gauge}`")

        # 본문
        report_md = report.get("report_markdown", "")
        if report_md:
            with st.expander("전체 브리핑 보기", expanded=True):
                st.markdown(report_md)

        # 키워드
        keywords = report.get("keywords", [])
        if keywords:
            st.write(" ".join([f"`{k}`" for k in keywords]))
