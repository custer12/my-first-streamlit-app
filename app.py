import streamlit as st
from openai import OpenAI
import json
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from pyparsing import empty

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
    page_title="AI 음식 추천", 
    page_icon="🍽️",
    layout="wide"
)

st.title("AI 음식 추천")
st.markdown("AI 추천과 레시피 정보를 제공합니다!")


def get_fallback_recipes(search_url, top_n = 10):
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
            imgs = card.select(".common_sp_thumb img")
            img_url = imgs[-1]["src"] if imgs else None
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
tab1, tab2, tab3 = st.tabs(["🍳 AI 레시피 추천", "🧁 AI 디저트 추천", "🏆 인기 레시피"])

with tab1:
    # 페이지 설정
    st.title("🍳 AI 레시피 추천")
    # 10000레시피에서 추천 요리 관련 TOP5 레시피를 크롤링하는 함수 (이미지 포함)
    def get_top5_recipes_from_10000recipe(dish_name):
        search_url = f"https://www.10000recipe.com/recipe/list.html?q={dish_name.replace(" ", "+")}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        try:
            res = requests.get(search_url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            recipe_cards = soup.select(".common_sp_list_ul .common_sp_list_li")[:5]
            recipes = []
            for card in recipe_cards:
                title = card.select_one(".common_sp_caption_tit").get_text(strip=True)
                link = "https://www.10000recipe.com" + card.select_one("a")["href"]
                intro = ""
                try:
                    detail_res = requests.get(link, headers=headers, timeout=10)
                    detail_res.raise_for_status()
                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                    intro_tag = detail_soup.select_one("#recipeIntro")
                    intro = intro_tag.get_text(strip=True) if intro_tag else ""
                except:
                    pass
                imgs = card.select(".common_sp_thumb img")
                img_url = imgs[-1]["src"] if imgs else None
                recipes.append({
                    "title": title,
                    "link": link,
                    "summary": intro,
                    "img_url": img_url
                })
            return recipes
        except Exception as e:
            return []

    st.header("🥕 요리 정보 입력")
    ingredients = st.text_area("냉장고 속 재료를 입력하세요", placeholder="예: 계란, 당근, 대파")
    cuisine = st.selectbox("원하는 요리 종류를 선택하세요", ["한식", "중식", "양식", "일식", "동남아식", "전체"])

    # 요리 스타일 선택 추가
    style = st.selectbox("요리 스타일을 선택하세요", ["고급", "일반", "간단", "전체"])
    submit = st.button("🍽️ 요리 추천")
    st.markdown("---")

    # 결과 영역
    if submit:
        with st.spinner("요리를 생성 중입니다..."):

            # 스타일별로 AI에게 줄 추가 설명 문구 정의
            style_description = {
                "고급": "고급요리를 한개 추천해 주세요",
                "일반": "일반 요리 스타일로, 보통 사람들이 쉽게 만들 수 있는 음식을 한개 추천해주세요",
                "간단": "초보자도 쉽게 따라 할 수 있는 간단한 요리 스타일로 한개 추천해주세요",
                "전체": "아무 요리 한개 추천해주세요"
            }
            prompt = (
                f"요리를 한개 추천해 주세요"
                f"재료: {ingredients}\n"
                f"요리 종류: {cuisine}\n"
                f"요리 스타일: {style}\n"
                f"{style_description.get(style, '')}\n"  # 스타일에 맞는 설명 추가
                f"위 정보를 참고하여 아래 항목을 포함한 요리를 선택한 요리 스타일에 맞는 난이도로 추천해주세요(생략이나 불필요하면 아무런 택스트 없이 제거 합니다) (만약 냉장고 속 재료의 값이 비어있으면):\n"
                f"1. 요리 이름 (크게)\n"
                f"2. 간단한 설명 (1줄 이내로 요리의 특징이나 매력을 표현)\n"
                f"3. AI 즉 당신은 요리의 레시피는 말하면 안됩니다. 그냥 요리의 이름과 간단한 설명만 말해주세요.\n"
            )

            try:
                # OpenAI 호출
                response = client.chat.completions.create(
                    model="solar-pro2",
                    messages=[{"role": "user", "content": prompt}],
                    stream=False
                )

                reply = response.choices[0].message.content

                # GPT 응답 출력 영역
                st.subheader("🍽️ 추천 요리 결과")
                st.markdown("📝 **AI가 추천한 요리입니다!**")

                sections = reply.split("\n\n")
                for section in sections:
                    st.markdown(section)

                # dish_name 추출 개선: 다양한 형식 대응 및 한글/영문/숫자 추출
                dish_name = None
                # 1. "1. 요리 이름 : 김치볶음밥" 또는 "1. 김치볶음밥" 또는 "1) 김치볶음밥" 등 다양한 케이스 대응
                for section in sections:
                    lines = section.strip().split("\n")
                    for line in lines:
                        # "1. 요리 이름 : ..." 또는 "1. ..." 또는 "1) ..." 등
                        m = re.match(r"^\s*1[.)]?\s*(요리\s*이름)?\s*[:\-]?\s*(.+)", line)
                        if m:
                            # m.group(2)에 요리 이름이 들어감
                            candidate = m.group(2).strip()
                            # 한글, 영문, 숫자, 공백만 남기고 추출
                            candidate = re.sub(r"[^가-힣a-zA-Z0-9\s]", "", candidate)
                            # 너무 짧거나 이상하면 무시
                            if len(candidate) > 1:
                                dish_name = candidate
                                break
                    if dish_name:
                        break
                # 만약 위에서 못찾으면, 첫 번째 줄에서 한글+영문+숫자 2글자 이상만 추출
                if not dish_name:
                    for section in sections:
                        lines = section.strip().split("\n")
                        for line in lines:
                            candidate = re.findall(r"[가-힣a-zA-Z0-9 ]{2,}", line)
                            if candidate:
                                dish_name = candidate[0].strip()
                                break
                        if dish_name:
                            break
                # 그래도 못찾으면 재료에서 첫 번째 재료 사용
                if not dish_name:
                    dish_name = ingredients.split(",")[0].strip() if ingredients else "추천 요리"

                # 10000레시피에서 추천 요리 관련 TOP5 레시피 요약 및 링크+이미지 출력
                st.markdown("---")
                st.subheader("🍳 '만개의 레시피' 인기 레시피 TOP 5 요약")
                st.write(f"**{dish_name}**(와)과 관련된 10000레시피 인기 레시피를 요약해서 보여드립니다.")

                recipes = get_top5_recipes_from_10000recipe(dish_name.replace(" ", "+"))
                if recipes:
                    for idx, recipe in enumerate(recipes, 1):
                        st.markdown(f"### **[ {idx} ] [{recipe['title']}]({recipe['link']})**")
                        if recipe["img_url"]:
                            col1, col2 = st.columns([1, 6])
                            with col1:
                                st.image(recipe["img_url"], width=150)
                            with col2:
                                st.markdown(f"{recipe['summary']}")
                        else:
                            st.write("이미지 없음")
                        st.markdown("---")
                    st.markdown(f"[ 더 많이 알아보기 ](https://www.10000recipe.com/recipe/list.html?q={dish_name.replace(" ", "+")})")
                else:
                    st.info("🔍 10000레시피에서 관련 레시피를 찾을 수 없었습니다.")

            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
    else:
        st.info("재료와 요리 종류를 입력하고 버튼을 눌러주세요!")
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
        st.success(f"✅ 레시피를 성공적으로 불러왔습니다!")
    # 레시피들
    filtered_recipes = BEST_RECIPES
    
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
