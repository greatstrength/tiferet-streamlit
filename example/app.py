"""Calculator App — Streamlit entry point"""

from tiferet_streamlit import StreamlitApp
from views import CalculatorView, AboutView

# Initialize the Tiferet application.
app = StreamlitApp()
app.load_app_service(app_yaml_file='config.yml')

# Run the Streamlit app with multi-page navigation.
app.run('calc_app', pages={
    'calculator': CalculatorView,
    'about': AboutView,
})
