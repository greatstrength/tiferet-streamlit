'''Tiferet Streamlit – Theme Domain Objects'''

# *** imports

# ** core
from typing import Dict, Optional

# ** infra
from pydantic import Field

# ** app
from tiferet.domain.core import DomainObject

# *** models

# ** model: theme
class Theme(DomainObject):
    '''
    A theme declares appearance as data so a brand color lives in one place
    instead of being patched into every ``render()``.
    '''

    # * attribute: base
    base: Optional[str] = Field(
        default=None,
        description='The base theme to build from ("light" or "dark").',
    )

    # * attribute: primary_color
    primary_color: Optional[str] = Field(
        default=None,
        description='The accent color used for interactive elements.',
    )

    # * attribute: background_color
    background_color: Optional[str] = Field(
        default=None,
        description='The background color for the main content area.',
    )

    # * attribute: secondary_background_color
    secondary_background_color: Optional[str] = Field(
        default=None,
        description='The background color for the sidebar and widgets.',
    )

    # * attribute: text_color
    text_color: Optional[str] = Field(
        default=None,
        description='The color used for most text.',
    )

    # * attribute: font
    font: Optional[str] = Field(
        default=None,
        description='The font family used across the app.',
    )

    # * attribute: custom_css
    custom_css: Optional[str] = Field(
        default=None,
        description='Raw CSS injected via st.markdown on every app run.',
    )

    # * method: native_fields (property)
    @property
    def native_fields(self) -> Dict[str, str]:
        '''
        Map set native attributes to Streamlit ``[theme]`` keys.

        Unset attributes are omitted. ``custom_css`` is not a native field
        and is never included.

        :return: Native theme values keyed by Streamlit TOML names.
        :rtype: Dict[str, str]
        '''

        # Pair each native attribute with its Streamlit key.
        native_keys = (
            ('base', 'base'),
            ('primary_color', 'primaryColor'),
            ('background_color', 'backgroundColor'),
            ('secondary_background_color', 'secondaryBackgroundColor'),
            ('text_color', 'textColor'),
            ('font', 'font'),
        )

        # Keep only attributes whose value is set.
        fields: Dict[str, str] = {}
        for attribute, key in native_keys:
            value = getattr(self, attribute)
            if value is not None:
                fields[key] = value

        # Return the native field map.
        return fields
