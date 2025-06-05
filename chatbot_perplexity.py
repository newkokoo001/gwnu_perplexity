import os
import streamlit as st
import requests
import json
import re
from dotenv import load_dotenv

# .env 파일에서 환경 변수 불러오기
load_dotenv()
api_key = os.getenv("PPLX_API_KEY")

# API 키 체크
if not api_key:
    st.error("API 키가 설정되어 있지 않습니다. .env 파일에 PPLX_API_KEY를 등록하세요.")
    st.stop()

st.set_page_config(
    page_title="국립강릉원주대학교 챗봇",
    page_icon="🏫",
    layout="centered",
    initial_sidebar_state="collapsed"
)
st.title("🏫 국립강릉원주대학교 챗봇")
st.markdown("*학교 관련 질문에 답변해 드립니다. 무엇이든 물어보세요!*")

# 세션 메시지는 비워두고
if "messages" not in st.session_state:
    st.session_state.messages = []

# 화면에만 안내 메시지 표시
st.markdown("📘 안녕하세요! 🏫 국립강릉원주대학교에 관한 질문이 있으신가요?")

def fix_message_roles(messages):
    fixed = []
    prev_role = None
    for msg in messages:
        if msg["role"] == "system":
            fixed.append(msg)
        elif prev_role != msg["role"]:
            fixed.append(msg)
            prev_role = msg["role"]
        else:
            continue
    return fixed

def query_perplexity(history):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = [{"role": "system", "content": "국립강릉원주대학교 정보를 정확하고 간결하게 제공하는 도우미입니다."}]
    messages += history
    messages = fix_message_roles(messages)
    data = {
        "model": "sonar-pro",
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.2,
        "frequency_penalty": 0.5
    }
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "응답을 처리하는 중 오류가 발생했습니다."
    except requests.exceptions.RequestException as e:
        try:
            err = response.json()
            return f"API 요청 중 오류 발생: {str(e)}\n상세: {err}"
        except Exception:
            return f"API 요청 중 오류 발생: {str(e)}"
    except Exception as e:
        return f"오류 발생: {str(e)}"

def render_answer_with_links(answer):
    # 링크와 참고마크(예: [1])가 붙어 있으면 분리
    # 예: <https://www.gwnu.ac.kr/kr/7852/subview.do>[1]  →  [증명서 발급 바로가기](https://www.gwnu.ac.kr/kr/7852/subview.do) [1]
    url_ref_pattern = r"(https?://[^\s\[\]\)]+)(\[\d+\])"
    answer = re.sub(
        url_ref_pattern,
        lambda m: f"[{m.group(1)}]({m.group(1)}) {m.group(2)}",
        answer
    )
    # 일반적인 링크도 마크다운으로 자동 변환
    url_pattern = r"(?<!\]\()(?P<url>https?://[^\s\[\]\)]+)"
    answer = re.sub(
        url_pattern,
        lambda m: f"[{m.group('url')}]({m.group('url')})",
        answer
    )
    st.markdown(answer, unsafe_allow_html=False)

# 이전 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # assistant 답변만 링크/참고마크 분리 렌더링
        if message["role"] == "assistant":
            render_answer_with_links(message["content"])
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 생각 중...")
        answer = query_perplexity(st.session_state.messages)
        message_placeholder.markdown("답변 생성 완료.")
        st.session_state.messages.append({"role": "assistant", "content": answer})
        render_answer_with_links(answer)

with st.sidebar:
    st.header("챗봇 설정")
    model = st.selectbox(
        "모델 선택",
        ["sonar-pro", "sonar", "sonar-reasoning", "mistral-7b-instruct", "pplx-70b-chat", "codellama-34b-instruct"]
    )
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.session_state.messages.append({"role": "user", "content": "안녕하세요! 국립강릉원주대학교에 관한 질문이 있으신가요?"})
        st.rerun()
    debug_mode = st.checkbox("디버그 모드")
    if debug_mode and "debug_info" in st.session_state:
        st.text_area("API 요청 데이터", st.session_state.debug_info, height=300)
    st.markdown("---")
    st.markdown("### 사용 정보")
    st.markdown("퍼플렉시티 API는 하루 500개의 쿼리 제한이 있습니다.")
    st.markdown("### 개발자 정보")
    st.markdown("이 챗봇은 퍼플렉시티 API를 활용하여 개발되었습니다.")
