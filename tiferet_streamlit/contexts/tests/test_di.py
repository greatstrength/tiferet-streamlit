'''Tiferet Streamlit – DI Context Tests'''

# *** imports

# ** infra
import pytest
from unittest.mock import MagicMock

# ** app
from tiferet import TiferetError
from tiferet_streamlit.assets.constants import INVALID_VIEW_SERVICE_ID, VIEW_SERVICE_ID
from tiferet_streamlit.contexts.di import get_view_service
from tiferet_streamlit.interfaces.view import ViewService

# *** fixtures

# ** fixture: mock_app
@pytest.fixture
def mock_app() -> MagicMock:
    '''
    MagicMock standing in for AppInterfaceContext, exposing the
    features.services.get_dependency DI resolution chain.

    :return: A mocked app interface context.
    :rtype: MagicMock
    '''

    return MagicMock()

# *** tests

# ** test: get_view_service_returns_verified_dependency
def test_get_view_service_returns_verified_dependency(mock_app: MagicMock) -> None:
    '''
    Verify get_view_service resolves via DI and returns a valid ViewService.

    :param mock_app: The mocked app interface context.
    :type mock_app: MagicMock
    '''

    # Configure the DI resolution to return a ViewService-shaped mock.
    mock_view_service = MagicMock(spec=ViewService)
    mock_app.features.services.get_dependency.return_value = mock_view_service

    # Resolve the view service.
    result = get_view_service(mock_app)

    # Assert the DI context was consulted with the default service id.
    mock_app.features.services.get_dependency.assert_called_once_with(VIEW_SERVICE_ID, None)

    # Assert the verified dependency was returned unchanged.
    assert result is mock_view_service

# ** test: get_view_service_honors_custom_service_id_and_flags
def test_get_view_service_honors_custom_service_id_and_flags(mock_app: MagicMock) -> None:
    '''
    Verify get_view_service forwards a custom service_id and flags.

    :param mock_app: The mocked app interface context.
    :type mock_app: MagicMock
    '''

    # Configure the DI resolution to return a ViewService-shaped mock.
    mock_view_service = MagicMock(spec=ViewService)
    mock_app.features.services.get_dependency.return_value = mock_view_service

    # Resolve the view service with a custom id and flags.
    get_view_service(mock_app, service_id='custom_view_service', flags=['admin'])

    # Assert the DI context was consulted with the custom arguments.
    mock_app.features.services.get_dependency.assert_called_once_with('custom_view_service', ['admin'])

# ** test: get_view_service_raises_for_invalid_dependency
def test_get_view_service_raises_for_invalid_dependency(mock_app: MagicMock) -> None:
    '''
    Verify get_view_service raises a structured error when the resolved
    dependency does not implement ViewService.

    :param mock_app: The mocked app interface context.
    :type mock_app: MagicMock
    '''

    # Configure the DI resolution to return something that isn't a ViewService.
    mock_app.features.services.get_dependency.return_value = object()

    # Assert a structured TiferetError with INVALID_VIEW_SERVICE_ID is raised.
    with pytest.raises(TiferetError) as exc_info:
        get_view_service(mock_app)

    assert exc_info.value.error_code == INVALID_VIEW_SERVICE_ID
