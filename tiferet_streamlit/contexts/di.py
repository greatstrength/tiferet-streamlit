'''Tiferet Streamlit – DI Contexts'''

# *** imports

# ** core
from typing import List

# ** infra
from tiferet import TiferetError
from tiferet.contexts.app import AppSessionContext

# ** app
from ..assets.constants import INVALID_VIEW_SERVICE_ID, VIEW_SERVICE_ID
from ..interfaces.view import ViewService

# *** functions

# ** function: get_view_service
def get_view_service(
        app: AppSessionContext,
        service_id: str = VIEW_SERVICE_ID,
        flags: List[str] = None,
    ) -> ViewService:
    '''
    Resolve and verify a DI-registered ViewService by configuration ID.

    This is the sole sanctioned path for reaching a ViewService instance:
    callers (blueprints included) never import ViewService or a concrete
    repository directly, they resolve one through this accessor instead.

    :param app: The realized Tiferet app session context.
    :type app: AppSessionContext
    :param service_id: The DI service configuration ID to resolve.
    :type service_id: str
    :param flags: Optional feature/data flags to use for resolution.
    :type flags: List[str]
    :return: The resolved and verified ViewService instance.
    :rtype: ViewService
    :raises TiferetError: If the resolved dependency does not implement
        ViewService, carrying error_code INVALID_VIEW_SERVICE_ID and the
        attempted service_id / resolved type for diagnosis.
    '''

    # Resolve the dependency via the app's feature-level DI context.
    resolved = app.features.services.get_dependency(service_id, flags)

    # Verify the resolved dependency actually implements ViewService.
    if not isinstance(resolved, ViewService):
        TiferetError.raise_error(
            INVALID_VIEW_SERVICE_ID,
            service_id=service_id,
            resolved_type=type(resolved).__name__,
        )

    # Return the verified ViewService instance.
    return resolved
