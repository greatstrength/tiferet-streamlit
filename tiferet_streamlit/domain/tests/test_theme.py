'''Tiferet Streamlit – Theme Domain Object Tests'''

# *** imports

# ** app
from tiferet_streamlit import Theme as PackageTheme
from tiferet_streamlit.domain import Theme as DomainTheme
from tiferet_streamlit.domain.theme import Theme

# *** tests

# ** test: theme_defaults_are_none
def test_theme_defaults_are_none() -> None:
    '''
    Verify a bare Theme leaves every field unset and maps no native keys.
    '''

    # Construct a theme with no fields set.
    theme = Theme()

    # Assert every field defaults to None.
    assert theme.base is None
    assert theme.primary_color is None
    assert theme.background_color is None
    assert theme.secondary_background_color is None
    assert theme.text_color is None
    assert theme.font is None
    assert theme.custom_css is None

    # Assert the native map is empty.
    assert theme.native_fields == {}


# ** test: theme_is_exported
def test_theme_is_exported() -> None:
    '''
    Verify Theme is importable from the domain package and the package root.
    '''

    # Assert both public names are this model.
    assert DomainTheme is Theme
    assert PackageTheme is Theme


# ** test: native_fields_uses_streamlit_keys
def test_native_fields_uses_streamlit_keys() -> None:
    '''
    Verify set native attributes map to Streamlit camelCase keys.
    '''

    # Set the accent color and font.
    theme = Theme(
        primary_color='#ff4b4b',
        font='serif',
    )

    # Assert only those keys appear, under Streamlit names.
    assert theme.native_fields == {
        'primaryColor': '#ff4b4b',
        'font': 'serif',
    }


# ** test: native_fields_maps_every_set_attribute
def test_native_fields_maps_every_set_attribute() -> None:
    '''
    Verify each set native attribute uses its Streamlit TOML key.
    '''

    # Set every native attribute and custom CSS.
    theme = Theme(
        base='light',
        primary_color='#111111',
        background_color='#222222',
        secondary_background_color='#333333',
        text_color='#444444',
        font='monospace',
        custom_css='body { margin: 0; }',
    )

    # Assert the camelCase map and the absence of custom CSS.
    assert theme.native_fields == {
        'base': 'light',
        'primaryColor': '#111111',
        'backgroundColor': '#222222',
        'secondaryBackgroundColor': '#333333',
        'textColor': '#444444',
        'font': 'monospace',
    }


# ** test: native_fields_omits_custom_css
def test_native_fields_omits_custom_css() -> None:
    '''
    Verify custom CSS does not add a native Streamlit theme key.
    '''

    # Set custom CSS alongside one native field.
    theme = Theme(
        custom_css='h1 { color: red; }',
        base='dark',
    )

    # Assert custom CSS is stored but absent from the native map.
    assert theme.custom_css == 'h1 { color: red; }'
    assert 'custom_css' not in theme.native_fields
    assert theme.native_fields == {'base': 'dark'}
