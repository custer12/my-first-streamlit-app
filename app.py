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
tab1, tab2, tab3 = st.tabs(["🍳 AI 레시피 추천", "🧁 디저트 추천", "🏆 인기 레시피"])

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
                st.write(f"**{dish_name}**(와)과 관련된 10000레시피 인기 레시피를 요약해서 보여드립니다.")

                recipes = get_top5_recipes_from_10000recipe(dish_name.replace(" ", "+"))
                if recipes:
                    for idx, recipe in enumerate(recipes, 1):
                        with st.form(f'dish_{idx}'):
                            st.markdown(f"## **[ {idx} ] [{recipe['title']}]**")
                            if recipe["img_url"]:
                                col1, col2 = st.columns([1, 6])
                                with col1:
                                    st.image(recipe["img_url"], width=150)
                                with col2:
                                    st.markdown(f"{recipe['summary']}")
                                st.form_submit_button('ㅁ')
                            else:
                                st.write("이미지 없음")
                    st.markdown(f"### {dish_name} 관련 레시피")
                    st.markdown(f"[[ 더 많이 알아보기 ]](https://www.10000recipe.com/recipe/list.html?q={dish_name.replace(" ", "+")})")
                else:
                    st.info("🔍 10000레시피에서 관련 레시피를 찾을 수 없었습니다.")

            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
    else:
        st.info("재료와 요리 종류를 입력하고 버튼을 눌러주세요!")
with tab2:
    st.title("디저트 추천기")
    st.markdown("""
    음식 이름, 열량, 맛을 입력하면 AI가 어울리는 디저트를 추천해 드려요!
    

    """)

    col1, empty1, col2 = st.columns([1,0.05, 1])
    with col1:
        with st.form(key="dessert_form"):
            food = st.text_input("🍽️ 먹었던 음식을 입력하세요:")
            dessert_type_options = ["상관없음", "케이크", "아이스크림", "과자", "푸딩", "타르트", "무스", "음료수", "파이"]
            calorie_options = ["상관없음", "낮음", "높음"]
            taste_options = ["상관없음", "달콤", "진한", "상큼", "신", "짭짤", "시원", "탄산"]
            selected_type = st.selectbox("🍰 디저트 종류 선택", options=dessert_type_options)
            selected_calorie = st.selectbox("🔥 열량 수준 선택", options=calorie_options)
            selected_taste = st.selectbox("😋 디저트 맛 선택", options=taste_options)

            def recommend_desserts_ai(food_name, type_selected, calorie_selected, taste_selected):
                prompt = (
                    f"'{food_name}'와 어울리는 디저트를 3개 추천해줘.\n"
                    f"디저트 종류: {type_selected if type_selected != '상관없음' else '제한 없음'}\n"
                    f"열량 수준: {calorie_selected if calorie_selected != '상관없음' else '제한 없음'}\n"
                    f"맛: {taste_selected if taste_selected != '상관없음' else '제한 없음'}\n"
                    "아래 형식의 JSON만 반환해. 설명이나 다른 텍스트는 절대 포함하지 마:\n"
                    "{\n"
                    '  "desserts": [\n'
                    '    {"name": "디저트명", "type": "타입", "calorie": "열량", "taste": "맛", "description": "간단설명"},\n'
                    '    ...\n'
                    "  ]\n"
                    "}\n"
                )
                try:
                    response = client.chat.completions.create(
                        model="solar-pro2",
                        messages=[{"role": "user", "content": prompt}],
                        stream=False
                    )
                    reply = response.choices[0].message.content
                    import re
                    match = re.search(r'\{[\s\S]*\}', reply)
                    if match:
                        json_str = match.group(0)
                    else:
                        json_str = reply
                    data = json.loads(json_str)
                    return data.get("desserts", [])
                except Exception as e:
                    return [f"AI 추천 오류: {e}"]
            pass
            if st.form_submit_button("🍰 디저트 추천해줘!"):
                with col2:
                    with st.spinner("AI가 디저트를 추천하고 있습니다..."):
                        recommendations = recommend_desserts_ai(food, selected_type, selected_calorie, selected_taste)
                        st.markdown("### 🍨 추천 디저트 리스트")
                        for d in recommendations:
                            if isinstance(d, str):
                                st.error(d)
                            else:
                                with st.container():
                                    st.markdown(f"**🍰 {d['name']}**")
                                    st.caption(f"타입: {d['type']} | 열량: {d['calorie']} | 맛: {d['taste']}")
                                    st.write(f"💡 {d['description']}")
    with empty1:
        empty()


with tab3:
    BEST_RECIPES = get_fallback_recipes('https://www.10000recipe.com/ranking/home_new.html?dtype=d&rtype=r', 1000)
    st.header("🏆 레시피 베스트 순위")
    
    # 페이지네이션 설정
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    
    items_per_page = 10
    total_items = len(BEST_RECIPES)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**실시간 인기 레시피** - [만개의 레시피](https://www.10000recipe.com/index.html)에서 가져온 실제 데이터")
    with col2:
        col2_1, col2_2 = st.columns(2)
        with col2_1:
            if st.button("⬅️ 이전", disabled=st.session_state.current_page == 0):
                st.session_state.current_page = max(0, st.session_state.current_page - 1)
                st.rerun()
        with col2_2:
            if st.button("다음 ➡️", disabled=st.session_state.current_page >= total_pages - 1):
                st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
                st.rerun()
    
    # 페이지 정보 표시
    st.markdown(f"**페이지 {st.session_state.current_page + 1} / {total_pages}**")
    
    # 데이터 로딩 상태 표시
    if len(BEST_RECIPES) == 0:
        st.warning("레시피 데이터를 불러오는 중입니다...")
        st.stop()
    else:
        # 데이터 로딩 성공
        pass
    
    # 현재 페이지에 해당하는 레시피들만 표시
    start_idx = st.session_state.current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    current_recipes = BEST_RECIPES[start_idx:end_idx]
    
    # 레시피 카드 표시
    for i, recipe in enumerate(current_recipes):
        recipe_index = start_idx + i + 1
        with st.expander(f"[ {recipe_index} ] {recipe['title']}"):
            st.image(f"{recipe['img_url']}", caption=f"{recipe['link']} 의 자료")
            st.markdown(f"{recipe['summary']}")



st.markdown("---")
st.markdown("💡 **팁**: 더 정확한 추천을 위해 현재 상황을 자세히 설명해주세요!")
st.markdown("📊 **데이터 출처**: [만개의 레시피](https://www.10000recipe.com/index.html) - 실시간 인기 레시피") 
