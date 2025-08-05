import streamlit as st
from openai import OpenAI
import random

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

# 페이지 설정
st.set_page_config(
    page_title="🍽️ AI 음식 추천", 
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ AI 음식 추천")
st.markdown("당신의 취향과 상황에 맞는 완벽한 음식을 추천해드립니다!")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 음식 카테고리
    category = st.selectbox(
        "음식 카테고리",
        ["한식", "중식", "일식", "양식", "분식", "디저트", "음료", "전체"]
    )
    
    # 예산 범위
    budget = st.selectbox(
        "예산 범위",
        ["1만원 이하", "1-2만원", "2-3만원", "3-5만원", "5만원 이상", "상관없음"]
    )
    
    # 시간대
    time_of_day = st.selectbox(
        "시간대",
        ["아침", "점심", "저녁", "야식", "간식", "상관없음"]
    )
    
    # 인원수
    people_count = st.slider("인원수", 1, 10, 1)
    
    # 조리 시간
    cooking_time = st.selectbox(
        "조리 시간",
        ["5분 이하", "5-15분", "15-30분", "30분-1시간", "1시간 이상", "상관없음"]
    )

# 메인 컨텐츠
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🎯 선호도 설정")
    
    # 알레르기/기피 음식
    allergies = st.text_area(
        "알레르기/기피 음식 (선택사항):",
        placeholder="예: 새우, 견과류, 우유 등",
        height=100
    )
    
    # 선호하는 맛
    taste_preference = st.multiselect(
        "선호하는 맛",
        ["매운맛", "단맛", "신맛", "쓴맛", "짭짤한맛", "고소한맛", "새콤달콤", "상관없음"],
        default=["상관없음"]
    )
    
    # 특별한 요청
    special_request = st.text_area(
        "특별한 요청 (선택사항):",
        placeholder="예: 건강식, 다이어트용, 아이와 함께 먹을 수 있는 음식 등",
        height=100
    )

with col2:
    st.header("📝 상황 설명")
    
    # 현재 상황
    situation = st.text_area(
        "현재 상황을 설명해주세요:",
        placeholder="예: 오늘은 정말 피곤해서 간단하게 먹고 싶어요\n예: 친구들과 함께 즐길 수 있는 음식이 필요해요\n예: 건강에 좋은 음식을 찾고 있어요",
        height=200
    )
    
    # 기분
    mood = st.selectbox(
        "오늘의 기분",
        ["기쁨", "우울함", "스트레스", "평온함", "배고픔", "상관없음"]
    )

# 추천 버튼
if st.button("🍽️ 음식 추천받기", type="primary"):
    if situation.strip():
        with st.spinner("AI가 완벽한 음식을 찾고 있습니다..."):
            try:
                # 프롬프트 구성
                prompt = f"""
당신은 음식 추천 전문가입니다. 사용자의 상황과 선호도에 맞는 음식을 추천해주세요.

**기본 정보:**
- 카테고리: {category}
- 예산: {budget}
- 시간대: {time_of_day}
- 인원수: {people_count}명
- 조리시간: {cooking_time}

**선호도:**
- 알레르기/기피: {allergies if allergies.strip() else "없음"}
- 선호 맛: {', '.join(taste_preference)}
- 특별 요청: {special_request if special_request.strip() else "없음"}

**상황:**
- 현재 상황: {situation}
- 기분: {mood}

다음 형식으로 5개의 음식을 추천해주세요:

1. **[음식명]** - [간단한 설명]
   - 가격대: [예상 가격]
   - 조리시간: [예상 시간]
   - 추천 이유: [왜 이 음식을 추천하는지]

2. **[음식명]** - [간단한 설명]
   - 가격대: [예상 가격]
   - 조리시간: [예상 시간]
   - 추천 이유: [왜 이 음식을 추천하는지]

3. **[음식명]** - [간단한 설명]
   - 가격대: [예상 가격]
   - 조리시간: [예상 시간]
   - 추천 이유: [왜 이 음식을 추천하는지]

4. **[음식명]** - [간단한 설명]
   - 가격대: [예상 가격]
   - 조리시간: [예상 시간]
   - 추천 이유: [왜 이 음식을 추천하는지]

5. **[음식명]** - [간단한 설명]
   - 가격대: [예상 가격]
   - 조리시간: [예상 시간]
   - 추천 이유: [왜 이 음식을 추천하는지]

추가로 간단한 조리 팁이나 주의사항도 알려주세요.
"""

                response = client.chat.completions.create(
                    model="solar-pro2",
                    messages=[{"role": "user", "content": prompt}],
                    stream=False,
                )
                
                st.session_state.recommendations = response.choices[0].message.content
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")

# 결과 표시
if "recommendations" in st.session_state:
    st.markdown("---")
    st.header("🍽️ AI 추천 음식")
    st.markdown(st.session_state.recommendations)

# 하단에 예시들
st.markdown("---")
st.header("🎯 사용 예시")

examples = [
    {
        "상황": "오늘은 정말 피곤해서 간단하게 먹고 싶어요",
        "추천": "라면, 김밥, 샌드위치, 토스트, 컵라면",
        "설명": "간단하고 빠르게 먹을 수 있는 음식들"
    },
    {
        "상황": "친구들과 함께 즐길 수 있는 음식이 필요해요",
        "추천": "치킨, 피자, 샤브샤브, 삼겹살, 파스타",
        "설명": "함께 나누며 즐길 수 있는 음식들"
    },
    {
        "상황": "건강에 좋은 음식을 찾고 있어요",
        "추천": "샐러드, 닭가슴살, 현미밥, 채소국수, 두부요리",
        "설명": "영양가가 높고 건강한 음식들"
    }
]

for example in examples:
    with st.expander(f"📦 {example['상황']}"):
        st.markdown(f"**추천 음식:** {example['추천']}")
        st.markdown(f"**설명:** {example['설명']}")

# 랜덤 음식 추천 (빠른 추천)
st.markdown("---")
st.header("🎲 빠른 추천")

if st.button("🎲 랜덤 음식 추천"):
    korean_foods = [
        "김치찌개", "된장찌개", "비빔밥", "불고기", "삼겹살", "닭볶음탕", 
        "갈비찜", "순두부찌개", "김치볶음밥", "제육볶음", "된장국", "미역국",
        "떡볶이", "김밥", "라면", "순대", "어묵", "호떡", "붕어빵", "타코야키"
    ]
    
    chinese_foods = [
        "짜장면", "짬뽕", "탕수육", "깐풍기", "마파두부", "꿔바로우",
        "양장피", "고추잡채", "훠궈", "딤섬", "만두", "샤오롱바오"
    ]
    
    japanese_foods = [
        "초밥", "라멘", "우동", "덮밥", "오니기리", "타코야키",
        "오코노미야키", "가라아게", "돈카츠", "규동", "오야코동", "가츠동"
    ]
    
    western_foods = [
        "피자", "파스타", "스테이크", "샌드위치", "버거", "샐러드",
        "리조또", "오믈렛", "토스트", "팬케이크", "와플", "크로아상"
    ]
    
    all_foods = korean_foods + chinese_foods + japanese_foods + western_foods
    
    random_food = random.choice(all_foods)
    
    st.success(f"🎉 오늘의 추천 음식: **{random_food}**")
    
    # 음식 설명
    food_descriptions = {
        "김치찌개": "매콤하고 얼큰한 김치찌개로 식욕을 돋우세요!",
        "피자": "치즈가 듬뿍 올라간 피자로 행복한 시간을 보내세요!",
        "초밥": "신선한 생선으로 만든 초밥으로 건강한 한끼를!",
        "짜장면": "진한 짜장소스가 묻은 면발의 매력을 느껴보세요!"
    }
    
    if random_food in food_descriptions:
        st.info(food_descriptions[random_food])

# 푸터
st.markdown("---")
st.markdown("💡 **팁**: 더 정확한 추천을 위해 현재 상황을 자세히 설명해주세요!") 
