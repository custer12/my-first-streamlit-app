import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="음식 레시피 추천", layout="wide")
st.title("🍽️ 10000레시피 인기 레시피 순위별 요약")

st.write(
    """
    원하는 음식 이름을 입력하면, 10000레시피 사이트에서 해당 음식의 인기 레시피를 순위별로 정리해서 보여줍니다.
    사이트에 직접 들어가지 않아도 대표 레시피와 요약 정보를 한눈에 확인할 수 있습니다.
    """
)

def get_top_recipes(food_name, top_n=5):
    search_url = f"https://www.10000recipe.com/recipe/list.html?q={food_name}"
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

with st.form("food_search_form"):
    food_name = st.text_input("음식 이름을 입력하세요", placeholder="예: 김치찌개, 파스타, 초밥 등")
    top_n = st.slider("몇 개의 인기 레시피를 볼까요?", min_value=3, max_value=10, value=5)
    submitted = st.form_submit_button("인기 레시피 검색")

if submitted and food_name.strip():
    with st.spinner("10000레시피에서 인기 레시피를 찾는 중입니다..."):
        recipes = get_top_recipes(food_name, top_n)
        if recipes:
            st.success(f"'{food_name}'에 대한 인기 레시피 {len(recipes)}개를 찾았습니다!")
            for recipe in enumerate(recipes, 1):
                st.markdown(f"### [{recipe['title']}]({recipe['link']})")
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
