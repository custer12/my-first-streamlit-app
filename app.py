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

import streamlit as st

left, middle1, middle2, right = st.columns(4, vertical_alignment="bottom")

left.text_input("Write something")
middle1.button("Click me", use_container_width=True)
middle2.success("SUCCESS")
right.checkbox("Check me")
