'''Calculator Example – Entry Point'''

from tiferet_streamlit import StreamlitApp
from views import CalculatorView, AboutView

# Create the application.
app = StreamlitApp()

# Load the app service with consolidated config.
app.load_app_service(app_yaml_file='config.yml')

# Run the multi-page application.
app.run('calc_app', pages={
    'calculator': CalculatorView,
    'about': AboutView,
})
