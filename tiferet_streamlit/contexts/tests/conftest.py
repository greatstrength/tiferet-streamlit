'''Tiferet Streamlit – Context Test Configuration'''

# *** imports

# ** infra
import pytest
from unittest.mock import patch

# *** fixtures

# ** fixture: mock_session_state
@pytest.fixture(autouse=True)
def mock_session_state():
    '''
    Replace streamlit.session_state with a plain dict for all context tests.
    Yields the dict for direct inspection.

    :return: A plain dict acting as session state.
    :rtype: dict
    '''

    # Create a plain dict to stand in for session state.
    state = {}

    # Patch st.session_state with the dict.
    with patch('streamlit.session_state', state):
        yield state
