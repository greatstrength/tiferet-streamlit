'''Calculator Example – Entry Point'''

from tiferet_streamlit import StreamlitApp
from views import CalculatorView, AboutView

# Run the multi-page application.
StreamlitApp('calc_app', pages={
    'calculator': CalculatorView,
    'about': AboutView,
}, app_yaml_file='config.yml')
