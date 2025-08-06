import streamlit as st
from tkinter.tix import COLUMN
from pyparsing import empty

col1, empty, col2, empty1, col3, empty2, col4 = st.columns([5,1,1,1,1])

with col1:
    st.header("테스트1")

with empty:
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
    


left, middle1, middle2, right = st.columns(4, vertical_alignment="bottom")

left.text_input("Write something")
middle1.button("Click me", use_container_width=True)
middle2.success("SUCCESS")
right.checkbox("Check me")
