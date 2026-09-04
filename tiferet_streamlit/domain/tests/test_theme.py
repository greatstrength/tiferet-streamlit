'''Tiferet Streamlit – Theme Domain Object Tests'''

# *** imports

# ** infra
import pytest
from pydantic import ValidationError

# ** app
from tiferet_streamlit.domain.theme import Theme

# *** tests

# ** test: theme_defaults_are_none
def test_theme_defaults_are_none() -> None:
    '''
    Verify all fields default to None when a Theme is declared bare.
    '''

    # Create a bare theme.
    theme = Theme()

    # Assert every field defaults to None.
    assert theme.base is None
    assert theme.primary_color is None
    assert theme.background_color is None
    assert theme.secondary_background_color is None
    assert theme.text_color is None
    assert theme.font is None
    assert theme.custom_css is None

# ** test: theme_native_fields_empty_by_default
def test_theme_native_fields_empty_by_default() -> None:
    '''
    Verify native_fields is empty when no native keys were declared.
    '''

    # Create a bare theme.
    theme = Theme()

    # Assert native_fields is empty.
    assert theme.native_fields == {}

# ** test: theme_native_fields_maps_to_streamlit_keys
def test_theme_native_fields_maps_to_streamlit_keys() -> None:
    '''
    Verify native_fields maps snake_case attributes to Streamlit's
    camelCase [theme] config.toml key names.
    '''

    # Declare a theme with every native field set.
    theme = Theme(
        base='dark',
        primary_color='#FF4B4B',
        background_color='#0E1117',
        secondary_background_color='#262730',
        text_color='#FAFAFA',
        font='sans serif',
    )

    # Assert the mapped native fields.
    assert theme.native_fields == {
        'base': 'dark',
        'primaryColor': '#FF4B4B',
        'backgroundColor': '#0E1117',
        'secondaryBackgroundColor': '#262730',
        'textColor': '#FAFAFA',
        'font': 'sans serif',
    }

# ** test: theme_native_fields_excludes_custom_css
def test_theme_native_fields_excludes_custom_css() -> None:
    '''
    Verify native_fields never includes custom_css, since it is applied
    through a separate, always-runtime-applicable path.
    '''

    # Declare a theme with only custom_css set.
    theme = Theme(custom_css='.stButton { color: red; }')

    # Assert native_fields remains empty.
    assert theme.native_fields == {}

# ** test: theme_native_fields_only_includes_declared_fields
def test_theme_native_fields_only_includes_declared_fields() -> None:
    '''
    Verify native_fields includes only the fields that were explicitly set.
    '''

    # Declare a theme with a single native field set.
    theme = Theme(primary_color='#FF4B4B')

    # Assert only the declared field is present.
    assert theme.native_fields == {'primaryColor': '#FF4B4B'}

# ** test: theme_custom_css_stored
def test_theme_custom_css_stored() -> None:
    '''
    Verify custom_css is stored verbatim.
    '''

    # Declare a theme with custom CSS.
    css = '.stButton button { border-radius: 8px; }'
    theme = Theme(custom_css=css)

    # Assert the CSS is stored unchanged.
    assert theme.custom_css == css

# ** test: theme_rejects_extra_fields
def test_theme_rejects_extra_fields() -> None:
    '''
    Verify DomainObject(extra='forbid') rejects unknown fields.
    '''

    # Attempt to create a theme with an extra field.
    with pytest.raises(ValidationError):
        Theme(unknown_field='value')
