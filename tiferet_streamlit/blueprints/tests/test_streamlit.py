'''Tiferet Streamlit – Streamlit Blueprint Tests'''

# *** imports

# ** infra
import pytest
from unittest.mock import MagicMock, patch

# ** app
from tiferet import TiferetError
from tiferet_streamlit.assets.constants import PAGE_NOT_FOUND_ID
from tiferet_streamlit.contexts.session import SessionCacheContext
from tiferet_streamlit.contexts.view import ViewContext
from tiferet_streamlit.contexts.page import PageContext
from tiferet_streamlit.domain.view import Page
from tiferet_streamlit.blueprints.streamlit import (
    create_view,
    build_pages,
    build_pages_from_config,
    build_streamlit_app,
)

# *** helpers

# ** helper: stub_view
class StubView(ViewContext):
    '''
    Minimal ViewContext subclass for testing.
    '''

    # * method: render
    def render(self):
        '''Render stub.'''
        return 'stub'


# *** fixtures

# ** fixture: mock_session_state
@pytest.fixture(autouse=True)
def mock_session_state():
    '''
    Replace streamlit.session_state with a plain dict for all blueprint tests.

    :return: A plain dict acting as session state.
    :rtype: dict
    '''

    state = {}
    with patch('streamlit.session_state', state):
        yield state


# ** fixture: mock_app_interface
@pytest.fixture
def mock_app_interface() -> MagicMock:
    '''
    MagicMock standing in for AppInterfaceContext.

    :return: A mocked app interface context.
    :rtype: MagicMock
    '''
    return MagicMock()


# *** tests: create_view

# ** test: create_view_returns_instance
def test_create_view_returns_instance(mock_app_interface: MagicMock) -> None:
    '''
    Verify create_view returns correct type with app and key.

    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Create a view.
    view = create_view(StubView, mock_app_interface, key='test')

    # Assert it is the correct type.
    assert isinstance(view, StubView)
    assert view.app is mock_app_interface
    assert view.key == 'test'


# ** test: create_view_auto_namespace
def test_create_view_auto_namespace(mock_app_interface: MagicMock) -> None:
    '''
    Verify session namespace matches key.

    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Create a view.
    view = create_view(StubView, mock_app_interface, key='ns_test')

    # Assert the session namespace matches the key.
    assert view.session.namespace == 'ns_test'


# ** test: create_view_custom_session
def test_create_view_custom_session(mock_app_interface: MagicMock) -> None:
    '''
    Verify custom session is used.

    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Create a custom session.
    custom_session = SessionCacheContext(namespace='custom')

    # Create a view with the custom session.
    view = create_view(StubView, mock_app_interface, key='test', session=custom_session)

    # Assert the custom session is used.
    assert view.session is custom_session


# *** tests: build_pages

# ** test: build_pages_returns_page_context
def test_build_pages_returns_page_context(mock_app_interface: MagicMock) -> None:
    '''
    Verify build_pages returns PageContext with registered pages.

    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Build pages.
    page_ctx = build_pages(mock_app_interface, {
        '/home': StubView,
        '/about': StubView,
    })

    # Assert it returns a PageContext with both pages.
    assert isinstance(page_ctx, PageContext)
    assert len(page_ctx.pages) == 2
    assert '/home' in page_ctx.pages
    assert '/about' in page_ctx.pages


# ** test: build_pages_view_keys_match_routes
def test_build_pages_view_keys_match_routes(mock_app_interface: MagicMock) -> None:
    '''
    Verify view keys match route strings.

    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Build pages.
    page_ctx = build_pages(mock_app_interface, {'/home': StubView})

    # Assert the view key matches the route.
    view = page_ctx.pages['/home']['view']
    assert view.key == '/home'


# *** tests: build_pages_from_config

# ** test: build_pages_from_config_returns_page_context
def test_build_pages_from_config_returns_page_context(mock_app_interface: MagicMock) -> None:
    '''
    Verify build from Page domain objects with title and icon.

    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Create Page domain objects pointing to StubView.
    page_config = Page(
        route='/home',
        title='Home',
        icon='🏠',
        view_module_path='tiferet_streamlit.blueprints.tests.test_streamlit',
        view_class_name='StubView',
    )

    # Build pages from config.
    page_ctx = build_pages_from_config(mock_app_interface, [page_config])

    # Assert it returns a PageContext with the page.
    assert isinstance(page_ctx, PageContext)
    assert '/home' in page_ctx.pages
    assert page_ctx.pages['/home']['title'] == 'Home'
    assert page_ctx.pages['/home']['icon'] == '🏠'


# *** tests: build_streamlit_app

# ** test: build_streamlit_app_with_pages
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.realize_interface')
@patch('tiferet_streamlit.blueprints.streamlit.resolve_interface')
def test_build_streamlit_app_with_pages(
        mock_resolve: MagicMock,
        mock_realize: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify build_streamlit_app with pages dict calls page_ctx.run().

    :param mock_resolve: The mocked resolve_interface function.
    :type mock_resolve: MagicMock
    :param mock_realize: The mocked realize_interface function.
    :type mock_realize: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure mocks.
    mock_app_interface = MagicMock()
    mock_app = MagicMock()
    mock_resolve.return_value = (mock_app_interface, [])
    mock_realize.return_value = mock_app

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Run with pages.
    build_streamlit_app('test_interface', pages={'/home': StubView})

    # Assert resolve and realize were called.
    mock_resolve.assert_called_once_with('test_interface')
    mock_realize.assert_called_once_with(mock_app_interface, 'test_interface')

    # Assert navigation ran.
    mock_nav.run.assert_called_once()


# ** test: build_streamlit_app_with_page_configs
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.realize_interface')
@patch('tiferet_streamlit.blueprints.streamlit.resolve_interface')
def test_build_streamlit_app_with_page_configs(
        mock_resolve: MagicMock,
        mock_realize: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify build_streamlit_app with page_configs list calls page_ctx.run().

    :param mock_resolve: The mocked resolve_interface function.
    :type mock_resolve: MagicMock
    :param mock_realize: The mocked realize_interface function.
    :type mock_realize: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure mocks.
    mock_app_interface = MagicMock()
    mock_app = MagicMock()
    mock_resolve.return_value = (mock_app_interface, [])
    mock_realize.return_value = mock_app

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Create page config.
    page_config = Page(
        route='/home',
        title='Home',
        view_module_path='tiferet_streamlit.blueprints.tests.test_streamlit',
        view_class_name='StubView',
    )

    # Run with page_configs.
    build_streamlit_app('test_interface', page_configs=[page_config])

    # Assert navigation ran.
    mock_nav.run.assert_called_once()


# ** test: build_streamlit_app_no_pages_raises_error
@patch('tiferet_streamlit.blueprints.streamlit.realize_interface')
@patch('tiferet_streamlit.blueprints.streamlit.resolve_interface')
def test_build_streamlit_app_no_pages_raises_error(
        mock_resolve: MagicMock,
        mock_realize: MagicMock,
    ) -> None:
    '''
    Verify TiferetError is raised when no pages provided.

    :param mock_resolve: The mocked resolve_interface function.
    :type mock_resolve: MagicMock
    :param mock_realize: The mocked realize_interface function.
    :type mock_realize: MagicMock
    '''

    # Configure mocks.
    mock_app_interface = MagicMock()
    mock_app = MagicMock()
    mock_resolve.return_value = (mock_app_interface, [])
    mock_realize.return_value = mock_app

    # Assert TiferetError with PAGE_NOT_FOUND_ID is raised.
    with pytest.raises(TiferetError) as exc_info:
        build_streamlit_app('test_interface')

    assert exc_info.value.error_code == PAGE_NOT_FOUND_ID


# ** test: build_streamlit_app_page_configs_take_precedence
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.realize_interface')
@patch('tiferet_streamlit.blueprints.streamlit.resolve_interface')
def test_build_streamlit_app_page_configs_take_precedence(
        mock_resolve: MagicMock,
        mock_realize: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify page_configs preferred over pages when both given.

    :param mock_resolve: The mocked resolve_interface function.
    :type mock_resolve: MagicMock
    :param mock_realize: The mocked realize_interface function.
    :type mock_realize: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure mocks.
    mock_app_interface = MagicMock()
    mock_app = MagicMock()
    mock_resolve.return_value = (mock_app_interface, [])
    mock_realize.return_value = mock_app

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav
    mock_st.Page.return_value = 'page_obj'

    # Create page config with a distinct title.
    page_config = Page(
        route='/config',
        title='Config Page',
        view_module_path='tiferet_streamlit.blueprints.tests.test_streamlit',
        view_class_name='StubView',
    )

    # Run with both pages and page_configs.
    build_streamlit_app(
        'test_interface',
        pages={'/dict': StubView},
        page_configs=[page_config],
    )

    # Assert st.Page was called with the config route, not the dict route.
    mock_st.Page.assert_called_once()
    call_kwargs = mock_st.Page.call_args[1]
    assert call_kwargs['url_path'] == '/config'
    assert call_kwargs['title'] == 'Config Page'
