'''Tiferet Streamlit – Blueprints Package'''

# *** exports

# ** export: streamlit
from .streamlit import build_streamlit_app

# ** export: alias
StreamlitApp = build_streamlit_app
