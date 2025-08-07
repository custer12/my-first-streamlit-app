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


        
# 탭 생성
tab1, tab2, tab3 = st.tabs(["🍳 AI 레시피 추천", "🧁 디저트 추천", "🏆 인기 레시피"])

with tab1:
    space1 = st.empty()
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
    ingredients = st.text_area("재료 혹은 음식 이름 입력하세요", placeholder="예: 계란, 당근, 대파")
    cuisine = st.selectbox("원하는 요리 종류를 선택하세요", ["전체","한식", "중식", "양식", "일식", "동남아식"])
    space1 = st.empty()

    # 요리 스타일 선택 추가
    style = st.selectbox("요리 스타일을 선택하세요", ["전체""고급", "일반", "간단"])
    submit = st.button("🍽️ 요리 추천")
    space1 = st.empty()
    # 결과 영역
    if submit:
        with st.spinner("요리를 생성 중입니다..."):
            st.markdown("---")

            # 스타일별로 AI에게 줄 추가 설명 문구 정의
            style_description = {
                "고급": "고급요리를 한개 추천해 주세요",
                "일반": "일반 요리 스타일로, 보통 사람들이 쉽게 만들 수 있는 음식을 한개 추천해주세요",
                "간단": "초보자도 쉽게 따라 할 수 있는 간단한 요리 스타일로 한개 추천해주세요",
                "전체": "아무 요리 한개 추천해주세요"
            }
            prompt = (
                f"요리를 한개 추천해 주세요"
                f"재료 혹은 음식 : {ingredients}\n"
                f"요리 종류: {cuisine}\n"
                f"요리 스타일: {style}\n"
                f"{style_description.get(style, '')}\n"  # 스타일에 맞는 설명 추가
                f"위 정보를 참고하여 아래 항목을 포함한 요리를 선택한 요리 스타일에 맞는 난이도로 추천해주세요(생략이나 불필요하면 아무런 택스트 없이 제거 합니다) (만약 냉장고 속 재료의 값이 비어있으면):\n"
                f"요리 이름 (굵게 양옆에 **)\n"
                f"간단한 설명 (1줄 이내로 요리의 특징이나 매력을 표현)\n"
                f"AI 즉 당신은 요리의 레시피는 말하면 안됩니다. 그냥 요리의 이름과 간단한 설명만 말해주세요.\n"
            )
            with space1.container():
                try:
                    # OpenAI 호출
                    response = client.chat.completions.create(
                        model="solar-pro2",
                        messages=[{"role": "user", "content": prompt}],
                        stream=False
                    )

                    reply = response.choices[0].message.content

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
                    if not dish_name:
                        dish_name = ingredients.split(",")[0].strip() if ingredients else "추천 요리"

                    recipes = get_top5_recipes_from_10000recipe(dish_name.replace(" ", "+"))
                    if recipes:
                        for idx, recipe in enumerate(recipes, 1):
                            with st.form(f'dish_{idx}', False):
                                st.markdown(f"### **[ {idx} ] [{recipe['title']}]**")
                                col1, col2, button = st.columns([1, 6, 3])
                                with col1:
                                    st.image(recipe["img_url"], width=100)
                                with col2:
                                    st.markdown(f"{recipe['summary']}")
                                with button:
                                    st.markdown(f"[🍽️ 레시피 보기]({recipe['link']})")
                                    st.form_submit_button(f" ", type="tertiary")
                        st.markdown(f"## {dish_name} 관련 레시피")
                        st.markdown(f"[[ 더 많이 알아보기 ]](https://www.10000recipe.com/recipe/list.html?q={dish_name.replace(" ", "+")})")
                    else:
                        st.info("🔍 10000레시피에서 관련 레시피를 찾을 수 없었습니다.")

                except Exception as e:
                    st.error(f"❌ 오류 발생: {e}")
    else:
        st.info("재료와 요리 종류를 입력하고 버튼을 눌러주세요!")
    st.markdown("---")
    st.markdown("💡 **팁**: 더 정확한 추천을 위해 현재 상황을 자세히 설명해주세요!")
    st.markdown("📊 **데이터 출처**: [만개의 레시피](https://www.10000recipe.com/)") 

with tab2:
    def get_item_top1(search_url):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            res = requests.get(search_url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            item_list_div = soup.find("div", id="itemList")
            if not item_list_div:
                return {"error": "itemList 없음"}

            item = item_list_div.find("a", class_="item-card")
            if not item:
                return {"error": "아이템 없음"}

            title_tag = item.select_one(".txt3")
            txt4_tag = item.select_one(".txt4")
            txt5_tag = item.select_one(".right .txt5")
            link = f"https://www.pillyze.com{item['href']}" if item.has_attr('href') else ""

            return {
                "title": title_tag.get_text(strip=True) if title_tag else "",
                "g": txt4_tag.get_text(strip=True) if txt4_tag else "",
                "kcal": txt5_tag.get_text(strip=True) if txt5_tag else "",
                "link": link
            }

        except Exception as e:
            return {"error": str(e)}

    # ✅ Streamlit 시작
    space1 = st.empty()
    st.title("디저트 추천기")
    st.markdown("""
    음식 이름, 열량, 맛을 입력하면 AI가 어울리는 디저트를 추천해 드려요!
    """)
    space = st.empty()
    with st.form(key="dessert_form"):
        with space.container():
            food = st.text_input("🍽️ 먹었던 음식을 입력하세요:")
            dessert_type_options = ["상관없음", "케이크", "아이스크림", "과자", "푸딩", "타르트", "무스", "음료수", "파이"]
            taste_options = ["상관없음", "달콤", "진한", "상큼", "신", "짭짤", "시원", "탄산"]
            selected_type = st.selectbox("🍰 디저트 종류 선택", options=dessert_type_options)
            selected_taste = st.selectbox("😋 디저트 맛 선택", options=taste_options)
            # ✅ AI에게 추천 요청
            def recommend_desserts_ai(food_name, type_selected, taste_selected):
                prompt = (
                    f"'{food_name}'와 어울리는 디저트를 3개 추천해줘.\n"
                    f"디저트 종류: {type_selected if type_selected != '상관없음' else '제한 없음'}\n"
                    f"맛: {taste_selected if taste_selected != '상관없음' else '제한 없음'}\n"
                    "아래 형식의 JSON만 반환해. 설명이나 다른 텍스트는 절대 포함하지 마:\n"
                    "{\n"
                    '  "desserts": [\n'
                    '    {"name": "디저트명", "type": "타입", "taste": "맛", "link":"여기에 띄어쓰기를 +로 바꾼 디저트명 적기"},\n'
                    '    ...\n'
                    "  ]\n"
                    "}\n"
                )
                try:
                    # 너의 OpenAI 클라이언트 객체 (예시)
                    response = client.chat.completions.create(
                        model="solar-pro2",
                        messages=[{"role": "user", "content": prompt}],
                        stream=False
                    )
                    reply = response.choices[0].message.content
                    import re
                    match = re.search(r'\{[\s\S]*\}', reply)
                    json_str = match.group(0) if match else reply
                    data = json.loads(json_str)
                    return data.get("desserts", [])
                except Exception as e:
                    return [f"AI 추천 오류: {e}"]
        if st.form_submit_button("🍰 디저트 추천해줘!"):
                space = st.empty()
                with st.spinner("AI가 디저트를 추천하고 있습니다..."):
                    recommendations = recommend_desserts_ai(food, selected_type, selected_taste)
                    with space.container():
                        st.markdown("### 🍨 추천 디저트 리스트")
                        for d in recommendations:
                            data = get_item_top1(f'https://www.pillyze.com/foods/search?query={d['link']}')
                            if isinstance(d, str):
                                st.error(d)
                            elif "error" in data:
                                st.error(data["error"])
                            else:
                                st.markdown(f"### {data['title']}")
                                st.caption(f"타입: {d['type']} | 열량: {data['g']} / {data['kcal']} | 맛: {d['taste']}")
                                st.link_button('더 알아보기', data['link'])
                    st.form_submit_button("확인")
    st.markdown("---")
    st.markdown("💡 **팁**: 더 정확한 추천을 위해 현재 상황을 자세히 설명해주세요!")
    st.markdown("📊 **데이터 출처**: [필라이즈](https://www.pillyze.com/) - 영양성분 등등") 

def get_fallback_recipes(search_url, top_n = 10):
    import concurrent.futures
    print('get_fallback_recipes 진입')
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        print('requests.get 시작')
        res = requests.get(search_url, headers=headers, timeout=10)
        print('requests.get 완료')
        res.raise_for_status()
        print('raise_for_status 완료')
        soup = BeautifulSoup(res.text, "html.parser")
        print('BeautifulSoup 파싱 완료')
        recipe_cards = soup.select(".common_sp_list_ul .common_sp_list_li")[:10]  # 무조건 10개만
        print(f'recipe_cards 개수: {len(recipe_cards)}')
        recipes = []
        detail_links = []
        for card in recipe_cards:
            title = card.select_one(".common_sp_caption_tit").get_text(strip=True)
            link = "https://www.10000recipe.com" + card.select_one("a")["href"]
            imgs = card.select(".common_sp_thumb img")
            img_url = imgs[-1]["src"] if imgs else None
            recipes.append({
                "title": title,
                "link": link,
                "img_url": img_url,
                "summary": ""
            })
            detail_links.append(link)
        # detail 요청을 병렬로 처리 (10개만)
        def fetch_summary(link):
            try:
                detail_res = requests.get(link, headers=headers, timeout=10)
                detail_res.raise_for_status()
                detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                intro_tag = detail_soup.select_one("#recipeIntro")
                return intro_tag.get_text(strip=True) if intro_tag else ""
            except Exception as e:
                print(f'detail 요청 실패: {e}')
                return ""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            summaries = list(executor.map(fetch_summary, detail_links))
        # summary를 recipes에 할당
        for i, summary in enumerate(summaries):
            recipes[i]["summary"] = summary
        print(f'최종 반환 recipes 개수: {len(recipes)}')
        return recipes
    except Exception as e:
        print(f'get_fallback_recipes 예외: {e}')
        import traceback
        print(traceback.format_exc())
        return []

with tab3:
    try:
        print(1)
        st.header("🏆 레시피 베스트 순위")
        space1 = st.empty()
        @st.cache_data
        def get_best_recipes():
            return get_fallback_recipes('https://www.10000recipe.com/ranking/home_new.html?dtype=d&rtype=r', 100)
        with space1.container():
            with st.spinner("레시피 데이터를 불러오는 중입니다..."):
                BEST_RECIPES = get_best_recipes()
        # 10개만 표시
        if len(BEST_RECIPES) == 0:
            st.warning("레시피 데이터를 불러오는 중입니다... (크롤링 실패 또는 네트워크 문제일 수 있습니다)")
        else:
            for i, recipe in enumerate(BEST_RECIPES):
                recipe_index = i + 1
                with st.expander(f"[ {recipe_index} ] {recipe['title'].replace('백종원', '~~백종원~~')}"):
                    st.image(f"{recipe['img_url']}", caption=f"{recipe['link']} 의 자료")
                    st.markdown(f"{recipe['summary']}")
    except Exception as e:
        st.error(f"인기레시피 탭 오류: {e}")
        import traceback
        st.text(traceback.format_exc())
    st.markdown("---")
    st.markdown("💡 **팁**: 더 정확한 추천을 위해 현재 상황을 자세히 설명해주세요!")
    st.markdown("📊 **데이터 출처**: [만개의 레시피](https://www.10000recipe.com/ranking/home_new.html) - 실시간 인기 레시피") 

