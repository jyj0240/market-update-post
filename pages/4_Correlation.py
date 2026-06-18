import math
from datetime import date

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils import (load_sentiment_history, daily_sentiment_series,
                   fetch_daily_index_closes, render_sidebar, render_nav, inject_css)

st.set_page_config(page_title="Correlation", page_icon="\U0001F4C8", layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={"Get help": None, "Report a Bug": None, "About": None})
inject_css()
render_sidebar()
render_nav()

TICKERS = [("^GSPC", "S&P 500", "#6366f1"), ("^IXIC", "Nasdaq", "#22d3ee")]

st.title("Sentiment ↔ Return Correlation")
st.caption("뉴스 기반 sentiment(레벨/증분)가 *다음* 기간 지수 수익률과 상관이 있는지 검정. "
           "수익률은 ET 거래일 종가수익률, sentiment는 ET 거래일 기준으로 정렬됩니다.")

history = load_sentiment_history()
if not history:
    st.info("No sentiment data yet.")
    st.stop()

sent_map = daily_sentiment_series(history)
if len(sent_map) < 10:
    st.info("상관분석을 위한 데이터가 충분하지 않습니다 (최소 10거래일 필요).")
    st.stop()

dates = sorted(sent_map)
closes = fetch_daily_index_closes(dates[0], date.today().isoformat(),
                                  tickers=[t[0] for t in TICKERS])
if isinstance(closes, dict) and closes.get("error"):
    st.warning(f"지수 데이터를 불러오지 못했습니다: {closes['error'][:80]}")
    st.stop()


def corr_n_t(x, y):
    """(r, n, t-stat) 반환. n<5면 (None, n, None)"""
    df = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    n = len(df)
    if n < 5:
        return None, n, None
    r = df["x"].corr(df["y"])
    if r is None or pd.isna(r):
        return None, n, None
    t = r * math.sqrt((n - 2) / max(1e-9, 1 - r * r))
    return r, n, t


def fmt(r, n, t):
    if r is None:
        return f"n={n} (부족)"
    star = " ★" if (t is not None and abs(t) > 2) else ""
    return f"{r:+.3f}{star}  (n={n})"


sent_series = pd.Series(sent_map)
sent_series.index = pd.to_datetime(sent_series.index)

TESTS = [
    ("동일시점  S_t vs r_t", "same"),
    ("레벨 → 다음날  S_t vs r_{t+1}", "lvl_next"),
    ("증분 → 다음날  ΔS_t vs r_{t+1}", "d_next"),
    ("주간 레벨 → 다음주  WkS vs Wkr_{+1}", "wlvl_next"),
    ("주간 증분 → 다음주  ΔWkS vs Wkr_{+1}", "wd_next"),
]

results = {key: {} for _, key in TESTS}
lag_corr = {}  # ticker -> list of (k, r) for daily level vs r_{t+k}

for tk, name, _ in TICKERS:
    if tk not in closes:
        continue
    cl = pd.Series(closes[tk])
    cl.index = pd.to_datetime(cl.index)
    cl = cl.sort_index()
    ret = cl.pct_change() * 100

    S = sent_series.reindex(ret.index)          # 거래일 기준 sentiment
    dS = S.diff()
    r_next = ret.shift(-1)

    # 주간 (ISO week, 일요일 종료)
    wS = S.resample("W-SUN").mean()
    wret = cl.resample("W-SUN").last().pct_change() * 100
    wdS = wS.diff()
    wret_next = wret.shift(-1)

    results["same"][tk] = corr_n_t(S, ret)
    results["lvl_next"][tk] = corr_n_t(S, r_next)
    results["d_next"][tk] = corr_n_t(dS, r_next)
    results["wlvl_next"][tk] = corr_n_t(wS, wret_next)
    results["wd_next"][tk] = corr_n_t(wdS, wret_next)

    # lag sweep: corr(S_t, r_{t+k}), k = -2..+3  (k>0 = sentiment 선행/예측)
    sweep = []
    for k in range(-2, 4):
        r, n, t = corr_n_t(S, ret.shift(-k))
        sweep.append((k, r if r is not None else 0.0))
    lag_corr[tk] = sweep

# --- 상관 요약 테이블 ---
st.subheader("Correlation Summary")
table = {}
for tk, name, _ in TICKERS:
    table[name] = [fmt(*results[key][tk]) if tk in results[key] else "-"
                   for _, key in TESTS]
df_show = pd.DataFrame(table, index=[label for label, _ in TESTS])
st.table(df_show)
st.caption("★ = |t| > 2 (대략 p<0.05). 동일시점 상관은 sentiment가 당일 시장을 반영해 "
           "생기는 동행이므로 예측력과는 별개입니다. *다음* 기간(→) 상관이 예측력 검정입니다.")

# --- Lag sweep 차트 ---
st.subheader("Lead–Lag Profile")
st.caption("corr( sentimentₜ , returnₜ₊ₖ ). k=0 동일시점, k>0 = sentiment가 미래 수익률을 선행(예측), k<0 = 후행.")
fig = go.Figure()
for tk, name, color in TICKERS:
    if tk not in lag_corr:
        continue
    ks = [k for k, _ in lag_corr[tk]]
    rs = [r for _, r in lag_corr[tk]]
    fig.add_trace(go.Bar(x=[f"k={k:+d}" for k in ks], y=rs, name=name,
                         marker_color=color, opacity=0.8))
fig.add_hline(y=0, line_color="#475569", line_width=1)
fig.update_layout(
    barmode="group", height=320, margin=dict(l=40, r=20, t=10, b=40),
    yaxis=dict(title="correlation", gridcolor="rgba(255,255,255,0.05)", zeroline=False),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8"), hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, use_container_width=True,
                config={"displayModeBar": False, "staticPlot": True})

# --- 산점도: 주간 레벨 → 다음주 수익률 (가장 신호가 있던 검정) ---
st.subheader("Weekly Sentiment vs Next-Week Return")
tab_objs = st.tabs([name for _, name, _ in TICKERS])
for (tk, name, color), tab in zip(TICKERS, tab_objs):
    with tab:
        if tk not in closes:
            st.info("데이터 없음")
            continue
        cl = pd.Series(closes[tk]); cl.index = pd.to_datetime(cl.index); cl = cl.sort_index()
        wS = sent_series.reindex(cl.index).resample("W-SUN").mean()
        wret_next = (cl.resample("W-SUN").last().pct_change() * 100).shift(-1)
        d = pd.concat([wS.rename("S"), wret_next.rename("r")], axis=1).dropna()
        if len(d) < 5:
            st.info("표본 부족")
            continue
        r, n, t = corr_n_t(d["S"], d["r"])
        fig_s = go.Figure(go.Scatter(
            x=d["S"], y=d["r"], mode="markers",
            marker=dict(size=10, color=color, opacity=0.8, line=dict(width=1, color="#1e293b")),
            text=[i.strftime("%m/%d") for i in d.index], hovertemplate="wk %{text}<br>S=%{x:.1f}<br>r=%{y:+.2f}%<extra></extra>",
        ))
        # 회귀선
        try:
            import numpy as np
            m, b = np.polyfit(d["S"], d["r"], 1)
            xs = [d["S"].min(), d["S"].max()]
            fig_s.add_trace(go.Scatter(x=xs, y=[m * x + b for x in xs], mode="lines",
                                       line=dict(color="#f59e0b", width=2, dash="dash"),
                                       hoverinfo="skip", showlegend=False))
        except Exception:
            pass
        fig_s.add_hline(y=0, line_color="#475569", line_width=1)
        fig_s.update_layout(
            height=360, margin=dict(l=50, r=20, t=10, b=45),
            xaxis=dict(title="Weekly avg sentiment", gridcolor="rgba(255,255,255,0.05)", fixedrange=True),
            yaxis=dict(title="Next-week return %", gridcolor="rgba(255,255,255,0.05)", zeroline=False, fixedrange=True),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"), showlegend=False,
        )
        st.plotly_chart(fig_s, use_container_width=True,
                        config={"displayModeBar": False, "staticPlot": True})
        st.caption(f"{name}: r = {r:+.3f} (n={n}, t={t:+.2f}). "
                   + ("약한 양의 관계이나 표본이 작아 단정 불가." if r and abs(t) < 2 else ""))

st.divider()

# --- Nasdaq − S&P 스프레드 예측 (리스크 쏠림) ---
if "^GSPC" in closes and "^IXIC" in closes:
    st.subheader("Risk-On Rotation: Sentiment → Next-Week (Nasdaq − S&P) Spread")
    st.caption("Nasdaq−S&P 스프레드는 공통 시장 베타가 상쇄돼 '리스크 선호/기술주 쏠림'만 남는 지표입니다. "
               "절대수익률보다 변동성이 작아 sentiment 신호가 더 잘 드러납니다.")

    csp = pd.Series(closes["^GSPC"]); csp.index = pd.to_datetime(csp.index); csp = csp.sort_index()
    cnq = pd.Series(closes["^IXIC"]); cnq.index = pd.to_datetime(cnq.index); cnq = cnq.sort_index()
    rsp = csp.resample("W-SUN").last().pct_change() * 100
    rnq = cnq.resample("W-SUN").last().pct_change() * 100
    spread = (rnq - rsp).rename("spread")
    wS_sp = sent_series.resample("W-SUN").mean()

    r_same, n_same, t_same = corr_n_t(wS_sp, spread)
    r_pred, n_pred, t_pred = corr_n_t(wS_sp, spread.shift(-1))

    c1, c2 = st.columns(2)
    c1.metric("동일주  S_w vs 스프레드_w", fmt(r_same, n_same, t_same))
    c2.metric("예측  S_w vs 스프레드_{w+1}", fmt(r_pred, n_pred, t_pred))

    d = pd.concat([wS_sp.rename("S"), spread.shift(-1).rename("sp")], axis=1).dropna()
    if len(d) >= 5:
        fig_sp = go.Figure(go.Scatter(
            x=d["S"], y=d["sp"], mode="markers",
            marker=dict(size=10, color="#22d3ee", opacity=0.85, line=dict(width=1, color="#1e293b")),
            text=[i.strftime("%m/%d") for i in d.index],
            hovertemplate="wk %{text}<br>S=%{x:.1f}<br>spread=%{y:+.2f}%p<extra></extra>",
        ))
        try:
            import numpy as np
            m, b = np.polyfit(d["S"], d["sp"], 1)
            xs = [d["S"].min(), d["S"].max()]
            fig_sp.add_trace(go.Scatter(x=xs, y=[m * x + b for x in xs], mode="lines",
                                        line=dict(color="#f59e0b", width=2, dash="dash"),
                                        hoverinfo="skip", showlegend=False))
        except Exception:
            pass
        fig_sp.add_hline(y=0, line_color="#475569", line_width=1)
        fig_sp.update_layout(
            height=360, margin=dict(l=50, r=20, t=10, b=45),
            xaxis=dict(title="Weekly avg sentiment", gridcolor="rgba(255,255,255,0.05)", fixedrange=True),
            yaxis=dict(title="Next-week (Nasdaq − S&P) %p", gridcolor="rgba(255,255,255,0.05)",
                       zeroline=False, fixedrange=True),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"), showlegend=False,
        )
        st.plotly_chart(fig_sp, use_container_width=True,
                        config={"displayModeBar": False, "staticPlot": True})

        # 상/하위 그룹 다음주 스프레드
        med = d["S"].median()
        hi = d[d["S"] >= med]["sp"]; lo = d[d["S"] < med]["sp"]
        st.caption(
            f"sentiment 상위 {len(hi)}주 → 다음주 Nasdaq이 S&P 대비 평균 {hi.mean():+.2f}%p, "
            f"하위 {len(lo)}주 → {lo.mean():+.2f}%p (차이 {hi.mean()-lo.mean():+.2f}%p). "
            + ("예측 상관이 유의(|t|>2) — 지금까지 중 가장 강한 신호이나 n이 작아 다중검정·단일국면 주의."
               if t_pred is not None and abs(t_pred) > 2
               else "표본이 작아 아직 확정적이지 않음.")
        )

st.divider()
st.caption("⚠️ 표본이 작고(수개월) sentiment는 키워드 기반 간이 점수이며 단일 국면입니다. "
           "탐색적 참고용이며 투자 신호로 단정하지 마세요.")
