from datetime import date
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (load_sentiment_history, score_to_color, score_to_label,
                   bucket_sentiment_history, fetch_weekly_index_returns,
                   render_sidebar, render_nav, inject_css)

INDEX_TICKERS = [("^GSPC", "S&P 500", "#6366f1"), ("^IXIC", "Nasdaq", "#22d3ee")]

st.set_page_config(page_title="Market Sentiment", page_icon="\U0001F4C8", layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={"Get help": None, "Report a Bug": None, "About": None})
inject_css()
render_sidebar()
render_nav()

st.title("Market Sentiment")

history = load_sentiment_history()
if not history:
    st.info("No sentiment data yet.")
    st.stop()

latest = history[-1]
prev = history[-2] if len(history) >= 2 else None
total = latest.get("total", 0)

# Top row: gauge + radar
col_gauge, col_radar = st.columns([3, 2])

with col_gauge:
    color = score_to_color(total)
    label = score_to_label(total)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total,
        number={"suffix": "/10", "font": {"size": 42, "color": "#e2e8f0"}},
        delta={"reference": prev["total"] if prev else total,
               "increasing": {"color": "#22c55e"},
               "decreasing": {"color": "#ef4444"},
               "font": {"size": 16}} if prev else None,
        title={"text": label, "font": {"size": 14, "color": "#94a3b8"}},
        gauge={
            "axis": {"range": [0, 10], "tickwidth": 0, "dtick": 2,
                     "tickfont": {"color": "#64748b"}},
            "bar": {"color": color, "thickness": 0.7},
            "bgcolor": "#1e293b",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 3], "color": "rgba(239,68,68,0.1)"},
                {"range": [3, 5], "color": "rgba(234,179,8,0.08)"},
                {"range": [5, 7], "color": "rgba(34,197,94,0.08)"},
                {"range": [7, 10], "color": "rgba(16,185,129,0.1)"},
            ],
        },
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", font={"color": "#e2e8f0"})
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

with col_radar:
    cats = ["Equity", "Vol (inv.)", "Risk App.", "Geopolitical", "Tone"]
    keys = ["equity_direction", "volatility", "risk_appetite", "geopolitical_macro", "participant_tone"]
    vals = []
    for k in keys:
        v = latest.get(k, 5)
        if k == "volatility":
            v = 10 - v
        vals.append(v)
    vals.append(vals[0])
    cats.append(cats[0])

    fig_r = go.Figure(go.Scatterpolar(
        r=vals, theta=cats, fill="toself",
        fillcolor="rgba(99,102,241,0.15)",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=6, color="#6366f1"),
    ))
    fig_r.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 10],
                           tickfont=dict(size=9, color="#64748b"),
                           gridcolor="rgba(255,255,255,0.08)"),
            angularaxis=dict(tickfont=dict(size=11, color="#94a3b8"),
                            gridcolor="rgba(255,255,255,0.08)"),
        ),
        showlegend=False, height=280, margin=dict(l=60, r=60, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

if latest.get("rationale"):
    st.caption(latest["rationale"])

st.divider()

recent, weekly = bucket_sentiment_history(history, recent_days=7)

# ---------------------------------------------------------------
# Weekly view (1주 이상 지난 구간): 주간 sentiment + 주간 지수 수익률
# ---------------------------------------------------------------
if weekly:
    st.subheader("Weekly Sentiment & Index Returns")
    st.caption("1주 이상 지난 구간은 주간 평균으로 집계합니다.")

    idx_data = fetch_weekly_index_returns(weekly[0]["week_start"], date.today().isoformat(),
                                          tickers=[t[0] for t in INDEX_TICKERS])
    sent_by_week = {w["week_start"]: w.get("total") for w in weekly}

    if isinstance(idx_data, list) and idx_data:
        idx_by_week = {it["week_start"]: it["returns"] for it in idx_data}
    else:
        idx_by_week = {}
        if isinstance(idx_data, dict) and idx_data.get("error"):
            st.caption(f":warning: 지수 데이터를 불러오지 못했습니다 ({idx_data['error'][:60]}).")

    # x축 = sentiment·지수 둘 다 있는 주(교집합)만 사용.
    # 합집합을 쓰면 양 끝에 한쪽만 있는 주가 생겨(맨앞 sentiment-only, 맨뒤 index-only)
    # 라인이 막대보다 한 칸 밀려 보이는 '래깅 착시'가 생김.
    if idx_by_week:
        weeks = sorted(set(sent_by_week) & set(idx_by_week))
    else:
        weeks = sorted(sent_by_week)
    x_labels = [f"Wk {date.fromisoformat(w).strftime('%m/%d')}" for w in weeks]

    fig_w = make_subplots(specs=[[{"secondary_y": True}]])
    for ticker, name, color in INDEX_TICKERS:
        fig_w.add_trace(go.Bar(
            x=x_labels,
            y=[idx_by_week.get(w, {}).get(ticker) for w in weeks],
            name=name, marker_color=color, opacity=0.75,
        ), secondary_y=False)
    fig_w.add_trace(go.Scatter(
        x=x_labels, y=[sent_by_week.get(w) for w in weeks],
        name="Sentiment", mode="lines+markers",
        line=dict(color="#f59e0b", width=2.5),  # 직선(보간 곡선이 주는 위상 왜곡 방지)
        marker=dict(size=7, color="#f59e0b"), connectgaps=True,
    ), secondary_y=True)

    fig_w.add_hline(y=0, line_dash="dot", line_color="#475569", line_width=1, secondary_y=False)
    # 두 축 모두 고정(터치/핀치 줌·패닝 완전 차단). 전체 주를 다 표시해 패닝 없이도 과거가 보임.
    fig_w.update_yaxes(title_text="Weekly Return %", gridcolor="rgba(255,255,255,0.05)",
                       zeroline=False, fixedrange=True, secondary_y=False)
    fig_w.update_yaxes(title_text="Sentiment", range=[0, 10], dtick=2,
                       showgrid=False, fixedrange=True, secondary_y=True)
    fig_w.update_xaxes(gridcolor="rgba(255,255,255,0.05)", fixedrange=True)
    fig_w.update_layout(
        barmode="group", height=380, margin=dict(l=40, r=40, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"), hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_w, use_container_width=True,
                    config={"displayModeBar": False, "staticPlot": True})

# ---------------------------------------------------------------
# Recent daily trend (최근 7일)
# ---------------------------------------------------------------
st.subheader("Recent Sentiment (Daily)")

dates = [h.get("datetime", "")[:16].replace("T", " ") for h in recent]
totals = [h.get("total") for h in recent]

fig_hist = go.Figure()
fig_hist.add_hrect(y0=0, y1=3, fillcolor="rgba(239,68,68,0.05)", line_width=0)
fig_hist.add_hrect(y0=7, y1=10, fillcolor="rgba(34,197,94,0.05)", line_width=0)
fig_hist.add_trace(go.Scatter(
    x=dates, y=totals, mode="lines+markers", name="Overall",
    line=dict(color="#6366f1", width=2.5, shape="spline"),
    marker=dict(size=8, color=[score_to_color(t) for t in totals],
                line=dict(width=1, color="#1e293b")),
    fill="tozeroy", fillcolor="rgba(99,102,241,0.08)",
))
fig_hist.add_hline(y=5, line_dash="dot", line_color="#475569", line_width=1)
fig_hist.update_layout(
    yaxis=dict(range=[0, 10.5], dtick=2, gridcolor="rgba(255,255,255,0.05)"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    height=320, margin=dict(l=40, r=20, t=10, b=40),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8"), showlegend=False, hovermode="x unified",
)
st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

# Recent readings
st.subheader("Recent Readings")
recent_cards = list(reversed(recent[-6:])) if recent else list(reversed(history[-6:]))
cols = st.columns(len(recent_cards))
for col, h in zip(cols, recent_cards):
    score = h.get("total", 0)
    dt_str = h.get("datetime", "")[:16].replace("T", " ")
    time_only = dt_str.split(" ")[-1] if " " in dt_str else dt_str
    color = score_to_color(score)
    with col:
        st.html(f"""
        <div style="text-align:center; background:#1e293b; border-radius:10px;
                    padding:12px 8px; border:1px solid #334155;">
            <div style="color:#64748b; font-size:0.7rem;">{time_only}</div>
            <div style="color:{color}; font-size:1.5rem; font-weight:700; margin:4px 0;">
                {score:.1f}
            </div>
            <div style="color:#475569; font-size:0.65rem;">/10</div>
        </div>
        """)
