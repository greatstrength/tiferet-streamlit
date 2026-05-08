"""Tiferet Streamlit Domain View Models"""

# *** imports

# ** core
from importlib import import_module

# ** infra
from pydantic import Field

# ** app
from tiferet.domain.settings import DomainObject

# *** models

# ** model: page
class Page(DomainObject):
    '''
    Configuration-driven page metadata for a Streamlit multi-page application.

    Defines the routing, display properties, and the ViewContext class
    to render for this page.
    '''

    # * attribute: route
    route: str = Field(
        ...,
        description='The URL path for the page.',
    )

    # * attribute: title
    title: str = Field(
        ...,
        description='The display title for the page.',
    )

    # * attribute: icon
    icon: str | None = Field(
        default=None,
        description='An optional icon for the page navigation.',
    )

    # * attribute: layout
    layout: str = Field(
        default='centered',
        description='The page layout. One of "centered" or "wide".',
    )

    # * attribute: view_module_path
    view_module_path: str = Field(
        ...,
        description='The module path to the ViewContext class for this page.',
    )

    # * attribute: view_class_name
    view_class_name: str = Field(
        ...,
        description='The class name of the ViewContext for this page.',
    )

    # * method: get_view_type
    def get_view_type(self) -> type:
        '''
        Import and return the ViewContext class for this page.

        :return: The ViewContext class.
        :rtype: type
        '''

        # Import and return the view class.
        return getattr(import_module(self.view_module_path), self.view_class_name)
