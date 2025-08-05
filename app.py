import streamlit as st
from openai import OpenAI

# API 키를 secrets에서 가져오기
api_key = st.secrets["UPSTAGE_API_KEY"]

client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1"
)

st.set_page_config(page_title="RPG AI", page_icon="😊")
st.title("RPG AI")
st.write("아래 상점, 인벤토리, 공격 명령어 적기")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "상점, 인벤토리, 전투 명령어가 있고 명령어를 말하면 이제 그에 대한 답변이 나와야해 전투를 하면 이기면 보상 지면 아이템을 잃는 느낌"}
    ]

# 이전 대화 내용 출력
for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

# 사용자 입력 받기
if prompt := st.chat_input("고민이나 궁금한 점을 입력하세요..."):
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
