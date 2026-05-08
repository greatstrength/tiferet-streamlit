'''Tiferet Streamlit – Streamlit Builder Tests'''

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
from tiferet_streamlit.builders.main import StreamlitBuilder

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
    Replace streamlit.session_state with a plain dict for all builder tests.

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


# ** fixture: builder
@pytest.fixture
def builder() -> StreamlitBuilder:
    '''
    StreamlitBuilder instance with mocked internals.

    :return: A StreamlitBuilder instance.
    :rtype: StreamlitBuilder
    '''

    # Create a builder with a mocked service provider to avoid real DI.
    with patch.object(StreamlitBuilder, 'create_service_provider', return_value=MagicMock()):
        return StreamlitBuilder()


# *** tests: create_view

# ** test: create_view_returns_instance
def test_create_view_returns_instance(builder: StreamlitBuilder, mock_app_interface: MagicMock) -> None:
    '''
    Verify create_view returns correct type with app and key.

    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Create a view.
    view = builder.create_view(StubView, mock_app_interface, key='test')

    # Assert it is the correct type.
    assert isinstance(view, StubView)
    assert view.app is mock_app_interface
    assert view.key == 'test'


# ** test: create_view_auto_namespace
def test_create_view_auto_namespace(builder: StreamlitBuilder, mock_app_interface: MagicMock) -> None:
    '''
    Verify session namespace matches key.

    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Create a view.
    view = builder.create_view(StubView, mock_app_interface, key='ns_test')

    # Assert the session namespace matches the key.
    assert view.session.namespace == 'ns_test'


# ** test: create_view_custom_session
def test_create_view_custom_session(builder: StreamlitBuilder, mock_app_interface: MagicMock) -> None:
    '''
    Verify custom session is used.

    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Create a custom session.
    custom_session = SessionCacheContext(namespace='custom')

    # Create a view with the custom session.
    view = builder.create_view(StubView, mock_app_interface, key='test', session=custom_session)

    # Assert the custom session is used.
    assert view.session is custom_session


# *** tests: build_pages

# ** test: build_pages_returns_page_context
def test_build_pages_returns_page_context(builder: StreamlitBuilder, mock_app_interface: MagicMock) -> None:
    '''
    Verify build_pages returns PageContext with registered pages.

    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Build pages.
    page_ctx = builder.build_pages(mock_app_interface, {
        '/home': StubView,
        '/about': StubView,
    })

    # Assert it returns a PageContext with both pages.
    assert isinstance(page_ctx, PageContext)
    assert len(page_ctx.pages) == 2
    assert '/home' in page_ctx.pages
    assert '/about' in page_ctx.pages


# ** test: build_pages_view_keys_match_routes
def test_build_pages_view_keys_match_routes(builder: StreamlitBuilder, mock_app_interface: MagicMock) -> None:
    '''
    Verify view keys match route strings.

    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Build pages.
    page_ctx = builder.build_pages(mock_app_interface, {'/home': StubView})

    # Assert the view key matches the route.
    view = page_ctx.pages['/home']['view']
    assert view.key == '/home'


# *** tests: build_pages_from_config

# ** test: build_pages_from_config_returns_page_context
def test_build_pages_from_config_returns_page_context(builder: StreamlitBuilder, mock_app_interface: MagicMock) -> None:
    '''
    Verify build from Page domain objects with title and icon.

    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    :param mock_app_interface: The mocked app interface context.
    :type mock_app_interface: MagicMock
    '''

    # Create Page domain objects pointing to StubView.
    page_config = Page(
        route='/home',
        title='Home',
        icon='🏠',
        view_module_path='tiferet_streamlit.builders.tests.test_main',
        view_class_name='StubView',
    )

    # Build pages from config.
    page_ctx = builder.build_pages_from_config(mock_app_interface, [page_config])

    # Assert it returns a PageContext with the page.
    assert isinstance(page_ctx, PageContext)
    assert '/home' in page_ctx.pages
    assert page_ctx.pages['/home']['title'] == 'Home'
    assert page_ctx.pages['/home']['icon'] == '🏠'


# *** tests: run

# ** test: run_with_pages_calls_page_ctx_run
@patch('tiferet_streamlit.contexts.page.st')
def test_run_with_pages_calls_page_ctx_run(mock_st: MagicMock, builder: StreamlitBuilder) -> None:
    '''
    Verify run with pages dict calls page_ctx.run().

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    '''

    # Mock load_interface.
    mock_app = MagicMock()
    builder.load_interface = MagicMock(return_value=mock_app)

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Run with pages.
    builder.run('test_interface', pages={'/home': StubView})

    # Assert load_interface was called.
    builder.load_interface.assert_called_once_with('test_interface')

    # Assert navigation ran.
    mock_nav.run.assert_called_once()


# ** test: run_with_page_configs_calls_page_ctx_run
@patch('tiferet_streamlit.contexts.page.st')
def test_run_with_page_configs_calls_page_ctx_run(mock_st: MagicMock, builder: StreamlitBuilder) -> None:
    '''
    Verify run with page_configs list calls page_ctx.run().

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    '''

    # Mock load_interface.
    mock_app = MagicMock()
    builder.load_interface = MagicMock(return_value=mock_app)

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Create page config.
    page_config = Page(
        route='/home',
        title='Home',
        view_module_path='tiferet_streamlit.builders.tests.test_main',
        view_class_name='StubView',
    )

    # Run with page_configs.
    builder.run('test_interface', page_configs=[page_config])

    # Assert navigation ran.
    mock_nav.run.assert_called_once()


# ** test: run_no_pages_raises_error
def test_run_no_pages_raises_error(builder: StreamlitBuilder) -> None:
    '''
    Verify TiferetError is raised when no pages provided.

    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    '''

    # Mock load_interface.
    builder.load_interface = MagicMock(return_value=MagicMock())

    # Assert TiferetError with PAGE_NOT_FOUND_ID is raised.
    with pytest.raises(TiferetError) as exc_info:
        builder.run('test_interface')

    assert exc_info.value.error_code == PAGE_NOT_FOUND_ID


# ** test: run_page_configs_take_precedence
@patch('tiferet_streamlit.contexts.page.st')
def test_run_page_configs_take_precedence(mock_st: MagicMock, builder: StreamlitBuilder) -> None:
    '''
    Verify page_configs preferred over pages when both given.

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    :param builder: The builder instance.
    :type builder: StreamlitBuilder
    '''

    # Mock load_interface.
    mock_app = MagicMock()
    builder.load_interface = MagicMock(return_value=mock_app)

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav
    mock_st.Page.return_value = 'page_obj'

    # Create page config with a distinct title.
    page_config = Page(
        route='/config',
        title='Config Page',
        view_module_path='tiferet_streamlit.builders.tests.test_main',
        view_class_name='StubView',
    )

    # Run with both pages and page_configs.
    builder.run(
        'test_interface',
        pages={'/dict': StubView},
        page_configs=[page_config],
    )

    # Assert st.Page was called with the config route, not the dict route.
    mock_st.Page.assert_called_once()
    call_kwargs = mock_st.Page.call_args[1]
    assert call_kwargs['url_path'] == '/config'
    assert call_kwargs['title'] == 'Config Page'
