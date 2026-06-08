import streamlit as st

GLOBAL_CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
.block-container {padding-top: 1rem !important; max-width: 900px !important;}

div[data-testid="stMetric"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
}
div[data-testid="stMetric"] label {
    font-size: 0.65rem !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600 !important;
    color: #94a3b8 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1rem !important;
    font-weight: 700 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.7rem !important;
}

.stMarkdown code {
    background: #312e81 !important;
    color: #a5b4fc !important;
    border: 1px solid #4338ca !important;
    border-radius: 12px !important;
    padding: 2px 10px !important;
    font-size: 0.8rem !important;
}

hr {border-color: #334155 !important; margin: 1rem 0 !important;}

section[data-testid="stSidebar"] {background: #0f172a;}

@media (max-width: 768px) {
    .block-container {padding-left: 1rem !important; padding-right: 1rem !important;}
}
</style>
"""

def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
