'''Tiferet Streamlit – Asset Constants Tests'''

# *** imports

# ** infra
import pytest

# ** app
from tiferet_streamlit.assets import INCOMPATIBLE_APP_CONTEXT_ID as EXPORTED_INCOMPATIBLE_APP_CONTEXT_ID
from tiferet_streamlit.assets.constants import (
    VIEW_NOT_INITIALIZED_ID,
    PAGE_NOT_FOUND_ID,
    VIEW_RENDER_FAILED_ID,
    INVALID_VIEW_TYPE_ID,
    INCOMPATIBLE_APP_CONTEXT_ID,
    SESSION_KEY_PREFIX,
)

# *** tests

# ** test: all_constants_are_non_empty_strings
@pytest.mark.parametrize('constant', [
    VIEW_NOT_INITIALIZED_ID,
    PAGE_NOT_FOUND_ID,
    VIEW_RENDER_FAILED_ID,
    INVALID_VIEW_TYPE_ID,
    INCOMPATIBLE_APP_CONTEXT_ID,
    SESSION_KEY_PREFIX,
])
def test_all_constants_are_non_empty_strings(constant: str) -> None:
    '''
    Test that each constant is a non-empty string.

    :param constant: The constant value to check.
    :type constant: str
    '''

    # Assert the constant is a string.
    assert isinstance(constant, str)

    # Assert the constant is non-empty.
    assert len(constant) > 0


# ** test: constants_are_uppercase
@pytest.mark.parametrize('constant', [
    VIEW_NOT_INITIALIZED_ID,
    PAGE_NOT_FOUND_ID,
    VIEW_RENDER_FAILED_ID,
    INVALID_VIEW_TYPE_ID,
    INCOMPATIBLE_APP_CONTEXT_ID,
])
def test_constants_are_uppercase(constant: str) -> None:
    '''
    Test that each error code constant is uppercase.

    :param constant: The error code constant value to check.
    :type constant: str
    '''

    # Assert the constant value is uppercase.
    assert constant == constant.upper()


# ** test: constants_are_distinct
def test_constants_are_distinct() -> None:
    '''
    Test that all error code constants have unique values.
    '''

    # Collect all error code constants.
    error_codes = [
        VIEW_NOT_INITIALIZED_ID,
        PAGE_NOT_FOUND_ID,
        VIEW_RENDER_FAILED_ID,
        INVALID_VIEW_TYPE_ID,
        INCOMPATIBLE_APP_CONTEXT_ID,
    ]

    # Assert all values are distinct.
    assert len(error_codes) == len(set(error_codes))


# ** test: incompatible_app_context_id
def test_incompatible_app_context_id() -> None:
    '''
    Verify the incompatible app context error id value and assets export.
    '''

    # Assert the constant value.
    assert INCOMPATIBLE_APP_CONTEXT_ID == 'INCOMPATIBLE_APP_CONTEXT'

    # Assert the assets package exports the same constant.
    assert EXPORTED_INCOMPATIBLE_APP_CONTEXT_ID == INCOMPATIBLE_APP_CONTEXT_ID
