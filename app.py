import streamlit as st
from openai import OpenAI

api_key = st.secrets["UPSTAGE_API_KEY"]

client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1"
)

st.set_page_config(page_title="RPG AI", page_icon="🧙‍♂️")
st.title("RPG AI")
st.write("RPG 세계에 오신 것을 환영합니다! 원하는 행동을 입력해보세요.")

# RPG 시스템 프롬프트
SYSTEM_PROMPT = (
    "당신은 판타지 세계의 게임 마스터입니다. "
    "사용자가 입력하는 모든 행동에 대해 상황을 묘사하고, "
    "NPC(등장인물)처럼 대화하세요. 게임을 재미있게 진행하세요."
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# 이전 대화 출력
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

# 사용자 입력 받기
if prompt := st.chat_input("행동을 입력하세요:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # AI 응답
    with st.chat_message("assistant"):
        response = ""
        stream = client.chat.completions.create(
            model="solar-pro2",
            messages=st.session_state.messages,
            stream=True,
        )
        msg_placeholder = st.empty()
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content
                msg_placeholder.markdown(response + "▌")
