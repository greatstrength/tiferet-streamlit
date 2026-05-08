"""Tiferet Streamlit Assets Constants Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..constants import (
    VIEW_NOT_INITIALIZED_ID,
    PAGE_NOT_FOUND_ID,
    VIEW_RENDER_FAILED_ID,
    INVALID_VIEW_TYPE_ID,
    SESSION_KEY_PREFIX,
)

# *** tests

# ** test: all_constants_are_non_empty_strings
@pytest.mark.parametrize('constant', [
    VIEW_NOT_INITIALIZED_ID,
    PAGE_NOT_FOUND_ID,
    VIEW_RENDER_FAILED_ID,
    INVALID_VIEW_TYPE_ID,
    SESSION_KEY_PREFIX,
])
def test_all_constants_are_non_empty_strings(constant: str) -> None:
    '''
    Test that each constant is a non-empty string.
    '''

    assert isinstance(constant, str)
    assert len(constant) > 0


# ** test: constants_are_uppercase
@pytest.mark.parametrize('constant', [
    VIEW_NOT_INITIALIZED_ID,
    PAGE_NOT_FOUND_ID,
    VIEW_RENDER_FAILED_ID,
    INVALID_VIEW_TYPE_ID,
])
def test_constants_are_uppercase(constant: str) -> None:
    '''
    Test that error code constants are uppercase.
    '''

    assert constant == constant.upper()


# ** test: constants_are_distinct
def test_constants_are_distinct() -> None:
    '''
    Test that all error code constants have unique values.
    '''

    values = [
        VIEW_NOT_INITIALIZED_ID,
        PAGE_NOT_FOUND_ID,
        VIEW_RENDER_FAILED_ID,
        INVALID_VIEW_TYPE_ID,
    ]

    assert len(values) == len(set(values))
