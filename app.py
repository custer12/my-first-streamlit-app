import streamlit as st
from openai import OpenAI

# API 키를 secrets에서 가져오기
api_key = st.secrets["UPSTAGE_API_KEY"]

client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1"
)

st.set_page_config(page_title="심리상담 챗봇", page_icon="🧑‍🎓")
st.title("🧑‍🎓 학생 심리상담 챗봇")
st.write("아래 챗봇에 고민이나 궁금한 점을 자유롭게 입력해보세요. 여러분의 마음을 이해하고 도와드릴 수 있도록 노력할게요.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "너는 학생들의 심리상담을 도와주는 친절한 상담사야. 학생의 고민을 공감하고, 따뜻하게 조언해줘."}
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
