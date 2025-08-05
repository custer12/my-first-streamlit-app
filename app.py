import streamlit as st
from openai import OpenAI
import re

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
    page_title="AI 변수명 생성기", 
    page_icon="🔤",
    layout="wide"
)

st.title("🤖 AI 변수명 생성기")
st.markdown("코드의 의미를 설명하면 AI가 적절한 변수명을 제안해드립니다!")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 프로그래밍 언어 선택
    language = st.selectbox(
        "프로그래밍 언어",
        ["Python", "JavaScript", "Java", "C++", "C#", "TypeScript", "Go", "Rust", "PHP", "Ruby"]
    )
    
    # 네이밍 컨벤션 선택
    convention = st.selectbox(
        "네이밍 컨벤션",
        ["snake_case (Python 스타일)", "camelCase (JavaScript 스타일)", "PascalCase (클래스명)", "UPPER_SNAKE_CASE (상수)"]
    )
    
    # 변수 타입 선택
    var_type = st.selectbox(
        "변수 타입",
        ["일반 변수", "함수명", "클래스명", "상수", "배열/리스트", "객체/딕셔너리", "불린값"]
    )

# 메인 컨텐츠
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 변수 설명")
    
    # 사용자 입력
    description = st.text_area(
        "변수의 용도나 의미를 설명해주세요:",
        placeholder="예: 사용자의 나이를 저장하는 변수\n예: 로그인 성공 여부를 확인하는 변수\n예: 상품 목록을 담는 배열",
        height=200
    )
    
    # 추가 컨텍스트
    context = st.text_area(
        "추가 컨텍스트 (선택사항):",
        placeholder="예: 웹 애플리케이션의 사용자 관리 시스템\n예: 게임의 플레이어 상태 관리",
        height=100
    )
    
    # 생성 버튼
    if st.button("🚀 변수명 생성하기", type="primary"):
        if description.strip():
            with st.spinner("AI가 변수명을 생성하고 있습니다..."):
                try:
                    # 프롬프트 구성
                    prompt = f"""
당신은 프로그래밍 전문가입니다. 주어진 설명에 따라 적절한 변수명을 제안해주세요.

프로그래밍 언어: {language}
네이밍 컨벤션: {convention}
변수 타입: {var_type}

변수 설명: {description}
추가 컨텍스트: {context if context.strip() else "없음"}

다음 형식으로 5개의 변수명을 제안해주세요:

1. [변수명] - [설명]
2. [변수명] - [설명]
3. [변수명] - [설명]
4. [변수명] - [설명]
5. [변수명] - [설명]

추가로 다른 프로그래밍 언어에서의 동등한 변수명도 제안해주세요.
"""

                    response = client.chat.completions.create(
                        model="solar-pro2",
                        messages=[{"role": "user", "content": prompt}],
                        stream=False,
                    )
                    
                    st.session_state.suggestions = response.choices[0].message.content
                    
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")

with col2:
    st.header("💡 AI 제안")
    
    if "suggestions" in st.session_state:
        st.markdown("### 추천 변수명")
        st.markdown(st.session_state.suggestions)
        
        # 변수명 추출 및 복사 기능
        st.markdown("### 📋 복사하기")
        
        # 정규식으로 변수명 추출
        lines = st.session_state.suggestions.split('\n')
        variable_names = []
        
        for line in lines:
            if re.match(r'^\d+\.\s*\[([^\]]+)\]\s*-\s*', line):
                var_name = re.search(r'^\d+\.\s*\[([^\]]+)\]\s*-\s*', line).group(1)
                variable_names.append(var_name)
        
        if variable_names:
            for i, var_name in enumerate(variable_names, 1):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.code(var_name, language="python")
                with col_b:
                    if st.button(f"복사 {i}", key=f"copy_{i}"):
                        st.write("✅ 복사됨!")

# 하단에 예시들
st.markdown("---")
st.header("🎯 사용 예시")

examples = [
    {
        "설명": "사용자의 나이를 저장하는 변수",
        "Python": "user_age, age, person_age, current_age, user_age_value",
        "JavaScript": "userAge, age, personAge, currentAge, userAgeValue"
    },
    {
        "설명": "로그인 성공 여부를 확인하는 변수",
        "Python": "is_logged_in, login_success, user_authenticated, auth_status, login_status",
        "JavaScript": "isLoggedIn, loginSuccess, userAuthenticated, authStatus, loginStatus"
    },
    {
        "설명": "상품 목록을 담는 배열",
        "Python": "products, product_list, items, inventory, product_catalog",
        "JavaScript": "products, productList, items, inventory, productCatalog"
    }
]

for example in examples:
    with st.expander(f"📦 {example['설명']}"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Python 스타일:**")
            st.code(example['Python'])
        with col2:
            st.markdown("**JavaScript 스타일:**")
            st.code(example['JavaScript'])

# 푸터
st.markdown("---")
st.markdown("💡 **팁**: 변수의 용도를 명확하게 설명할수록 더 정확한 변수명을 제안받을 수 있습니다!") 
