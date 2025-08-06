import streamlit as st

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.header("테스트1")

with col2:
    st.header("테스트2")

with col3:
    st.header("테스트3")

with col4:
    st.header("테스트4")
