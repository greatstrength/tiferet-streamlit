"""Tiferet Streamlit Contexts Test Configuration"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest


# *** fixtures

# ** fixture: mock_session_state
@pytest.fixture(autouse=True)
def mock_session_state():
    '''
    Replace st.session_state with a plain dict for all context tests.
    Automatically applied to every test in this directory.
    '''

    state = {}
    with mock.patch('streamlit.session_state', state):
        yield state
