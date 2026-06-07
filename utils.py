import json
import os
from pathlib import Path
from datetime import datetime

import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = DATA_DIR / "reports"


@st.cache_data(ttl=300)
def load_latest():
    """최신 리포트 포인터 로드 후 해당 리포트 반환"""
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
def load_report(date_str: str, filename: str):
    """특정 날짜/파일명의 리포트 로드"""
    path = REPORTS_DIR / date_str / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def load_sentiment_history():
    """센티멘트 히스토리 로드"""
    path = DATA_DIR / "sentiment.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def list_available_dates():
    """사용 가능한 날짜 목록 (최신순)"""
    if not REPORTS_DIR.exists():
        return []
    dates = sorted(
        [d.name for d in REPORTS_DIR.iterdir() if d.is_dir()],
        reverse=True,
    )
    return dates


@st.cache_data(ttl=300)
def list_reports_for_date(date_str: str):
    """특정 날짜의 리포트 파일 목록 (시간순)"""
    date_dir = REPORTS_DIR / date_str
    if not date_dir.exists():
        return []
    files = sorted([f.name for f in date_dir.glob("*_briefing.json")])
    return files


def format_time_label(filename: str) -> str:
    """파일명에서 시간 라벨 추출 (0505_briefing.json -> 05:05)"""
    base = filename.replace("_briefing.json", "")
    if len(base) == 4 and base.isdigit():
        return f"{base[:2]}:{base[2:]}"
    return base


def format_sentiment_gauge(score, prev_score=None):
    """텍스트 기반 센티멘트 게이지"""
    if score is None:
        return "센티멘트 데이터 없음"
    filled = round(score)
    empty = 10 - filled
    bar = "\u2588" * filled + "\u2591" * empty

    if score <= 2:
        label = "매우 부정적"
    elif score <= 4:
        label = "부정적"
    elif score <= 6:
        label = "중립"
    elif score <= 8:
        label = "긍정적"
    else:
        label = "매우 긍정적"

    delta_str = ""
    if prev_score is not None:
        diff = score - prev_score
        if diff > 0:
            delta_str = f" (\u25b2{diff:.1f})"
        elif diff < 0:
            delta_str = f" (\u25bc{abs(diff):.1f})"
        else:
            delta_str = " (\u2192)"

    return f"{bar} {score:.1f}/10 {label}{delta_str}"
