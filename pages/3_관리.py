import streamlit as st
import json
import base64
import requests
from datetime import datetime, timezone
from style import inject_css
from utils import render_sidebar, render_nav

st.set_page_config(page_title="Admin", page_icon="\U0001F4C8", layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={"Get help": None, "Report a Bug": None, "About": None})
inject_css()
render_sidebar()
render_nav()

st.title("Request Briefing")
st.caption("Generate a fresh market analysis on demand.")

with st.form("briefing_request", clear_on_submit=True):
    col_pw, col_hrs = st.columns([2, 1])
    with col_pw:
        password = st.text_input("Access Key", type="password", placeholder="Enter access key")
    with col_hrs:
        hours = st.selectbox("Lookback", [4, 6, 8, 12], index=2,
                             format_func=lambda h: f"Last {h}h")
    submitted = st.form_submit_button("Generate Briefing", type="primary", use_container_width=True)

if submitted:
    correct_pw = st.secrets.get("REQUEST_PASSWORD", "")
    if not correct_pw:
        st.error("Server not configured. Set REQUEST_PASSWORD in Streamlit Secrets.")
    elif password != correct_pw:
        st.error("Invalid access key.")
    else:
        with st.spinner("Submitting request..."):
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
                content_b64 = base64.b64encode(content_str.encode()).decode()
                headers = {"Authorization": f"token {pat}",
                           "Accept": "application/vnd.github.v3+json"}

                check = requests.get(
                    f"https://api.github.com/repos/{repo}/contents/{path}",
                    headers=headers, timeout=10)
                sha = check.json().get("sha") if check.status_code == 200 else None

                payload = {"message": "request: new briefing", "content": content_b64}
                if sha:
                    payload["sha"] = sha

                resp = requests.put(
                    f"https://api.github.com/repos/{repo}/contents/{path}",
                    headers=headers, json=payload, timeout=15)

                if resp.status_code in (200, 201):
                    st.success(f"Request submitted (last {hours}h). New briefing in ~2 minutes.")
                else:
                    st.error(f"GitHub API error: {resp.status_code}")
            except requests.exceptions.Timeout:
                st.error("Request timed out. Try again.")
            except Exception as e:
                st.error(f"Error: {e}")
