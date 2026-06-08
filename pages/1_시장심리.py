import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import load_sentiment_history, score_to_color, score_to_label, render_sidebar
from style import inject_css

st.set_page_config(page_title="Market Sentiment", page_icon="\U0001F4C8", layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={"Get help": None, "Report a Bug": None, "About": None})
inject_css()
render_sidebar()

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
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

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
    st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})

if latest.get("rationale"):
    st.caption(latest["rationale"])

st.divider()

# Historical chart
st.subheader("Sentiment Trend")

dates = [h.get("datetime", "")[:16].replace("T", " ") for h in history]
totals = [h.get("total") for h in history]

fig_hist = go.Figure()

# Zone backgrounds
fig_hist.add_hrect(y0=0, y1=3, fillcolor="rgba(239,68,68,0.05)", line_width=0)
fig_hist.add_hrect(y0=7, y1=10, fillcolor="rgba(34,197,94,0.05)", line_width=0)

fig_hist.add_trace(go.Scatter(
    x=dates, y=totals, mode="lines+markers", name="Overall",
    line=dict(color="#6366f1", width=2.5, shape="spline"),
    marker=dict(size=7, color=[score_to_color(t) for t in totals],
                line=dict(width=1, color="#1e293b")),
    fill="tozeroy", fillcolor="rgba(99,102,241,0.08)",
))

fig_hist.add_hline(y=5, line_dash="dot", line_color="#475569", line_width=1)

fig_hist.update_layout(
    yaxis=dict(range=[0, 10.5], dtick=2, gridcolor="rgba(255,255,255,0.05)"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    height=350, margin=dict(l=40, r=20, t=10, b=40),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8"), showlegend=False, hovermode="x unified",
)
st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

# Component heatmap
if len(history) > 1:
    st.subheader("Component Breakdown")

    labels = ["Equity", "Volatility (inv.)", "Risk Appetite", "Geopolitical", "Tone"]
    hm_keys = ["equity_direction", "volatility", "risk_appetite", "geopolitical_macro", "participant_tone"]

    z = []
    for k in hm_keys:
        row = []
        for h in history:
            v = h.get(k, 5)
            if k == "volatility":
                v = 10 - v
            row.append(v)
        z.append(row)

    fig_hm = go.Figure(go.Heatmap(
        z=z, x=dates, y=labels,
        colorscale=[[0, "#ef4444"], [0.3, "#f97316"], [0.5, "#64748b"],
                    [0.7, "#22c55e"], [1, "#10b981"]],
        zmin=0, zmax=10,
        colorbar=dict(title="Score", tickvals=[0, 5, 10],
                      ticktext=["Bear", "Neutral", "Bull"], len=0.8),
    ))
    fig_hm.update_layout(
        height=220, margin=dict(l=100, r=20, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"), yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig_hm, use_container_width=True, config={"displayModeBar": False})

# Recent readings
st.subheader("Recent Readings")
recent = list(reversed(history[-6:]))
cols = st.columns(len(recent))
for col, h in zip(cols, recent):
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
