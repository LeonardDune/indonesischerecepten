import streamlit as st

st.set_page_config(layout="wide")

# Clear all filter-related session state
keys_to_clear = [k for k in st.session_state.keys() if k.startswith("cb_") or k.startswith("filter_")]
for k in keys_to_clear:
    del st.session_state[k]

# Clear query params
st.query_params.clear()

st.switch_page("pages/1_Recepten.py")
