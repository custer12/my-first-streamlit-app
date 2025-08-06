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
                    st.markdown(f"## {dish_name} 관련 레시피")
                    st.markdown(f"[[ 더 많이 알아보기 ]](https://www.10000recipe.com/recipe/list.html?q={dish_name.replace(" ", "+")})")
                else:
                    st.info("🔍 10000레시피에서 관련 레시피를 찾을 수 없었습니다.")

            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
    else:
        st.info("재료와 요리 종류를 입력하고 버튼을 눌러주세요!")
with tab2:
    st.title("디저트 추천기")
    st.write("음식을 입력하고, 원하는 디저트 타입, 열량, 맛을 선택하면 어울리는 디저트를 추천해 드려요!")

    desserts = [
        {"name": "초코 케이크", "calorie": 400, "type": "케이크", "taste": "진한"},
        {"name": "치즈 케이크", "calorie": 450, "type": "케이크", "taste": "진한"},
        {"name": "당근 케이크", "calorie": 380, "type": "케이크", "taste": "달콤"},
        {"name": "레드벨벳 케이크", "calorie": 420, "type": "케이크", "taste": "달콤"},
        {"name": "모카 케이크", "calorie": 410, "type": "케이크", "taste": "진한"},
        {"name": "바닐라 컵케이크", "calorie": 320, "type": "케이크", "taste": "달콤"},
        {"name": "초코 퐁당", "calorie": 330, "type": "케이크", "taste": "진한"},
        {"name": "티라미수", "calorie": 390, "type": "케이크", "taste": "진한"},
        {"name": "딸기 타르트", "calorie": 280, "type": "타르트", "taste": "상큼"},
        {"name": "체리 타르트", "calorie": 290, "type": "타르트", "taste": "상큼"},
        {"name": "레몬 타르트", "calorie": 270, "type": "타르트", "taste": "신"},
        {"name": "블루베리 타르트", "calorie": 300, "type": "타르트", "taste": "상큼"},
        {"name": "푸딩", "calorie": 250, "type": "푸딩", "taste": "달콤"},
        {"name": "카라멜 푸딩", "calorie": 280, "type": "푸딩", "taste": "달콤"},
        {"name": "녹차 아이스크림", "calorie": 200, "type": "아이스크림", "taste": "진한"},
        {"name": "바닐라 아이스크림", "calorie": 220, "type": "아이스크림", "taste": "달콤"},
        {"name": "망고 아이스크림", "calorie": 230, "type": "아이스크림", "taste": "상큼"},
        {"name": "피스타치오 아이스크림", "calorie": 240, "type": "아이스크림", "taste": "진한"},
        {"name": "민트 아이스크림", "calorie": 210, "type": "아이스크림", "taste": "시원"},
        {"name": "초코 쿠키", "calorie": 360, "type": "과자", "taste": "진한"},
        {"name": "아몬드 쿠키", "calorie": 340, "type": "과자", "taste": "짭짤"},
        {"name": "카라멜 팝콘", "calorie": 310, "type": "과자", "taste": "달콤"},
        {"name": "마카롱", "calorie": 290, "type": "과자", "taste": "달콤"},
        {"name": "젤리", "calorie": 180, "type": "과자", "taste": "상큼"},
        {"name": "블랙베리 젤리", "calorie": 190, "type": "과자", "taste": "상큼"},
        {"name": "허니 브레드", "calorie": 400, "type": "케이크", "taste": "달콤"},
        {"name": "피칸 파이", "calorie": 430, "type": "파이", "taste": "진한"},
        {"name": "호두 파이", "calorie": 420, "type": "파이", "taste": "진한"},
        {"name": "바나나 스무디", "calorie": 350, "type": "음료수", "taste": "달콤"},
        {"name": "망고 쉐이크", "calorie": 340, "type": "음료수", "taste": "상큼"},
        {"name": "레몬 에이드", "calorie": 200, "type": "음료수", "taste": "신"},
        {"name": "아이스 아메리카노", "calorie": 15, "type": "음료수", "taste": "진한"},
        {"name": "카라멜 라떼", "calorie": 320, "type": "음료수", "taste": "달콤"},
        {"name": "허브 티", "calorie": 5, "type": "음료수", "taste": "시원"},
        {"name": "허니 레몬 티", "calorie": 180, "type": "음료수", "taste": "신"},
        {"name": "딸기 쉐이크", "calorie": 300, "type": "음료수", "taste": "상큼"},
        {"name": "바닐라 라떼", "calorie": 310, "type": "음료수", "taste": "달콤"},
        {"name": "딸기 무스", "calorie": 260, "type": "무스", "taste": "달콤"},
        {"name": "초코 무스", "calorie": 280, "type": "무스", "taste": "진한"},
        {"name": "코코넛 무스", "calorie": 270, "type": "무스", "taste": "달콤"},
        {"name": "체리 무스", "calorie": 240, "type": "무스", "taste": "상큼"},
        {"name": "팥빙수", "calorie": 150, "type": "아이스크림", "taste": "시원"},
        {"name": "허니 브레드", "calorie": 400, "type": "케이크", "taste": "달콤"},
        {"name": "초콜릿 퐁당", "calorie": 330, "type": "케이크", "taste": "진한"},
        {"name": "딸기 젤리", "calorie": 190, "type": "과자", "taste": "상큼"},
        {"name": "레몬 셔벗", "calorie": 220, "type": "아이스크림", "taste": "신"},
        {"name": "콜라", "calorie": 200, "type": "음료수", "taste": "탄산"},
        {"name": "사이다", "calorie": 190, "type": "음료수", "taste": "탄산"},
        {"name": "토닉워터", "calorie": 150, "type": "음료수", "taste": "탄산"},
        {"name": "레몬 탄산수", "calorie": 120, "type": "음료수", "taste": "탄산"},
        {"name": "자몽 탄산수", "calorie": 130, "type": "음료수", "taste": "탄산"},
    ]

    # 칼로리 350 이상 -> 높음, 미만 -> 낮음
    col1, empty1, col2 = st.columns([1,0.1, 1])
    with col1:
        def calorie_level(cal):
            return "높음" if cal >= 350 else "낮음"

        # 필터 선택 옵션 생성
        all_types = ["상관없음"] + sorted(list({d["type"] for d in desserts}))
        all_calorie_levels = ["상관없음", "낮음", "높음"]
        all_tastes = ["상관없음"] + sorted(list({d["taste"] for d in desserts}))

        food = st.text_input("🍽️ 음식을 입력하세요:")

        selected_type = st.selectbox("🍰 디저트 타입 선택", options=all_types)
        selected_calorie = st.selectbox("🔥 열량 수준 선택", options=all_calorie_levels)
        selected_taste = st.selectbox("😋 디저트 맛 선택", options=all_tastes)

        def recommend_desserts(food_name, type_selected, calorie_selected, taste_selected):
            filtered = desserts

            if type_selected != "상관없음":
                filtered = [d for d in filtered if d["type"] == type_selected]

            if calorie_selected != "상관없음":
                filtered = [d for d in filtered if calorie_level(d["calorie"]) == calorie_selected]

            if taste_selected != "상관없음":
                filtered = [d for d in filtered if d["taste"] == taste_selected]

            if len(filtered) == 0:
                return ["조건에 맞는 디저트를 찾지 못했습니다."]
            else:
                return random.sample(filtered, min(5, len(filtered)))
    with empty1:
        empty()
        pass
        if st.button("🍰 디저트 추천해줘!"):
            if food.strip() == "":
                st.warning("음식 이름을 입력해주세요.")
            else:
                recommendations = recommend_desserts(food, selected_type, selected_calorie, selected_taste)
                with col2:
                    with st.form(key="dessert_form"):
                        st.markdown("### 🍨 추천 디저트 리스트")
                        for d in recommendations:
                            if isinstance(d, str):
                                st.write(d)
                            else:
                                level = calorie_level(d["calorie"])
                                st.write(f"- **{d['name']}** ({level} 열량, {d['type']}, {d['taste']} 맛)")
                        st.form_submit_button('확인')


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
