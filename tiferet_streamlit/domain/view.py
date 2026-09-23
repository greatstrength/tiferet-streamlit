'''Tiferet Streamlit – View Domain Objects'''

# *** imports

# ** core
import importlib

# ** infra
from pydantic import Field

# ** app
from tiferet.domain.core import DomainObject, ModelError
from ..assets.constants import INVALID_VIEW_TYPE_ID

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
        :raises ModelError: If the module cannot be imported or the class is missing.
        '''

        # Import the module from the dotted path and resolve the class.
        try:
            module = importlib.import_module(self.view_module_path)
            view_type = getattr(module, self.view_class_name)

        # Raise a model error for a missing module or class.
        except (ModuleNotFoundError, AttributeError) as e:
            ModelError.raise_error(
                INVALID_VIEW_TYPE_ID,
                model=self,
                view_module_path=self.view_module_path,
                view_class_name=self.view_class_name,
                exception=str(e),
            )

        # Return the resolved class.
        return view_type
