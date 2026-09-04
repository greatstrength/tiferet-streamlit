'''Tiferet Streamlit – View Domain Objects'''

# *** imports

# ** core
import importlib

# ** infra
from pydantic import Field

# ** app
from tiferet.domain.settings import DomainObject
from tiferet.events.static import RaiseError
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
        :raises TiferetError: If the module cannot be imported or the class does not
            exist, carrying error_code INVALID_VIEW_TYPE_ID and the attempted
            view_module_path / view_class_name for diagnosis.
        '''

        # Attempt to import the module and resolve the class from the dotted path.
        try:
            module = importlib.import_module(self.view_module_path)
            return getattr(module, self.view_class_name)

        # Re-raise a structured error carrying the attempted module path and class name.
        except (ModuleNotFoundError, AttributeError) as e:
            RaiseError.execute(
                error_code=INVALID_VIEW_TYPE_ID,
                view_module_path=self.view_module_path,
                view_class_name=self.view_class_name,
                exception=str(e),
            )
