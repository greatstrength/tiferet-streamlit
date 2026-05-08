"""Tiferet Streamlit Builder Tests"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest

# ** app
from tiferet import TiferetError
from ...contexts.session import SessionCacheContext
from ...contexts.view import ViewContext
from ...contexts.page import PageContext
from ...domain.view import Page
from ..main import StreamlitBuilder

# *** helpers

# ** helper: stub_view
class StubView(ViewContext):
    '''
    A minimal ViewContext subclass for builder tests.
    '''

    def render(self):
        pass


# *** fixtures

# ** fixture: mock_session_state
@pytest.fixture(autouse=True)
def mock_session_state():
    '''
    Replace st.session_state with a plain dict for all builder tests.
    '''

    state = {}
    with mock.patch('streamlit.session_state', state):
        yield state


# ** fixture: mock_app_interface
@pytest.fixture
def mock_app_interface():
    '''
    A mock AppInterfaceContext.
    '''
    return mock.MagicMock()


# ** fixture: builder
@pytest.fixture
def builder():
    '''
    A StreamlitBuilder instance.
    '''
    return StreamlitBuilder()


# *** tests — create_view

# ** test: create_view_returns_instance
def test_create_view_returns_instance(builder: StreamlitBuilder, mock_app_interface) -> None:
    '''
    Test that create_view returns a ViewContext instance.
    '''

    view = builder.create_view(StubView, mock_app_interface, key='test')

    assert isinstance(view, StubView)
    assert view.app is mock_app_interface
    assert view.key == 'test'


# ** test: create_view_auto_namespace
def test_create_view_auto_namespace(builder: StreamlitBuilder, mock_app_interface) -> None:
    '''
    Test that create_view creates a session with the key as namespace.
    '''

    view = builder.create_view(StubView, mock_app_interface, key='my_view')

    assert view.session.namespace == 'my_view'


# ** test: create_view_custom_session
def test_create_view_custom_session(builder: StreamlitBuilder, mock_app_interface) -> None:
    '''
    Test that create_view uses a provided session.
    '''

    custom = SessionCacheContext(namespace='custom')
    view = builder.create_view(StubView, mock_app_interface, key='v', session=custom)

    assert view.session is custom


# *** tests — build_pages

# ** test: build_pages_returns_page_context
def test_build_pages_returns_page_context(builder: StreamlitBuilder, mock_app_interface) -> None:
    '''
    Test that build_pages returns a PageContext with registered pages.
    '''

    pages = {'home': StubView, 'calc': StubView}
    page_ctx = builder.build_pages(mock_app_interface, pages)

    assert isinstance(page_ctx, PageContext)
    assert 'home' in page_ctx.pages
    assert 'calc' in page_ctx.pages


# ** test: build_pages_view_keys_match_routes
def test_build_pages_view_keys_match_routes(builder: StreamlitBuilder, mock_app_interface) -> None:
    '''
    Test that each view's key matches its route.
    '''

    pages = {'home': StubView, 'settings': StubView}
    page_ctx = builder.build_pages(mock_app_interface, pages)

    for route, page_info in page_ctx.pages.items():
        assert page_info['view'].key == route


# *** tests — build_pages_from_config

# ** test: build_pages_from_config_returns_page_context
def test_build_pages_from_config_returns_page_context(builder: StreamlitBuilder, mock_app_interface) -> None:
    '''
    Test that build_pages_from_config returns a PageContext from Page domain objects.
    '''

    page_configs = [
        Page(
            route='home',
            title='Home',
            view_module_path='tiferet_streamlit.builders.tests.test_main',
            view_class_name='StubView',
        ),
        Page(
            route='settings',
            title='Settings',
            icon=':gear:',
            view_module_path='tiferet_streamlit.builders.tests.test_main',
            view_class_name='StubView',
        ),
    ]

    page_ctx = builder.build_pages_from_config(mock_app_interface, page_configs)

    assert isinstance(page_ctx, PageContext)
    assert 'home' in page_ctx.pages
    assert 'settings' in page_ctx.pages
    assert page_ctx.pages['home']['title'] == 'Home'
    assert page_ctx.pages['settings']['icon'] == ':gear:'


# *** tests — run

# ** test: run_with_pages_calls_page_ctx_run
def test_run_with_pages_calls_page_ctx_run(builder: StreamlitBuilder) -> None:
    '''
    Test that run() with pages dict builds pages and calls PageContext.run().
    '''

    with mock.patch.object(builder, 'load_interface') as mock_load, \
         mock.patch.object(PageContext, 'run') as mock_run:

        mock_load.return_value = mock.MagicMock()

        builder.run('test_interface', pages={'home': StubView})

        mock_load.assert_called_once_with('test_interface')
        mock_run.assert_called_once()


# ** test: run_with_page_configs_calls_page_ctx_run
def test_run_with_page_configs_calls_page_ctx_run(builder: StreamlitBuilder) -> None:
    '''
    Test that run() with page_configs builds pages and calls PageContext.run().
    '''

    page_configs = [
        Page(
            route='home',
            title='Home',
            view_module_path='tiferet_streamlit.builders.tests.test_main',
            view_class_name='StubView',
        ),
    ]

    with mock.patch.object(builder, 'load_interface') as mock_load, \
         mock.patch.object(PageContext, 'run') as mock_run:

        mock_load.return_value = mock.MagicMock()

        builder.run('test_interface', page_configs=page_configs)

        mock_load.assert_called_once_with('test_interface')
        mock_run.assert_called_once()


# ** test: run_no_pages_raises_error
def test_run_no_pages_raises_error(builder: StreamlitBuilder) -> None:
    '''
    Test that run() raises TiferetError when neither pages nor page_configs is provided.
    '''

    with mock.patch.object(builder, 'load_interface') as mock_load:
        mock_load.return_value = mock.MagicMock()

        with pytest.raises(TiferetError):
            builder.run('test_interface')


# ** test: run_page_configs_take_precedence
def test_run_page_configs_take_precedence(builder: StreamlitBuilder) -> None:
    '''
    Test that page_configs takes precedence over pages when both are provided.
    '''

    page_configs = [
        Page(
            route='config_home',
            title='Config Home',
            view_module_path='tiferet_streamlit.builders.tests.test_main',
            view_class_name='StubView',
        ),
    ]

    with mock.patch.object(builder, 'load_interface') as mock_load, \
         mock.patch.object(builder, 'build_pages_from_config', wraps=builder.build_pages_from_config) as mock_from_config, \
         mock.patch.object(builder, 'build_pages') as mock_build, \
         mock.patch.object(PageContext, 'run'):

        mock_load.return_value = mock.MagicMock()

        builder.run('test_interface', pages={'home': StubView}, page_configs=page_configs)

        # build_pages_from_config should be called, not build_pages.
        mock_from_config.assert_called_once()
        mock_build.assert_not_called()
