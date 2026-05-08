'''Tiferet Streamlit – View Domain Objects'''

# *** imports

# ** core
import importlib

# ** infra
from pydantic import Field

# ** app
from tiferet.domain.settings import DomainObject

# *** models

# ** model: page
class Page(DomainObject):
    '''
    A domain object representing configuration-driven page metadata
    for Streamlit multi-page applications.
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
        description='Optional icon for navigation.',
    )

    # * attribute: layout
    layout: str = Field(
        default='centered',
        description='Page layout. Accepts "centered" or "wide".',
    )

    # * attribute: view_module_path
    view_module_path: str = Field(
        ...,
        description='Dotted module path to the ViewContext class.',
    )

    # * attribute: view_class_name
    view_class_name: str = Field(
        ...,
        description='Class name of the ViewContext subclass.',
    )

    # * method: get_view_type
    def get_view_type(self) -> type:
        '''
        Dynamically import and return the ViewContext class.

        :return: The ViewContext subclass identified by view_module_path and view_class_name.
        :rtype: type
        :raises ModuleNotFoundError: If the module cannot be imported.
        :raises AttributeError: If the class does not exist in the module.
        '''

        # Import the module from the dotted path.
        module = importlib.import_module(self.view_module_path)

        # Resolve and return the class from the module.
        return getattr(module, self.view_class_name)
