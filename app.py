import streamlit as st
from pyparsing import empty

col1, empty0, col2, empty1, col3, empty2, col4 = st.columns([1,0.5,1,0.5,1,0.5,1])

with col1:
    st.header("테스트1")

with empty0:
    empty()

with col2:
    st.header("테스트2")
    
with empty1:
    empty()

with col3:
    st.header("테스트3")
    
with empty2:
    empty()

with col4:
    st.header("테스트4")
    
