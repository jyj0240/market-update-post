import streamlit as st
import json
import requests
from datetime import datetime, timezone
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
else:
    # 업데이트 시각
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

# --- 리퀘스트 섹션 ---
st.divider()
with st.expander("Generate New Briefing"):
    password = st.text_input("Password", type="password", key="req_pw")
    hours = st.selectbox("Hours to analyze", [4, 6, 8, 12], index=2)

    if st.button("Request Briefing"):
        correct_pw = st.secrets.get("REQUEST_PASSWORD", "")
        if not correct_pw:
            st.error("Server not configured.")
        elif password != correct_pw:
            st.error("Incorrect password.")
        else:
            try:
                pat = st.secrets.get("GITHUB_PAT", "")
                repo = "jyj0240/market-update-post"
                path = "data/request.json"
                now = datetime.now(timezone.utc).isoformat()
                content_str = json.dumps({
                    "requested_at": now,
                    "hours_back": hours,
                    "status": "pending",
                })

                # Base64 encode
                import base64
                content_b64 = base64.b64encode(content_str.encode()).decode()

                # Check if file exists (to get sha for update)
                headers = {"Authorization": f"token {pat}", "Accept": "application/vnd.github.v3+json"}
                check = requests.get(f"https://api.github.com/repos/{repo}/contents/{path}", headers=headers)
                sha = check.json().get("sha") if check.status_code == 200 else None

                payload = {
                    "message": "request: new briefing",
                    "content": content_b64,
                }
                if sha:
                    payload["sha"] = sha

                resp = requests.put(
                    f"https://api.github.com/repos/{repo}/contents/{path}",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    st.success(f"Briefing requested! (last {hours}h) Processing will take ~2 minutes.")
                else:
                    st.error(f"Failed: {resp.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
