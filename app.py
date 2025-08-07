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
    # 🧠 AI 레시피 추천 탭
    with st.container():
        st.title("🍳 AI 레시피 추천")

        # 👉 컬럼 나누기: 왼쪽 입력, 오른쪽 결과
        col1, col2 = st.columns([1, 2])

        # ✅ 10000recipe 크롤링 함수
        def get_top5_recipes_from_10000recipe(dish_name):
            search_url = f"https://www.10000recipe.com/recipe/list.html?q={dish_name.replace(' ', '+')}"
            headers = {"User-Agent": "Mozilla/5.0"}

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
            except:
                return []

        # ✅ 왼쪽: 입력 영역
        with col1:
            st.header("🥕 요리 정보 입력")
            ingredients = st.text_area("재료 혹은 음식 이름 입력하세요", placeholder="예: 계란, 당근, 대파")
            cuisine = st.selectbox("원하는 요리 종류를 선택하세요", ["전체", "한식", "중식", "양식", "일식", "동남아식"])
            style = st.selectbox("요리 스타일을 선택하세요", ["전체", "고급", "일반", "간단"])
            submit = st.button("🍽️ 요리 추천")

        # ✅ 오른쪽: 결과 영역
        with col2:
            if submit:
                with st.spinner("AI가 요리를 추천 중입니다..."):

                    # 스타일별 안내 문구
                    style_description = {
                        "고급": "고급요리를 한개 추천해 주세요",
                        "일반": "일반 요리 스타일로, 보통 사람들이 쉽게 만들 수 있는 음식을 한개 추천해주세요",
                        "간단": "초보자도 쉽게 따라 할 수 있는 간단한 요리 스타일로 한개 추천해주세요",
                        "전체": "아무 요리 한개 추천해주세요"
                    }

                    prompt = (
                        f"요리를 한개 추천해 주세요\n"
                        f"재료 혹은 음식 : {ingredients}\n"
                        f"요리 종류: {cuisine}\n"
                        f"요리 스타일: {style}\n"
                        f"{style_description.get(style, '')}\n"
                        f"요리 이름 (굵게 양옆에 **)\n"
                        f"간단한 설명 (1줄 이내)\n"
                        f"레시피는 말하지 말고 이름과 설명만 줘\n"
                    )

                    try:
                        # ✅ AI 호출 (예시용 — 실제 모델 호출 코드로 교체 필요)
                        response = client.chat.completions.create(
                            model="solar-pro2",
                            messages=[{"role": "user", "content": prompt}],
                            stream=False
                        )
                        reply = response.choices[0].message.content
                        sections = reply.split("\n\n")

                        # 출력
                        for section in sections:
                            st.markdown(section)

                        # ✅ 요리 이름 추출
                        dish_name = None
                        for section in sections:
                            lines = section.strip().split("\n")
                            for line in lines:
                                m = re.match(r"^\s*1[.)]?\s*(요리\s*이름)?\s*[:\-]?\s*(.+)", line)
                                if m:
                                    candidate = m.group(2).strip()
                                    candidate = re.sub(r"[^가-힣a-zA-Z0-9\s]", "", candidate)
                                    if len(candidate) > 1:
                                        dish_name = candidate
                                        break
                            if dish_name:
                                break
                        if not dish_name:
                            dish_name = ingredients.split(",")[0].strip() if ingredients else "추천 요리"

                        # ✅ TOP 5 크롤링
                        recipes = get_top5_recipes_from_10000recipe(dish_name)
                        if recipes:
                            st.markdown(f"## 🔍 {dish_name} 관련 TOP 5 레시피")
                            for idx, recipe in enumerate(recipes, 1):
                                with st.form(f'dish_{idx}', clear_on_submit=False):
                                    st.markdown(f"### **[ {idx} ] {recipe['title']}**")
                                    col_img, col_desc, col_btn = st.columns([1, 4])
                                    with col_img:
                                        if recipe["img_url"]:
                                            st.image(recipe["img_url"], use_container_width=True)
                                    with col_desc:
                                        st.markdown(recipe["summary"])
                                    st.markdown(
                                        f'''
                                        <div style="
                                            display: flex;
                                            justify-content: center;
                                            align-items: center;
                                            height: 120px;  /* 상하높이 */
                                        ">
                                            <a href="{recipe["link"]}" target="_blank"
                                               style="
                                                   display: inline-block;
                                                   padding: 12px 28px;
                                                   border: 1px solid #D6D6D9;
                                                   color: #000000;
                                                   text-decoration: none;
                                                   border-radius: 8px;
                                                   font-size: 24px;
                                                   font-weight: bold;
                                               ">
                                               바로 가기
                                            </a>
                                        </div>
                                        ''',
                                        unsafe_allow_html=True
                                    )
                                    st.form_submit_button(" ", type="tertiary")

                            # 더 보기 링크
                            st.markdown(
                                f"[[ 👉 더 많은 레시피 보기 ]](https://www.10000recipe.com/recipe/list.html?q={dish_name.replace(' ', '+')})"
                            )
                        else:
                            st.info("❗ 관련 레시피를 찾을 수 없습니다.")
                    except Exception as e:
                        st.error(f"❌ 오류 발생: {e}")
            else:
                st.info("왼쪽에 재료를 입력하고 버튼을 눌러 추천을 받아보세요!")

    # 하단 안내
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

    st.title("디저트 추천기")
    st.markdown("음식 이름, 열량, 맛을 입력하면 AI가 어울리는 디저트를 추천해 드려요!")

    # 입력 영역 placeholder
    space = st.empty()

    # 상태 저장용
    if "recommend_mode" not in st.session_state:
        st.session_state.recommend_mode = False
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []

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
            "}"
        )
        try:
            # 예시 AI 호출 부분 (여기 수정하세요)
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
    if not st.session_state.recommend_mode:
        with space.form(key="dessert_form_enter"):
            food = st.text_input("🍽️ 먹었던 음식을 입력하세요:")
            dessert_type_options = ["상관없음", "케이크", "아이스크림", "과자", "푸딩", "타르트", "무스", "음료수", "파이"]
            taste_options = ["상관없음", "달콤", "진한", "상큼", "신", "짭짤", "시원", "탄산"]
            selected_type = st.selectbox("🍰 디저트 종류 선택", options=dessert_type_options)
            selected_taste = st.selectbox("😋 디저트 맛 선택", options=taste_options)
            if st.form_submit_button("🍰 디저트 추천해줘!"):
                with st.spinner("AI가 디저트를 추천하고 있습니다..."):
                    st.session_state.recommend_mode = True
                    st.session_state.recommendations = recommend_desserts_ai(food, selected_type, selected_taste)
                    st.rerun()
    else:
        with space.form(key="dessert_form_list"):
            st.markdown("### 🍨 추천 디저트 리스트")
            for d in st.session_state.recommendations:
                if isinstance(d, str):
                    st.error(d)
                    continue
                data = get_item_top1(f'https://www.pillyze.com/foods/search?query={d["link"]}')
                if "error" in data:
                    st.error(data["error"])
                else:
                    #st.markdown(f"### {data['title']} # [[더 알아보기]]({data["link"]})")
                    st.markdown(
                        f'''
                        <div style="display: flex; align-items: center;">
                            <h3 style="margin: 0;">{data['title']}</h3>
                            <a href="{data["link"]}" target="_blank"
                               style="
                                   display: inline-block;
                                   margin-left: 10px;
                                   padding: 6px 14px;
                                   border: 2px solid #007bff;
                                   color: #007bff;
                                   text-decoration: none;
                                   border-radius: 6px;
                                   font-size: 14px;
                                   font-weight: bold;
                               ">
                               바로 가기
                            </a>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                    st.caption(f"타입: {d['type']} | 열량: {data['g']} / {data['kcal']} | 맛: {d['taste']}")
            if st.form_submit_button("다시 추천하기"):
                st.session_state.recommend_mode = False
                st.session_state.recommendations = []
                st.rerun()

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
                    st.image(f"{recipe['img_url']}", caption=f"{recipe['link']} 의 자료", use_container_width=True)
                    st.markdown(f"{recipe['summary']}")
    except Exception as e:
        st.error(f"인기레시피 탭 오류: {e}")
        import traceback
        st.text(traceback.format_exc())
    st.markdown("---")
    st.markdown("💡 **팁**: 더 정확한 추천을 위해 현재 상황을 자세히 설명해주세요!")
    st.markdown("📊 **데이터 출처**: [만개의 레시피](https://www.10000recipe.com/ranking/home_new.html) - 실시간 인기 레시피") 

