'''Tiferet Streamlit – View Domain Object Tests'''

# *** imports

# ** infra
import pytest
from pydantic import ValidationError

# ** app
from tiferet_streamlit.domain.view import Page

# *** fixtures

# ** fixture: sample_page_data
@pytest.fixture
def sample_page_data() -> dict:
    '''
    Dict with minimal valid Page fields.

    :return: A dictionary of sample page data.
    :rtype: dict
    '''

    return dict(
        route='/home',
        title='Home',
        view_module_path='tiferet_streamlit.domain.view',
        view_class_name='Page',
    )


# ** fixture: sample_page
@pytest.fixture
def sample_page(sample_page_data: dict) -> Page:
    '''
    Page instance constructed from sample_page_data.

    :param sample_page_data: The sample page data dictionary.
    :type sample_page_data: dict
    :return: A Page instance.
    :rtype: Page
    '''

    return Page(**sample_page_data)


# *** tests

# ** test: page_required_fields
def test_page_required_fields(sample_page: Page, sample_page_data: dict) -> None:
    '''
    Verify required fields are stored correctly.

    :param sample_page: The sample Page instance.
    :type sample_page: Page
    :param sample_page_data: The sample page data dictionary.
    :type sample_page_data: dict
    '''

    # Assert each required field matches the input data.
    assert sample_page.route == sample_page_data['route']
    assert sample_page.title == sample_page_data['title']
    assert sample_page.view_module_path == sample_page_data['view_module_path']
    assert sample_page.view_class_name == sample_page_data['view_class_name']


# ** test: page_default_layout
def test_page_default_layout(sample_page: Page) -> None:
    '''
    Verify layout defaults to "centered".

    :param sample_page: The sample Page instance.
    :type sample_page: Page
    '''

    # Assert the default layout value.
    assert sample_page.layout == 'centered'


# ** test: page_default_icon_none
def test_page_default_icon_none(sample_page: Page) -> None:
    '''
    Verify icon defaults to None.

    :param sample_page: The sample Page instance.
    :type sample_page: Page
    '''

    # Assert the default icon value.
    assert sample_page.icon is None


# ** test: page_custom_layout
def test_page_custom_layout(sample_page_data: dict) -> None:
    '''
    Verify custom layout is stored.

    :param sample_page_data: The sample page data dictionary.
    :type sample_page_data: dict
    '''

    # Create a page with a custom layout.
    page = Page(**{**sample_page_data, 'layout': 'wide'})

    # Assert the custom layout value.
    assert page.layout == 'wide'


# ** test: page_custom_icon
def test_page_custom_icon(sample_page_data: dict) -> None:
    '''
    Verify custom icon is stored.

    :param sample_page_data: The sample page data dictionary.
    :type sample_page_data: dict
    '''

    # Create a page with a custom icon.
    page = Page(**{**sample_page_data, 'icon': '🏠'})

    # Assert the custom icon value.
    assert page.icon == '🏠'


# ** test: page_get_view_type
def test_page_get_view_type(sample_page: Page) -> None:
    '''
    Verify get_view_type() resolves the correct class.

    :param sample_page: The sample Page instance.
    :type sample_page: Page
    '''

    # Resolve the view type.
    view_type = sample_page.get_view_type()

    # Assert it returns the expected class.
    assert view_type is Page


# ** test: page_get_view_type_invalid_module
def test_page_get_view_type_invalid_module(sample_page_data: dict) -> None:
    '''
    Verify ModuleNotFoundError for a bad module path.

    :param sample_page_data: The sample page data dictionary.
    :type sample_page_data: dict
    '''

    # Create a page with an invalid module path.
    page = Page(**{**sample_page_data, 'view_module_path': 'nonexistent.module'})

    # Assert ModuleNotFoundError is raised.
    with pytest.raises(ModuleNotFoundError):
        page.get_view_type()


# ** test: page_get_view_type_invalid_class
def test_page_get_view_type_invalid_class(sample_page_data: dict) -> None:
    '''
    Verify AttributeError for a bad class name.

    :param sample_page_data: The sample page data dictionary.
    :type sample_page_data: dict
    '''

    # Create a page with an invalid class name.
    page = Page(**{**sample_page_data, 'view_class_name': 'NonexistentClass'})

    # Assert AttributeError is raised.
    with pytest.raises(AttributeError):
        page.get_view_type()


# ** test: page_rejects_extra_fields
def test_page_rejects_extra_fields(sample_page_data: dict) -> None:
    '''
    Verify DomainObject(extra='forbid') rejects unknown fields.

    :param sample_page_data: The sample page data dictionary.
    :type sample_page_data: dict
    '''

    # Attempt to create a page with an extra field.
    with pytest.raises(ValidationError):
        Page(**{**sample_page_data, 'unknown_field': 'value'})
