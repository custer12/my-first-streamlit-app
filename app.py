import streamlit as st
import requests
    
API_KEY= st.secrets["UPSTAGE_API_KEY"]

@st.cache_data(ttl=1800)
def fetch_recipes(API_KEY, start=1, end=10, recipe_name=None):
    base = "http://openapi.foodsafetykorea.go.kr/api"
    params = f"{API_KEY}/COOKRCP01/json/{start}/{end}"
    if recipe_name:
        params += f"/RCP_NM={recipe_name}"
    url = f"{base}/{params}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("COOKRCP01", {}).get("row", [])
    recipes = []
    for r in rows:
        recipes.append({
            "name": r.get("RCP_NM"),
            "category": r.get("RCP_PAT2"),
            "image": r.get("ATT_FILE_NO_MAIN"),
            "recipe_id": r.get("RCP_SEQ"),
        })
    return recipes

st.set_page_config(page_title="🍽️ 레시피 검색", layout="wide")
st.title("식품안전처 Recipe DB 검색")

if st.button("🔍 레시피 불러오기"):
    if not API_KEY:
        st.error("❌ API 키가 필요합니다.")
    else:
        try:
            recipes = fetch_recipes(API_KEY, 1, num, recipe_name or None)
            if recipes:
                for idx, rec in enumerate(recipes, 1):
                    st.markdown(f"### {idx}. {rec['name']} ({rec['category']})")
                    if rec['image']:
                        st.image(rec['image'], width=200)
            else:
                st.warning("검색 결과가 없습니다.")
        except Exception as e:
            st.error(f"API 호출 중 오류 발생: {e}")

