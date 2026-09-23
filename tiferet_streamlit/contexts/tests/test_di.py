'''Tiferet Streamlit – DI Context Tests'''

# *** imports

# ** infra
import pytest
from unittest.mock import MagicMock
from tiferet import TiferetError

# ** app
from tiferet_streamlit.assets.constants import (
    INVALID_VIEW_SERVICE_ID,
    VIEW_SERVICE_ID,
)
from tiferet_streamlit.contexts.di import get_view_service
from tiferet_streamlit.interfaces.view import ViewService

# *** helpers

# ** helper: stub_view_service
class StubViewService(ViewService):
    '''
    Concrete ViewService double for resolution tests.
    '''

    # * method: get_page
    def get_page(self, route: str):
        '''
        Return no page.

        :param route: The page route.
        :type route: str
        :return: None.
        :rtype: None
        '''
        return None

    # * method: list_pages
    def list_pages(self):
        '''
        Return no pages.

        :return: An empty page list.
        :rtype: list
        '''
        return []

# *** fixtures

# ** fixture: mock_app
@pytest.fixture
def mock_app() -> MagicMock:
    '''
    App double exposing get_dependency.

    :return: A MagicMock whose get_dependency can be configured per test.
    :rtype: MagicMock
    '''

    # Create an app double that exposes get_dependency.
    return MagicMock()

# *** tests

# ** test: get_view_service_returns_verified_dependency
def test_get_view_service_returns_verified_dependency(mock_app: MagicMock) -> None:
    '''
    Verify a ViewService double is returned for the default service id.

    :param mock_app: The app double.
    :type mock_app: MagicMock
    '''

    # Configure the dependency handler to return a view service.
    service = StubViewService()
    mock_app.get_dependency.return_value = service

    # Resolve the default view service.
    resolved = get_view_service(mock_app)

    # Assert the verified dependency is returned.
    assert resolved is service
    assert isinstance(resolved, ViewService)

    # Assert the default service id was forwarded with no flags.
    mock_app.get_dependency.assert_called_once_with(VIEW_SERVICE_ID)
    assert VIEW_SERVICE_ID == 'view_service'

# ** test: get_view_service_honors_custom_service_id_and_flags
def test_get_view_service_honors_custom_service_id_and_flags(mock_app: MagicMock) -> None:
    '''
    Verify a custom service id and flags are forwarded to get_dependency.

    :param mock_app: The app double.
    :type mock_app: MagicMock
    '''

    # Configure the dependency handler to return a view service.
    mock_app.get_dependency.return_value = StubViewService()

    # Resolve with a custom service id and flags.
    get_view_service(mock_app, 'other', 'a', 'b')

    # Assert the service id and flags were forwarded unchanged.
    mock_app.get_dependency.assert_called_once_with('other', 'a', 'b')

# ** test: get_view_service_raises_for_invalid_dependency
def test_get_view_service_raises_for_invalid_dependency(mock_app: MagicMock) -> None:
    '''
    Verify a non-ViewService dependency raises INVALID_VIEW_SERVICE.

    :param mock_app: The app double.
    :type mock_app: MagicMock
    '''

    # Configure the dependency handler to return a non-view service.
    resolved = object()
    mock_app.get_dependency.return_value = resolved

    # Assert the invalid dependency is rejected.
    with pytest.raises(TiferetError) as exc_info:
        get_view_service(mock_app)

    # Assert the error code and context identify the bad dependency.
    error = exc_info.value
    assert error.error_code == 'INVALID_VIEW_SERVICE'
    assert error.error_code == INVALID_VIEW_SERVICE_ID
    assert error.kwargs['service_id'] == VIEW_SERVICE_ID
    assert error.kwargs['resolved_type'] == type(resolved).__name__
