'''Tiferet Streamlit – DI Context Tests'''

# *** imports

# ** infra
import pytest
from unittest.mock import MagicMock

# ** app
from tiferet import TiferetError
from tiferet.contexts.app import AppSessionContext
from tiferet.di import DIDynamicServiceContainer, ServiceResolver
from tiferet.domain import ServiceDependency
from tiferet_streamlit.assets.constants import INVALID_VIEW_SERVICE_ID, VIEW_SERVICE_ID
from tiferet_streamlit.contexts.di import get_view_service
from tiferet_streamlit.interfaces.view import ViewService
from tiferet_streamlit.repos.view import ViewYamlRepository

# *** helpers

# ** helper: fixed_container_resolver
class FixedContainerResolver(ServiceResolver):
    '''
    A minimal concrete ServiceResolver that always builds the same
    pre-loaded container, for exercising the real
    get_dependency(service_id, *flags) contract without mocking it.
    '''

    # * init
    def __init__(self, container: DIDynamicServiceContainer):
        '''
        Initialize the fixed-container resolver.

        :param container: The container every build_container call returns.
        :type container: DIDynamicServiceContainer
        '''

        super().__init__()
        self._container = container

    # * method: build_container
    def build_container(self, flags):
        '''
        Return the fixed container regardless of flags.

        :param flags: The normalized flag list (ignored).
        :type flags: list
        :return: The fixed container.
        :rtype: DIDynamicServiceContainer
        '''

        return self._container

# *** fixtures

# ** fixture: mock_app
@pytest.fixture
def mock_app() -> MagicMock:
    '''
    MagicMock standing in for AppSessionContext, exposing its flat
    get_dependency DI resolution attribute.

    :return: A mocked app session context.
    :rtype: MagicMock
    '''

    return MagicMock()

# *** tests: verification logic (mocked DI resolution)

# ** test: get_view_service_returns_verified_dependency
def test_get_view_service_returns_verified_dependency(mock_app: MagicMock) -> None:
    '''
    Verify get_view_service resolves via DI and returns a valid ViewService.

    :param mock_app: The mocked app session context.
    :type mock_app: MagicMock
    '''

    # Configure the DI resolution to return a ViewService-shaped mock.
    mock_view_service = MagicMock(spec=ViewService)
    mock_app.get_dependency.return_value = mock_view_service

    # Resolve the view service.
    result = get_view_service(mock_app)

    # Assert the DI context was consulted with the default service id and no flags.
    mock_app.get_dependency.assert_called_once_with(VIEW_SERVICE_ID)

    # Assert the verified dependency was returned unchanged.
    assert result is mock_view_service

# ** test: get_view_service_honors_custom_service_id_and_flags
def test_get_view_service_honors_custom_service_id_and_flags(mock_app: MagicMock) -> None:
    '''
    Verify get_view_service forwards a custom service_id and flags
    positionally, matching AppSessionContext.get_dependency(service_id, *flags).

    :param mock_app: The mocked app session context.
    :type mock_app: MagicMock
    '''

    # Configure the DI resolution to return a ViewService-shaped mock.
    mock_view_service = MagicMock(spec=ViewService)
    mock_app.get_dependency.return_value = mock_view_service

    # Resolve the view service with a custom id and flags.
    get_view_service(mock_app, 'custom_view_service', 'admin', 'prod')

    # Assert the DI context was consulted with the custom id and flags as positional args.
    mock_app.get_dependency.assert_called_once_with('custom_view_service', 'admin', 'prod')

# ** test: get_view_service_raises_for_invalid_dependency
def test_get_view_service_raises_for_invalid_dependency(mock_app: MagicMock) -> None:
    '''
    Verify get_view_service raises a structured error when the resolved
    dependency does not implement ViewService.

    :param mock_app: The mocked app session context.
    :type mock_app: MagicMock
    '''

    # Configure the DI resolution to return something that isn't a ViewService.
    mock_app.get_dependency.return_value = object()

    # Assert a structured TiferetError with INVALID_VIEW_SERVICE_ID is raised.
    with pytest.raises(TiferetError) as exc_info:
        get_view_service(mock_app)

    assert exc_info.value.error_code == INVALID_VIEW_SERVICE_ID

# *** tests: real DI resolution (no mocks)

# ** test_int: get_view_service_resolves_through_real_di_container
def test_int_get_view_service_resolves_through_real_di_container() -> None:
    '''
    Verify get_view_service works against tiferet's real DI machinery: a
    genuine ServiceResolver/ServiceContainer registering a real
    ViewYamlRepository, wired into a real AppSessionContext. Guards against
    a calling-convention mismatch (e.g. a stale flags-as-list assumption)
    that a MagicMock-only test would not catch.
    '''

    # Register a real ViewYamlRepository under the default view_service id.
    container = DIDynamicServiceContainer(services={
        VIEW_SERVICE_ID: ServiceDependency(
            module_path='tiferet_streamlit.repos.view',
            class_name='ViewYamlRepository',
            parameters={'view_config': 'unused/path.yml'},
        ),
    })
    resolver = FixedContainerResolver(container)

    # Wire the resolver's real get_dependency into a real AppSessionContext.
    app = AppSessionContext(get_dependency=resolver.get_dependency)

    # Resolve the view service through the real DI chain.
    result = get_view_service(app)

    # Assert a genuine, correctly-constructed ViewYamlRepository was returned.
    assert isinstance(result, ViewService)
    assert isinstance(result, ViewYamlRepository)
    assert result.yaml_file == 'unused/path.yml'

# ** test_int: get_view_service_raises_for_real_non_view_service_dependency
def test_int_get_view_service_raises_for_real_non_view_service_dependency() -> None:
    '''
    Verify get_view_service raises INVALID_VIEW_SERVICE_ID when a real DI
    container resolves the configured id to something that isn't a
    ViewService, exercising the same real AppSessionContext/get_dependency
    call path as the success case.
    '''

    # Register a plain object (not a ViewService) under the view_service id.
    container = DIDynamicServiceContainer(constants={
        VIEW_SERVICE_ID: object(),
    })
    resolver = FixedContainerResolver(container)
    app = AppSessionContext(get_dependency=resolver.get_dependency)

    # Assert a structured TiferetError with INVALID_VIEW_SERVICE_ID is raised.
    with pytest.raises(TiferetError) as exc_info:
        get_view_service(app)

    assert exc_info.value.error_code == INVALID_VIEW_SERVICE_ID
