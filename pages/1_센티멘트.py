import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import load_sentiment_history, format_sentiment_gauge

st.set_page_config(page_title="센티멘트", page_icon="\U0001F4C8")
st.title("시장 센티멘트 추이")

history = load_sentiment_history()

if not history:
    st.info("센티멘트 데이터가 아직 없습니다.")
    st.stop()

# 최신 센티멘트
latest = history[-1]
prev = history[-2] if len(history) >= 2 else None
gauge = format_sentiment_gauge(
    latest.get("total"), prev.get("total") if prev else None
)
st.markdown(f"**현재 시장 심리** `{gauge}`")
if latest.get("rationale"):
    st.caption(latest["rationale"])

st.divider()

# 차트 데이터 준비
dates = [h.get("datetime", "")[:16].replace("T", " ") for h in history]
totals = [h.get("total") for h in history]

components = {
    "주식 방향성": "equity_direction",
    "변동성": "volatility",
    "위험선호": "risk_appetite",
    "지정학/매크로": "geopolitical_macro",
    "참여자 톤": "participant_tone",
}

# 종합 스코어 차트
fig = make_subplots(rows=2, cols=1, row_heights=[0.6, 0.4],
                    subplot_titles=["종합 센티멘트 (0-10)", "세부 항목별"],
                    vertical_spacing=0.15)

fig.add_trace(
    go.Scatter(x=dates, y=totals, mode="lines+markers", name="종합",
               line=dict(color="#1f77b4", width=3), marker=dict(size=6)),
    row=1, col=1,
)
fig.add_hline(y=5, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=1)

# 세부 항목
colors = ["#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
for (label, key), color in zip(components.items(), colors):
    values = [h.get(key) for h in history]
    if any(v is not None for v in values):
        fig.add_trace(
            go.Scatter(x=dates, y=values, mode="lines", name=label,
                       line=dict(color=color, width=1.5)),
            row=2, col=1,
        )

fig.update_yaxes(range=[0, 10], row=1, col=1)
fig.update_yaxes(range=[0, 10], row=2, col=1)
fig.update_layout(height=600, showlegend=True, legend=dict(orientation="h", y=-0.1))

st.plotly_chart(fig, use_container_width=True)

# 테이블
st.subheader("최근 기록")
table_data = []
for h in reversed(history[-20:]):
    dt = h.get("datetime", "")[:16].replace("T", " ")
    total = h.get("total", "-")
    rationale = h.get("rationale", "")
    if len(rationale) > 60:
        rationale = rationale[:60] + "..."
    table_data.append({"시각": dt, "종합": total, "요약": rationale})

st.dataframe(table_data, use_container_width=True, hide_index=True)
