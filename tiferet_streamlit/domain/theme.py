'''Tiferet Streamlit – Theme Domain Object'''

# *** imports

# ** core
from typing import Dict

# ** infra
from pydantic import Field

# ** app
from tiferet.domain.settings import DomainObject

# *** models

# ** model: theme
class Theme(DomainObject):
    '''
    A domain object declaring an app's appearance as data — mirroring
    Streamlit's own native [theme] configuration keys, plus a slot for
    raw CSS not covered by them — so a brand color lives in one declared
    place instead of being hand-patched into every page's render().
    '''

    # * attribute: base
    base: str | None = Field(
        default=None,
        description='The base theme to build from ("light" or "dark").',
    )

    # * attribute: primary_color
    primary_color: str | None = Field(
        default=None,
        description='The accent color used for interactive elements.',
    )

    # * attribute: background_color
    background_color: str | None = Field(
        default=None,
        description='The background color for the main content area.',
    )

    # * attribute: secondary_background_color
    secondary_background_color: str | None = Field(
        default=None,
        description='The background color for the sidebar and widgets.',
    )

    # * attribute: text_color
    text_color: str | None = Field(
        default=None,
        description='The color used for most text.',
    )

    # * attribute: font
    font: str | None = Field(
        default=None,
        description='The font family used across the app.',
    )

    # * attribute: custom_css
    custom_css: str | None = Field(
        default=None,
        description='Raw CSS injected via st.markdown on every app run.',
    )

    # * method: native_fields (property)
    @property
    def native_fields(self) -> Dict[str, str]:
        '''
        Describe this theme's declared native [theme] keys, mapped to
        Streamlit's own camelCase config.toml key names.

        :return: A dict of only the native fields that were explicitly set.
        :rtype: Dict[str, str]
        '''

        # Map snake_case attributes to Streamlit's native TOML key names.
        native_key_map = {
            'base': 'base',
            'primary_color': 'primaryColor',
            'background_color': 'backgroundColor',
            'secondary_background_color': 'secondaryBackgroundColor',
            'text_color': 'textColor',
            'font': 'font',
        }

        # Return only the native fields that were declared.
        return {
            toml_key: getattr(self, attr)
            for attr, toml_key in native_key_map.items()
            if getattr(self, attr) is not None
        }
