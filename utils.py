import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = DATA_DIR / "reports"

# 센티멘트 타임스탬프는 KST(미국장 마감+1h = 익일 새벽). 지수 수익률은 ET 거래일 기준 주차이므로
# 주차 정렬을 맞추려면 센티멘트도 ET 거래일로 환산해 ISO 주차에 넣어야 함.
# zoneinfo는 IANA tz DB가 필요(requirements의 tzdata). DB가 없는 환경이어도 앱이 죽지 않도록
# 고정 오프셋으로 폴백 (KST=+9, ET=-5 근사).
try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
    ET = ZoneInfo("America/New_York")
except Exception:  # tz DB 부재 등
    KST = timezone(timedelta(hours=9))
    ET = timezone(timedelta(hours=-5))

SENTIMENT_KEYS = ["total", "equity_direction", "volatility", "risk_appetite",
                  "geopolitical_macro", "participant_tone"]

CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
.block-container {padding-top: 1rem !important; max-width: 900px !important;}
div[data-testid="stMetric"] {
    background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 0.5rem 0.75rem;
}
div[data-testid="stMetric"] label {
    font-size: 0.65rem !important; text-transform: uppercase; letter-spacing: 0.04em;
    font-weight: 600 !important; color: #94a3b8 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1rem !important; font-weight: 700 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.7rem !important;
}
.stMarkdown code {
    background: #312e81 !important; color: #a5b4fc !important;
    border: 1px solid #4338ca !important; border-radius: 12px !important;
    padding: 2px 10px !important; font-size: 0.8rem !important;
}
hr {border-color: #334155 !important; margin: 1rem 0 !important;}
section[data-testid="stSidebar"] {background: #0f172a;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def render_nav():
    st.html("""
    <div style="display:flex;gap:12px;padding:4px 0 8px 0;font-size:0.8rem;">
        <a href="/" target="_self" style="color:#94a3b8;text-decoration:none;">Briefing</a>
        <a href="/Sentiment" target="_self" style="color:#94a3b8;text-decoration:none;">Sentiment</a>
        <a href="/Correlation" target="_self" style="color:#94a3b8;text-decoration:none;">Correlation</a>
        <a href="/History" target="_self" style="color:#94a3b8;text-decoration:none;">History</a>
        <a href="/Request" target="_self" style="color:#94a3b8;text-decoration:none;">Request</a>
    </div>
    """)


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:1rem 0;">
            <h2 style="margin:0; font-size:1.3rem; font-weight:700; color:#e2e8f0;">Market Briefing</h2>
            <p style="color:#64748b; font-size:0.8rem; margin:0.25rem 0 0 0;">AI-Powered Intelligence</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        history = load_sentiment_history()
        if history:
            latest = history[-1]
            total = latest.get("total", 0)
            prev = history[-2].get("total") if len(history) >= 2 else None
            delta = None
            if prev is not None:
                delta = f"{total - prev:+.1f}"
            st.metric("Sentiment", f"{total:.1f}/10", delta=delta)
        st.divider()
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption("Auto-refreshes every 5 min.")


@st.cache_data(ttl=300)
def load_latest():
    latest_path = DATA_DIR / "latest.json"
    if not latest_path.exists():
        return None
    with open(latest_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    report_path = Path(__file__).parent / meta.get("latest_report", "")
    if not report_path.exists():
        return None
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    report["_meta"] = meta
    return report


@st.cache_data(ttl=300)
def load_report(date_str, filename):
    path = REPORTS_DIR / date_str / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def load_sentiment_history():
    path = DATA_DIR / "sentiment.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def list_available_dates():
    if not REPORTS_DIR.exists():
        return []
    return sorted([d.name for d in REPORTS_DIR.iterdir() if d.is_dir()], reverse=True)


@st.cache_data(ttl=300)
def list_reports_for_date(date_str):
    date_dir = REPORTS_DIR / date_str
    if not date_dir.exists():
        return []
    return sorted([f.name for f in date_dir.glob("*_briefing.json")])


def format_time_label(filename):
    base = filename.replace("_briefing.json", "")
    if len(base) == 4 and base.isdigit():
        return f"{base[:2]}:{base[2:]}"
    return base


def score_to_color(score):
    if score is None:
        return "#64748b"
    if score <= 3:
        return "#ef4444"
    elif score <= 5:
        return "#eab308"
    elif score <= 7:
        return "#22c55e"
    return "#10b981"


def score_to_label(score):
    if score is None:
        return "-"
    if score <= 3:
        return "Bearish"
    elif score <= 5:
        return "Neutral"
    elif score <= 7:
        return "Bullish"
    return "Very Bullish"


def clean_keywords(keywords):
    return [k for k in keywords
            if not any(k.startswith(f"{i}.") for i in range(1, 7))
            and 2 < len(k) < 30]


def _parse_dt(s):
    """ISO 문자열 → tz-aware datetime. naive면 KST로 간주.
    (백필=naive KST, 라이브=aware(+로컬오프셋) 혼재 시 비교/정렬 TypeError 방지)"""
    try:
        dt = datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None
    return dt.replace(tzinfo=KST) if dt.tzinfo is None else dt


def bucket_sentiment_history(history, recent_days=7):
    """sentiment 이력을 (recent, weekly)로 분리.

    recent : 가장 최근 entry 기준 recent_days 이내의 개별 entry (시간순)
    weekly : 그보다 오래된 entry를 ISO 주차별로 평균낸 dict 리스트 (시간순)
             각 dict: {label, week_start(ISO date), datetime, count, <SENTIMENT_KEYS>}
    """
    parsed = [(dt, h) for h in history if (dt := _parse_dt(h.get("datetime", "")))]
    parsed.sort(key=lambda x: x[0])
    if not parsed:
        return [], []

    latest = parsed[-1][0]
    cutoff = latest - timedelta(days=recent_days)
    recent = [h for dt, h in parsed if dt >= cutoff]
    older = [(dt, h) for dt, h in parsed if dt < cutoff]

    # ET 거래일 기준 ISO 주차로 묶어 지수 수익률 주차와 정렬을 일치시킴
    buckets = {}
    for dt, h in older:
        et_date = (dt.replace(tzinfo=KST) if dt.tzinfo is None else dt).astimezone(ET).date()
        iso = et_date.isocalendar()
        buckets.setdefault((iso[0], iso[1]), []).append((et_date, h))

    weekly = []
    for key in sorted(buckets):
        items = buckets[key]
        d0 = items[0][0]
        monday = d0 - timedelta(days=d0.weekday())
        agg = {
            "label": f"Wk {monday.strftime('%m/%d')}",
            "week_start": monday.isoformat(),
            "datetime": monday.isoformat(),
            "count": len(items),
        }
        for k in SENTIMENT_KEYS:
            vals = [hh.get(k) for _, hh in items if isinstance(hh.get(k), (int, float))]
            agg[k] = round(sum(vals) / len(vals), 2) if vals else None
        weekly.append(agg)

    return recent, weekly


@st.cache_data(ttl=3600)
def fetch_weekly_index_returns(start_iso, end_iso, tickers=("^GSPC", "^IXIC")):
    """yfinance로 주간(ISO week, 월요일 기준) 지수 수익률(%)을 계산.

    반환: 성공 시 list[{week_start, week_label, returns:{ticker: pct|None}}],
          실패 시 {"error": msg}
    """
    tickers = tuple(tickers)
    try:
        import yfinance as yf
        import pandas as pd

        df = yf.download(list(tickers), start=start_iso, end=end_iso,
                         progress=False, auto_adjust=True)
        if df is None or df.empty:
            return {"error": "no data returned"}

        close = df["Close"] if "Close" in df.columns.get_level_values(0) else df
        if isinstance(close, pd.Series):
            close = close.to_frame(name=tickers[0])

        # ISO 주차(월~일)와 정렬: 일요일 종료 주간 bin의 마지막 종가
        weekly = close.resample("W-SUN").last()
        ret = (weekly.pct_change() * 100).dropna(how="all")

        out = []
        for idx, row in ret.iterrows():
            monday = (idx.date() - timedelta(days=6))
            out.append({
                "week_start": monday.isoformat(),
                "week_label": f"Wk {monday.strftime('%m/%d')}",
                "returns": {
                    t: (round(float(row[t]), 2)
                        if t in row.index and pd.notna(row[t]) else None)
                    for t in tickers
                },
            })
        return out
    except Exception as e:  # 네트워크/yfinance 오류 시 graceful fallback
        return {"error": str(e)}


def daily_sentiment_series(history):
    """ET 거래일 기준 일별 평균 sentiment total. 반환: dict {date_iso(str): float} (날짜 오름차순)"""
    rows = {}
    for h in history:
        dt = _parse_dt(h.get("datetime", ""))
        if not dt:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        d = dt.astimezone(ET).date().isoformat()
        v = h.get("total")
        if isinstance(v, (int, float)):
            rows.setdefault(d, []).append(v)
    return {d: sum(v) / len(v) for d, v in sorted(rows.items())}


@st.cache_data(ttl=3600)
def fetch_daily_index_closes(start_iso, end_iso, tickers=("^GSPC", "^IXIC")):
    """yfinance로 일별 종가를 받아 {ticker: {date_iso: close}} 반환. 실패 시 {"error": msg}"""
    tickers = tuple(tickers)
    try:
        import yfinance as yf
        import pandas as pd

        df = yf.download(list(tickers), start=start_iso, end=end_iso,
                         progress=False, auto_adjust=True)
        if df is None or df.empty:
            return {"error": "no data returned"}
        close = df["Close"] if "Close" in df.columns.get_level_values(0) else df
        if isinstance(close, pd.Series):
            close = close.to_frame(name=tickers[0])
        out = {}
        for t in tickers:
            if t in close.columns:
                s = close[t].dropna()
                out[t] = {idx.date().isoformat(): float(v) for idx, v in s.items()}
        return out if out else {"error": "no matching tickers"}
    except Exception as e:
        return {"error": str(e)}
