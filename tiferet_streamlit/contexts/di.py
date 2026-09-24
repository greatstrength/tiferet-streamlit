'''Tiferet Streamlit – DI Contexts'''

# *** imports

# ** infra
from tiferet import TiferetError
from tiferet.contexts.app import AppSessionContext

# ** app
from ..assets.constants import (
    INVALID_VIEW_SERVICE_ID,
    VIEW_SERVICE_ID,
)
from ..interfaces.view import ViewService

# *** functions

# ** function: get_view_service
def get_view_service(
        app: AppSessionContext,
        service_id: str = VIEW_SERVICE_ID,
        *flags: str,
    ) -> ViewService:
    '''
    Resolve a ViewService from the app session's dependency handler.

    This is the sole sanctioned path to a ViewService instance. Blueprints
    do not import the interface or a repository to obtain one.

    :param app: The app session whose dependency handler resolves the service.
    :type app: AppSessionContext
    :param service_id: The dependency identifier to resolve.
    :type service_id: str
    :param flags: Optional dependency flags forwarded to get_dependency.
    :type flags: str
    :return: The resolved view service.
    :rtype: ViewService
    '''

    # Resolve the dependency from the app session.
    resolved = app.get_dependency(service_id, *flags)

    # Reject anything that is not a ViewService.
    if not isinstance(resolved, ViewService):
        TiferetError.raise_error(
            INVALID_VIEW_SERVICE_ID,
            service_id=service_id,
            resolved_type=type(resolved).__name__,
        )

    # Return the verified view service.
    return resolved
