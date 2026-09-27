'''Tiferet Streamlit – Blueprints Package'''

# *** exports

# ** export: streamlit
from .streamlit import build_streamlit_app, inject_theme_css

# ** export: alias
StreamlitApp = build_streamlit_app
