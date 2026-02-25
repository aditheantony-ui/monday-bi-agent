import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="Monday Business Intelligence Agent",
    layout="wide"
)

# Institutional Black & White Styling
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #ffffff;
    color: #111111;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.main-title {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 32px;
    font-weight: 600;
    border-bottom: 2px solid #000000;
    padding-bottom: 12px;
    margin-bottom: 10px;
}

.sub-text {
    font-size: 14px;
    color: #444444;
    margin-bottom: 30px;
}

.section-title {
    font-size: 18px;
    font-weight: 600;
    border-bottom: 1px solid #cccccc;
    padding-bottom: 6px;
    margin-top: 30px;
    margin-bottom: 15px;
}

.answer-box {
    background-color: #ffffff;
    padding: 22px;
    border: 1px solid #000000;
    border-radius: 2px;
    font-size: 15px;
    line-height: 1.6;
}

button {
    background-color: #000000 !important;
    color: #ffffff !important;
    border-radius: 0px !important;
}

input {
    border-radius: 0px !important;
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-title">Monday Business Intelligence Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">Executive-level financial and operational reporting across work orders and deal pipeline</div>', unsafe_allow_html=True)

# Input section
st.markdown('<div class="section-title">Executive Query</div>', unsafe_allow_html=True)

question = st.text_input("Enter your business question")

if st.button("Generate Insight"):
    if question.strip() == "":
        st.warning("Please enter a question.")
    else:
        with st.spinner("Processing data..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/ask",
                    json={"question": question}
                )

                if response.status_code == 200:
                    answer = response.json().get("answer", "No response received.")
                    
                    st.markdown('<div class="section-title">Executive Summary</div>', unsafe_allow_html=True)
                    st.markdown('<div class="answer-box">' + answer + '</div>', unsafe_allow_html=True)

                else:
                    st.error("Backend service error.")

            except Exception:
                st.error("Unable to connect to backend service.")