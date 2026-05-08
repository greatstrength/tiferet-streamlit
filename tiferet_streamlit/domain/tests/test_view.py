"""Tiferet Streamlit Domain View Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..view import Page

# *** fixtures

# ** fixture: sample_page_data
@pytest.fixture
def sample_page_data() -> dict:
    '''
    Minimal valid data for constructing a Page domain object.
    '''
    return dict(
        route='calculator',
        title='Calculator',
        view_module_path='tiferet_streamlit.contexts.view',
        view_class_name='ViewContext',
    )


# ** fixture: sample_page
@pytest.fixture
def sample_page(sample_page_data: dict) -> Page:
    '''
    A Page instance with default values.
    '''
    return Page(**sample_page_data)


# *** tests

# ** test: page_required_fields
def test_page_required_fields(sample_page: Page) -> None:
    '''
    Test that Page constructs correctly with required fields.
    '''

    assert sample_page.route == 'calculator'
    assert sample_page.title == 'Calculator'
    assert sample_page.view_module_path == 'tiferet_streamlit.contexts.view'
    assert sample_page.view_class_name == 'ViewContext'


# ** test: page_default_layout
def test_page_default_layout(sample_page: Page) -> None:
    '''
    Test that layout defaults to 'centered'.
    '''

    assert sample_page.layout == 'centered'


# ** test: page_default_icon_none
def test_page_default_icon_none(sample_page: Page) -> None:
    '''
    Test that icon defaults to None.
    '''

    assert sample_page.icon is None


# ** test: page_custom_layout
def test_page_custom_layout(sample_page_data: dict) -> None:
    '''
    Test that a custom layout is stored correctly.
    '''

    page = Page(**{**sample_page_data, 'layout': 'wide'})

    assert page.layout == 'wide'


# ** test: page_custom_icon
def test_page_custom_icon(sample_page_data: dict) -> None:
    '''
    Test that a custom icon is stored correctly.
    '''

    page = Page(**{**sample_page_data, 'icon': ':calculator:'})

    assert page.icon == ':calculator:'


# ** test: page_get_view_type
def test_page_get_view_type(sample_page: Page) -> None:
    '''
    Test that get_view_type resolves the correct class.
    '''

    from tiferet_streamlit.contexts.view import ViewContext

    view_cls = sample_page.get_view_type()

    assert view_cls is ViewContext


# ** test: page_get_view_type_invalid_module
def test_page_get_view_type_invalid_module(sample_page_data: dict) -> None:
    '''
    Test that get_view_type raises ModuleNotFoundError for a bad module path.
    '''

    page = Page(**{**sample_page_data, 'view_module_path': 'nonexistent.module'})

    with pytest.raises(ModuleNotFoundError):
        page.get_view_type()


# ** test: page_get_view_type_invalid_class
def test_page_get_view_type_invalid_class(sample_page_data: dict) -> None:
    '''
    Test that get_view_type raises AttributeError for a bad class name.
    '''

    page = Page(**{**sample_page_data, 'view_class_name': 'NonexistentClass'})

    with pytest.raises(AttributeError):
        page.get_view_type()


# ** test: page_rejects_extra_fields
def test_page_rejects_extra_fields(sample_page_data: dict) -> None:
    '''
    Test that Page rejects unknown fields (DomainObject has extra='forbid').
    '''

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Page(**{**sample_page_data, 'unknown_field': 'value'})
