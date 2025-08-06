import streamlit as st
import requests
from bs4 import BeautifulSoup

@st.cache_data(ttl=1800)
def crawl_best_recipes():
    url = "https://www.10000recipe.com/index.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    # 인기 레시피 박스 찾기
    section = soup.select_one('ul.rcp_m_list')  # 실제 구조 확인 필요
    recipes = []

    if section:
        items = section.select('li.common_sp_list_li a.common_sp_link')[:10]
        for a in items:
            title = a.select_one('.common_sp_caption_tit').get_text(strip=True)
            href = a.get('href')
            full_link = f"https://www.10000recipe.com{href}" if href else "#"
            recipes.append({"title": title, "link": full_link})

    return recipes

# Streamlit UI
st.set_page_config(page_title="🍽️ 인기 레시피 제목 크롤링", page_icon="🍽️")
st.title("🍽️ 만개의레시피 인기 레시피")

data = crawl_best_recipes()
if data:
    for i, item in enumerate(data, 1):
        st.markdown(f"{i}. [{item['title']}]({item['link']})")
else:
    st.warning("😢 인기 레시피를 찾을 수 없습니다.")
