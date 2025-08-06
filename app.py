import streamlit as st
from openai import OpenAI

# API 키 설정
try:
    api_key = st.secrets["UPSTAGE_API_KEY"]
except KeyError:
    st.error("API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에서 UPSTAGE_API_KEY를 설정해주세요.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.upstage.ai/v1"
)

st.set_page_config(
    page_title="🎲 AI 음식 추천",
    page_icon="🍽️",
    layout="centered"
)

st.title("🎲 AI 음식 추천")
st.markdown("카테고리만 선택하면 AI가 랜덤으로 오늘의 음식을 추천해줍니다!")

# 카테고리 선택
category = st.selectbox(
    "음식 카테고리",
    ["전체", "한식", "중식", "일식", "양식", "분식", "디저트", "음료"]
)

if st.button("🎲 오늘의 음식 추천받기", type="primary"):
    with st.spinner("AI가 오늘의 음식을 추천하고 있습니다..."):
        try:
            prompt = f"""
당신은 음식 추천 전문가입니다. 사용자가 '{category}' 카테고리를 선택했습니다. 오늘 먹으면 좋을만한 음식을 1개 추천하고, 음식에 대한 간단한 설명도 함께 알려주세요. 다음 형식으로 답변하세요:
**음식명** (단, 아무 설명도 없이 음식명만 적어야함 이 설명은 적지 않음)
"""
            response = client.chat.completions.create(
                model="solar-pro2",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            st.success(response.choices[0].message.content.strip())
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")

st.markdown("---")
st.markdown("💡 **팁**: 카테고리를 바꿔가며 다양한 음식 추천을 받아보세요!") 
