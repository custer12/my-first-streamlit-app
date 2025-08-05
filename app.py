import streamlit as st
from openai import OpenAI
import json

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
    page_title="👨‍🍳 초보 요리사 도우미", 
    page_icon="👨‍🍳",
    layout="wide"
)

st.title("👨‍🍳 초보 요리사 도우미")
st.markdown("레시피를 입력하면 계량 단위와 생소한 재료를 친절하게 설명해드립니다!")

# 탭 생성
tab1, tab2, tab3 = st.tabs(["📖 레시피 해석", "🥄 계량 도우미", "🥬 재료 백과사전"])

with tab1:
    st.header("📖 레시피 해석")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("레시피 입력")
        
        # 레시피 입력
        recipe_text = st.text_area(
            "레시피를 입력해주세요:",
            placeholder="예: 김치찌개\n재료:\n- 돼지고기 200g\n- 김치 1컵\n- 작은숟갈 1t 고춧가루\n- 큰숟갈 1T 된장\n\n조리법:\n1. 돼지고기를 볶는다\n2. 김치를 넣고 볶는다\n3. 물을 넣고 끓인다",
            height=300
        )
        
        # 요리 경험 수준
        experience_level = st.selectbox(
            "요리 경험 수준",
            ["완전 초보 (요리 경험 없음)", "초보 (간단한 요리만 해봄)", "중급 (자주 요리함)", "상관없음"]
        )
        
        # 특별한 요청
        special_requests = st.multiselect(
            "추가로 알고 싶은 것",
            ["계량 단위 상세 설명", "재료 대체법", "조리 팁", "영양 정보", "보관법", "모든 것"]
        )
        
        if st.button("🔍 레시피 해석하기", type="primary"):
            if recipe_text.strip():
                with st.spinner("레시피를 분석하고 있습니다..."):
                    try:
                        # 프롬프트 구성
                        prompt = f"""
당신은 초보 요리사를 위한 친절한 요리 선생님입니다. 레시피를 분석해서 초보자가 이해하기 쉽게 설명해주세요.

**요리 경험 수준:** {experience_level}
**추가 요청:** {', '.join(special_requests) if special_requests else '없음'}

**레시피:**
{recipe_text}

다음 형식으로 JSON으로 응답해주세요:

{{
    "recipe_name": "요리 이름",
    "difficulty": "난이도 (초급/중급/고급)",
    "cooking_time": "예상 조리시간",
    "servings": "인분",
    
    "ingredients_analysis": [
        {{
            "original": "원본 재료명",
            "amount": "양",
            "unit": "단위",
            "detailed_amount": "상세한 양 설명 (예: 작은숟갈 1t = 5ml)",
            "substitute": "대체재료 (있는 경우)",
            "description": "재료 설명",
            "where_to_buy": "구매처",
            "storage": "보관법"
        }}
    ],
    
    "cooking_steps": [
        {{
            "step": "조리 단계",
            "detailed_instruction": "상세한 설명",
            "tips": "조리 팁",
            "common_mistakes": "자주 하는 실수",
            "time_estimate": "예상 시간"
        }}
    ],
    
    "measurement_guide": {{
        "tablespoon": "큰숟갈 설명",
        "teaspoon": "작은숟갈 설명",
        "cup": "컵 설명",
        "gram": "그램 설명",
        "other_units": "기타 단위들"
    }},
    
    "nutrition_info": {{
        "calories": "칼로리",
        "protein": "단백질",
        "carbs": "탄수화물",
        "fat": "지방",
        "fiber": "식이섬유"
    }},
    
    "tips_for_beginners": [
        "초보자를 위한 팁들"
    ],
    
    "common_questions": [
        {{
            "question": "자주 묻는 질문",
            "answer": "답변"
        }}
    ],
    
    "shopping_list": [
        "구매해야 할 재료들"
    ]
}}

초보자가 이해하기 쉽게 친절하고 상세하게 설명해주세요.
"""

                        response = client.chat.completions.create(
                            model="solar-pro2",
                            messages=[{"role": "user", "content": prompt}],
                            stream=False,
                        )
                        
                        try:
                            result = json.loads(response.choices[0].message.content)
                            st.session_state.recipe_analysis = result
                        except json.JSONDecodeError:
                            st.session_state.raw_recipe_response = response.choices[0].message.content
                            
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
    
    with col2:
        st.subheader("📋 빠른 레시피 예시")
        
        example_recipes = {
            "김치찌개": """
재료:
- 돼지고기 200g
- 김치 1컵
- 작은숟갈 1t 고춧가루
- 큰숟갈 1T 된장
- 양파 1/2개
- 대파 1대

조리법:
1. 돼지고기를 볶는다
2. 김치를 넣고 볶는다
3. 물을 넣고 끓인다
4. 양파, 대파를 넣는다
""",
            "계란볶음밥": """
재료:
- 밥 1공기
- 계란 2개
- 작은숟갈 1t 간장
- 작은숟갈 1/2t 소금
- 대파 1대

조리법:
1. 계란을 풀어둔다
2. 팬에 기름을 두르고 계란을 부친다
3. 밥을 넣고 볶는다
4. 간장, 소금으로 간한다
""",
            "된장찌개": """
재료:
- 큰숟갈 2T 된장
- 두부 1/2모
- 애호박 1/2개
- 양파 1/2개
- 대파 1대
- 마늘 2쪽

조리법:
1. 물을 끓인다
2. 된장을 풀어 넣는다
3. 채소들을 넣는다
4. 두부를 넣고 끓인다
"""
        }
        
        selected_example = st.selectbox("예시 레시피 선택:", list(example_recipes.keys()))
        st.text_area("선택된 레시피:", example_recipes[selected_example], height=200)
        
        if st.button("예시로 해석하기"):
            recipe_text = example_recipes[selected_example]
            st.session_state.example_recipe = recipe_text

# 결과 표시
if "recipe_analysis" in st.session_state:
    st.markdown("---")
    st.header("🍽️ 레시피 분석 결과")
    
    result = st.session_state.recipe_analysis
    
    # 기본 정보
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("요리명", result.get("recipe_name", "알 수 없음"))
    with col2:
        st.metric("난이도", result.get("difficulty", "알 수 없음"))
    with col3:
        st.metric("조리시간", result.get("cooking_time", "알 수 없음"))
    with col4:
        st.metric("인분", result.get("servings", "알 수 없음"))
    
    # 재료 분석
    if "ingredients_analysis" in result:
        st.subheader("🥬 재료 상세 분석")
        
        for i, ingredient in enumerate(result["ingredients_analysis"], 1):
            with st.expander(f"{i}. {ingredient['original']} {ingredient['amount']}{ingredient['unit']}"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"**상세한 양:** {ingredient['detailed_amount']}")
                    st.markdown(f"**설명:** {ingredient['description']}")
                    if ingredient.get('substitute'):
                        st.markdown(f"**대체재료:** {ingredient['substitute']}")
                
                with col2:
                    st.markdown(f"**구매처:** {ingredient['where_to_buy']}")
                    st.markdown(f"**보관법:** {ingredient['storage']}")
    
    # 조리 단계
    if "cooking_steps" in result:
        st.subheader("👨‍🍳 조리 단계")
        
        for i, step in enumerate(result["cooking_steps"], 1):
            with st.expander(f"단계 {i}: {step['step']}"):
                st.markdown(f"**상세 설명:** {step['detailed_instruction']}")
                st.markdown(f"**조리 팁:** {step['tips']}")
                st.markdown(f"**자주 하는 실수:** {step['common_mistakes']}")
                st.markdown(f"**예상 시간:** {step['time_estimate']}")
    
    # 계량 가이드
    if "measurement_guide" in result:
        st.subheader("🥄 계량 가이드")
        
        guide = result["measurement_guide"]
        guide_cols = st.columns(2)
        
        with guide_cols[0]:
            st.markdown(f"**큰숟갈 (T):** {guide['tablespoon']}")
            st.markdown(f"**작은숟갈 (t):** {guide['teaspoon']}")
        
        with guide_cols[1]:
            st.markdown(f"**컵:** {guide['cup']}")
            st.markdown(f"**그램 (g):** {guide['gram']}")
        
        if guide.get('other_units'):
            st.markdown(f"**기타 단위:** {guide['other_units']}")
    
    # 영양 정보
    if "nutrition_info" in result:
        st.subheader("🥗 영양 정보")
        
        nutrition = result["nutrition_info"]
        nut_cols = st.columns(5)
        
        with nut_cols[0]:
            st.metric("칼로리", nutrition['calories'])
        with nut_cols[1]:
            st.metric("단백질", nutrition['protein'])
        with nut_cols[2]:
            st.metric("탄수화물", nutrition['carbs'])
        with nut_cols[3]:
            st.metric("지방", nutrition['fat'])
        with nut_cols[4]:
            st.metric("식이섬유", nutrition['fiber'])
    
    # 초보자 팁
    if "tips_for_beginners" in result:
        st.subheader("💡 초보자를 위한 팁")
        for tip in result["tips_for_beginners"]:
            st.write(f"• {tip}")
    
    # 자주 묻는 질문
    if "common_questions" in result:
        st.subheader("❓ 자주 묻는 질문")
        for qa in result["common_questions"]:
            with st.expander(qa['question']):
                st.write(qa['answer'])
    
    # 쇼핑 리스트
    if "shopping_list" in result:
        st.subheader("🛒 쇼핑 리스트")
        for item in result["shopping_list"]:
            st.write(f"• {item}")

elif "raw_recipe_response" in st.session_state:
    st.markdown("---")
    st.header("🍽️ 레시피 분석")
    st.markdown(st.session_state.raw_recipe_response)

with tab2:
    st.header("🥄 계량 도우미")
    
    # 계량 단위 변환
    st.subheader("📏 계량 단위 변환")
    
    col1, col2 = st.columns(2)
    
    with col1:
        from_unit = st.selectbox(
            "변환할 단위",
            ["작은숟갈 (t)", "큰숟갈 (T)", "컵", "그램 (g)", "밀리리터 (ml)", "온스 (oz)"]
        )
        
        amount = st.number_input("양", min_value=0.0, value=1.0, step=0.1)
    
    with col2:
        to_unit = st.selectbox(
            "변환할 단위",
            ["밀리리터 (ml)", "그램 (g)", "작은숟갈 (t)", "큰숟갈 (T)", "컵", "온스 (oz)"]
        )
    
    if st.button("🔄 변환하기"):
        with st.spinner("변환 중..."):
            try:
                conversion_prompt = f"""
{amount} {from_unit}를 {to_unit}로 변환해주세요.

다음 형식으로 JSON으로 응답해주세요:

{{
    "from": {{
        "amount": {amount},
        "unit": "{from_unit}"
    }},
    "to": {{
        "amount": "변환된 양",
        "unit": "{to_unit}"
    }},
    "conversion_factors": {{
        "tablespoon_to_ml": "큰숟갈 1개 = ?ml",
        "teaspoon_to_ml": "작은숟갈 1개 = ?ml",
        "cup_to_ml": "컵 1개 = ?ml",
        "common_conversions": "기타 일반적인 변환"
    }},
    "tips": "계량 시 주의사항"
}}
"""

                response = client.chat.completions.create(
                    model="solar-pro2",
                    messages=[{"role": "user", "content": conversion_prompt}],
                    stream=False,
                )
                
                try:
                    conversion_result = json.loads(response.choices[0].message.content)
                    st.session_state.conversion_result = conversion_result
                except json.JSONDecodeError:
                    st.session_state.raw_conversion_response = response.choices[0].message.content
                    
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
    
    # 변환 결과 표시
    if "conversion_result" in st.session_state:
        result = st.session_state.conversion_result
        
        st.success(f"**{result['from']['amount']} {result['from']['unit']} = {result['to']['amount']} {result['to']['unit']}**")
        
        st.subheader("📋 일반적인 변환")
        factors = result['conversion_factors']
        for key, value in factors.items():
            st.write(f"• {value}")
        
        st.info(f"💡 **팁:** {result['tips']}")
    
    # 계량 팁
    st.subheader("💡 계량 팁")
    
    measurement_tips = {
        "작은숟갈 (t)": "5ml, 약 1/3 큰숟갈",
        "큰숟갈 (T)": "15ml, 약 3 작은숟갈",
        "컵": "200ml (일반적인 계량컵 기준)",
        "그램 (g)": "무게 단위, 저울로 측정",
        "밀리리터 (ml)": "부피 단위, 계량컵으로 측정",
        "온스 (oz)": "약 30ml, 2 큰숟갈"
    }
    
    for unit, tip in measurement_tips.items():
        with st.expander(unit):
            st.write(tip)

with tab3:
    st.header("🥬 재료 백과사전")
    
    # 재료 검색
    st.subheader("🔍 재료 검색")
    
    ingredient_query = st.text_input(
        "알고 싶은 재료를 입력하세요:",
        placeholder="예: 고춧가루, 된장, 두부, 애호박"
    )
    
    if st.button("🔍 재료 정보 찾기"):
        if ingredient_query.strip():
            with st.spinner("재료 정보를 찾고 있습니다..."):
                try:
                    ingredient_prompt = f"""
'{ingredient_query}'에 대한 상세한 정보를 알려주세요.

다음 형식으로 JSON으로 응답해주세요:

{{
    "name": "{ingredient_query}",
    "category": "카테고리",
    "description": "재료 설명",
    "taste": "맛과 특징",
    "nutrition": {{
        "calories": "칼로리",
        "protein": "단백질",
        "carbs": "탄수화물",
        "fat": "지방",
        "vitamins": "비타민",
        "minerals": "미네랄"
    }},
    "how_to_select": [
        "선택하는 방법"
    ],
    "how_to_store": [
        "보관하는 방법"
    ],
    "substitutes": [
        {{
            "name": "대체재료명",
            "ratio": "대체 비율",
            "notes": "주의사항"
        }}
    ],
    "common_uses": [
        "일반적인 용도"
    ],
    "cooking_tips": [
        "조리 팁"
    ],
    "where_to_buy": [
        "구매처"
    ],
    "price_range": "가격대",
    "season": "제철"
}}
"""

                    response = client.chat.completions.create(
                        model="solar-pro2",
                        messages=[{"role": "user", "content": ingredient_prompt}],
                        stream=False,
                    )
                    
                    try:
                        ingredient_result = json.loads(response.choices[0].message.content)
                        st.session_state.ingredient_result = ingredient_result
                    except json.JSONDecodeError:
                        st.session_state.raw_ingredient_response = response.choices[0].message.content
                        
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")
    
    # 재료 정보 표시
    if "ingredient_result" in st.session_state:
        result = st.session_state.ingredient_result
        
        st.subheader(f"🥬 {result['name']} 정보")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"**카테고리:** {result['category']}")
            st.markdown(f"**설명:** {result['description']}")
            st.markdown(f"**맛과 특징:** {result['taste']}")
            st.markdown(f"**가격대:** {result['price_range']}")
            st.markdown(f"**제철:** {result['season']}")
        
        with col2:
            st.markdown("**영양 정보:**")
            nutrition = result['nutrition']
            st.write(f"• 칼로리: {nutrition['calories']}")
            st.write(f"• 단백질: {nutrition['protein']}")
            st.write(f"• 탄수화물: {nutrition['carbs']}")
            st.write(f"• 지방: {nutrition['fat']}")
            st.write(f"• 비타민: {nutrition['vitamins']}")
            st.write(f"• 미네랄: {nutrition['minerals']}")
        
        # 선택법
        st.subheader("🛒 선택하는 방법")
        for tip in result['how_to_select']:
            st.write(f"• {tip}")
        
        # 보관법
        st.subheader("📦 보관하는 방법")
        for tip in result['how_to_store']:
            st.write(f"• {tip}")
        
        # 대체재료
        if result['substitutes']:
            st.subheader("🔄 대체재료")
            for sub in result['substitutes']:
                with st.expander(f"🔄 {sub['name']}"):
                    st.write(f"**대체 비율:** {sub['ratio']}")
                    st.write(f"**주의사항:** {sub['notes']}")
        
        # 일반적인 용도
        st.subheader("🍽️ 일반적인 용도")
        for use in result['common_uses']:
            st.write(f"• {use}")
        
        # 조리 팁
        st.subheader("👨‍🍳 조리 팁")
        for tip in result['cooking_tips']:
            st.write(f"• {tip}")
        
        # 구매처
        st.subheader("🏪 구매처")
        for place in result['where_to_buy']:
            st.write(f"• {place}")

# 푸터
st.markdown("---")
st.markdown("💡 **팁**: 레시피를 입력할 때 정확한 양과 단위를 포함하면 더 정확한 분석을 받을 수 있습니다!")
