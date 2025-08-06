import streamlit as st
from openai import OpenAI
import json
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup

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
    page_title="🍽️ 고급 AI 음식 추천", 
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ 고급 AI 음식 추천")
st.markdown("더 정교한 AI 추천과 레시피 정보를 제공합니다!")


def get_fallback_recipes(search_url, top_n = 5):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        res = requests.get(search_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        recipe_cards = soup.select(".common_sp_list_ul .common_sp_list_li")[:top_n]
        recipes = []
        for card in recipe_cards:
            title = card.select_one(".common_sp_caption_tit").get_text(strip=True)
            link = "https://www.10000recipe.com" + card.select_one("a")["href"]
            img = card.select_one(".common_sp_thumb img")
            img_url = img["src"] if img and img.has_attr("src") else None
            summary = card.select_one(".common_sp_caption_desc")
            summary_text = summary.get_text(strip=True) if summary else ""
            recipes.append({
                "title": title,
                "link": link,
                "img_url": img_url,
                "summary": summary_text
            })
        return recipes
    except Exception as e:
        return []

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["🎯 음식 추천", "📖 레시피 검색", "🍳 요리 도우미", "🏆 인기 레시피"])

with tab1:
    st.set_page_config(page_title="음식 레시피 추천", layout="wide")
    st.title("🍽️ 10000레시피 인기 레시피 순위별 요약")

    st.write(
        """
        원하는 음식 이름을 입력하면, 10000레시피 사이트에서 해당 음식의 인기 레시피를 순위별로 정리해서 보여줍니다.
        사이트에 직접 들어가지 않아도 대표 레시피와 요약 정보를 한눈에 확인할 수 있습니다.
        """
    )

    with st.form("food_search_form"):
        food_name = st.text_input("음식 이름을 입력하세요", placeholder="예: 김치찌개, 파스타, 초밥 등")
        top_n = st.slider("몇 개의 인기 레시피를 볼까요?", min_value=3, max_value=10, value=5)
        submitted = st.form_submit_button("인기 레시피 검색")

    if submitted and food_name.strip():
        with st.spinner("10000레시피에서 인기 레시피를 찾는 중입니다..."):
            recipes = get_fallback_recipes(f"https://www.10000recipe.com/recipe/list.html?q={food_name}", top_n=5)
            if recipes:
                st.success(f"'{food_name}'에 대한 인기 레시피 {len(recipes)}개를 찾았습니다!")
                for idx, recipe in enumerate(recipes, 1):
                    st.markdown(f"### {idx}위. [{recipe['title']}]({recipe['link']})")
                    cols = st.columns([1, 3])
                    with cols[0]:
                        if recipe["img_url"]:
                            st.image(recipe["img_url"], use_column_width=True)
                        else:
                            st.write("이미지 없음")
                    with cols[1]:
                        st.write(recipe["summary"] if recipe["summary"] else "설명 없음")
                    st.markdown("---")
            else:
                st.warning("해당 음식에 대한 인기 레시피를 찾을 수 없습니다. 다른 이름으로 시도해 보세요.")
    else:
        st.info("왼쪽에 음식 이름을 입력하고 '인기 레시피 검색' 버튼을 눌러주세요.")
with tab2:
    '''
    st.header("📖 레시피 검색")
    
    # 검색 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        search_type = st.selectbox(
            "검색 유형",
            ["음식명으로 검색", "재료로 검색", "조리법으로 검색"]
        )
        
        search_query = st.text_input(
            "검색어를 입력하세요:",
            placeholder="예: 김치찌개, 돼지고기, 간단한 요리"
        )
    
    with col2:
        cuisine_type = st.selectbox(
            "요리 종류",
            ["전체", "한식", "중식", "일식", "양식", "분식", "디저트"]
        )
        
        max_time = st.selectbox(
            "최대 조리시간",
            ["상관없음", "15분 이하", "30분 이하", "1시간 이하", "1시간 이상"]
        )
    
    if st.button("🔍 레시피 검색"):
        if search_query.strip():
            with st.spinner("레시피를 검색하고 있습니다..."):
                try:
                    search_prompt = f"""
{search_type}으로 레시피를 검색해주세요.

검색어: {search_query}
요리 종류: {cuisine_type}
최대 조리시간: {max_time}

다음 형식으로 JSON으로 응답해주세요:

{{
    "recipes": [
        {{
            "name": "음식명",
            "cuisine": "요리 종류",
            "cooking_time": "조리시간",
            "difficulty": "난이도",
            "servings": "인분",
            "ingredients": [
                {{
                    "name": "재료명",
                    "amount": "양",
                    "note": "참고사항"
                }}
            ],
            "instructions": [
                "조리 단계들"
            ],
            "tips": "조리 팁",
            "nutrition": {{
                "calories": "칼로리",
                "protein": "단백질",
                "carbs": "탄수화물",
                "fat": "지방"
            }}
        }}
    ],
    "total_found": "검색된 레시피 수",
    "search_summary": "검색 결과 요약"
}}

최소 3개의 레시피를 제공해주세요.
"""

                    response = client.chat.completions.create(
                        model="solar-pro2",
                        messages=[{"role": "user", "content": search_prompt}],
                        stream=False,
                    )
                    
                    try:
                        search_result = json.loads(response.choices[0].message.content)
                        st.session_state.search_result = search_result
                    except json.JSONDecodeError:
                        st.session_state.raw_search_response = response.choices[0].message.content
                        
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")
    
    # 검색 결과 표시
    if "search_result" in st.session_state:
        search_result = st.session_state.search_result
        
        st.subheader(f"📋 검색 결과 ({search_result['total_found']}개)")
        st.info(search_result['search_summary'])
        
        for i, recipe in enumerate(search_result['recipes'], 1):
            with st.expander(f"{i}. {recipe['name']} ({recipe['cuisine']})"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"**조리시간:** {recipe['cooking_time']}")
                    st.markdown(f"**난이도:** {recipe['difficulty']}")
                    st.markdown(f"**인분:** {recipe['servings']}")
                    
                    st.markdown("**재료:**")
                    for ingredient in recipe['ingredients']:
                        st.write(f"• {ingredient['name']}: {ingredient['amount']}")
                        if ingredient['note']:
                            st.caption(f"  ({ingredient['note']})")
                
                with col2:
                    st.markdown("**조리 순서:**")
                    for j, step in enumerate(recipe['instructions'], 1):
                        st.write(f"{j}. {step}")
                    
                    st.markdown(f"**조리 팁:** {recipe['tips']}")
                
                # 영양 정보
                st.markdown("**영양 정보:**")
                nutrition = recipe['nutrition']
                nut_cols = st.columns(4)
                with nut_cols[0]:
                    st.metric("칼로리", nutrition['calories'])
                with nut_cols[1]:
                    st.metric("단백질", nutrition['protein'])
                with nut_cols[2]:
                    st.metric("탄수화물", nutrition['carbs'])
                with nut_cols[3]:
                    st.metric("지방", nutrition['fat'])

    '''
with tab3:
    '''
    st.header("🍳 요리 도우미")
    
    # 요리 도우미 기능들
    helper_option = st.selectbox(
        "도움이 필요한 부분을 선택하세요:",
        ["재료 대체법", "조리 팁", "계량 변환", "음식 궁합", "보관법"]
    )
    
    if helper_option == "재료 대체법":
        st.subheader("🔄 재료 대체법")
        
        ingredient = st.text_input("대체하고 싶은 재료를 입력하세요:")
        
        if st.button("🔍 대체법 찾기"):
            if ingredient.strip():
                with st.spinner("대체법을 찾고 있습니다..."):
                    try:
                        substitute_prompt = f"""
'{ingredient}'의 대체재료를 알려주세요.

다음 형식으로 JSON으로 응답해주세요:

{{
    "original": "{ingredient}",
    "substitutes": [
        {{
            "name": "대체재료명",
            "ratio": "대체 비율",
            "notes": "대체 시 주의사항",
            "best_for": "어떤 요리에 적합한지"
        }}
    ],
    "tips": "대체 시 일반적인 팁"
}}
"""

                        response = client.chat.completions.create(
                            model="solar-pro2",
                            messages=[{"role": "user", "content": substitute_prompt}],
                            stream=False,
                        )
                        
                        try:
                            sub_result = json.loads(response.choices[0].message.content)
                            st.session_state.substitute_result = sub_result
                        except json.JSONDecodeError:
                            st.session_state.raw_substitute_response = response.choices[0].message.content
                            
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
    
    elif helper_option == "조리 팁":
        st.subheader("👨‍🍳 조리 팁")
        
        cooking_topic = st.text_input("궁금한 조리법을 입력하세요:")
        
        if st.button("💡 팁 받기"):
            if cooking_topic.strip():
                with st.spinner("조리 팁을 찾고 있습니다..."):
                    try:
                        tip_prompt = f"""
'{cooking_topic}'에 대한 조리 팁을 알려주세요.

다음 형식으로 JSON으로 응답해주세요:

{{
    "topic": "{cooking_topic}",
    "tips": [
        "조리 팁들"
    ],
    "common_mistakes": [
        "자주 하는 실수들"
    ],
    "pro_tips": [
        "전문가 팁들"
    ]
}}
"""

                        response = client.chat.completions.create(
                            model="solar-pro2",
                            messages=[{"role": "user", "content": tip_prompt}],
                            stream=False,
                        )
                        
                        try:
                            tip_result = json.loads(response.choices[0].message.content)
                            st.session_state.tip_result = tip_result
                        except json.JSONDecodeError:
                            st.session_state.raw_tip_response = response.choices[0].message.content
                            
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
    
    # 결과 표시
    if "substitute_result" in st.session_state:
        result = st.session_state.substitute_result
        st.success(f"**{result['original']}**의 대체재료")
        
        for sub in result['substitutes']:
            with st.expander(f"🔄 {sub['name']}"):
                st.markdown(f"**대체 비율:** {sub['ratio']}")
                st.markdown(f"**주의사항:** {sub['notes']}")
                st.markdown(f"**적합한 요리:** {sub['best_for']}")
        
        st.info(f"💡 **일반적인 팁:** {result['tips']}")
    
    elif "tip_result" in st.session_state:
        result = st.session_state.tip_result
        st.success(f"**{result['topic']}** 조리 팁")
        
        st.subheader("💡 조리 팁")
        for tip in result['tips']:
            st.write(f"• {tip}")
        
        st.subheader("❌ 자주 하는 실수")
        for mistake in result['common_mistakes']:
            st.write(f"• {mistake}")
        
        st.subheader("👨‍🍳 전문가 팁")
        for pro_tip in result['pro_tips']:
            st.write(f"• {pro_tip}")

    '''
with tab4:
    BEST_RECIPES = get_fallback_recipes('https://www.10000recipe.com/ranking/home_new.html?dtype=d&rtype=r', 10)
    st.header("🏆 만개의 레시피 베스트 순위")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**실시간 인기 레시피** - [만개의 레시피](https://www.10000recipe.com/index.html)에서 가져온 실제 데이터")
    with col2:
        if st.button("🔄 레시피 새로고침", type="secondary"):
            st.cache_data.clear()
            st.rerun()
    
    # 데이터 로딩 상태 표시
    if len(BEST_RECIPES) == 0:
        st.warning("레시피 데이터를 불러오는 중입니다...")
        st.stop()
    else:
        st.success(f"✅ {len(BEST_RECIPES)}개의 레시피를 성공적으로 불러왔습니다!")
    # 레시피들
    filtered_recipes = BEST_RECIPES
    st.markdown(f"**검색 결과: {len(filtered_recipes)}개**")
    
    # 레시피 카드 표시
    recipe_index = 0
    for recipe in filtered_recipes:
        recipe_index += 1
        with st.expander(f"[ {recipe_index} ] {recipe['title']}"):
            st.image(f"{recipe['img_url']}", caption=f"{recipe['link']} 의 자료")
            st.markdown(f"{recipe['summary']}")



st.markdown("---")
st.markdown("💡 **팁**: 더 정확한 추천을 위해 현재 상황을 자세히 설명해주세요!")
st.markdown("📊 **데이터 출처**: [만개의 레시피](https://www.10000recipe.com/index.html) - 실시간 인기 레시피") 
