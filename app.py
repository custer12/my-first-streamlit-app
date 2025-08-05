import streamlit as st
from openai import OpenAI

# API 키를 secrets에서 가져오기
api_key = st.secrets["UPSTAGE_API_KEY"]

client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1"
)

st.set_page_config(page_title="주식 AI", page_icon="😊")
st.title("주식")
st.write("!주식, !주식 구매")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "!주식, !주식 구매, !주식 판매, !주식 보유, !돈 같은거 내돈은 처음5000로 기본 주식들은 이제 1000 가격으로 시작"}
    ]

# 이전 대화 내용 출력
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

# 사용자 입력 받기
if prompt := st.chat_input("입력 : "):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 스트리밍 응답 받기
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
        msg_placeholder.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
