'''Tiferet Streamlit – Streamlit Blueprint Tests'''

# *** imports

# ** core
import toml

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
from tiferet_streamlit.domain.theme import Theme
from tiferet_streamlit.blueprints.streamlit import (
    create_view,
    build_pages,
    build_pages_from_config,
    apply_theme_config,
    inject_theme_css,
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

# *** tests: apply_theme_config

# ** test: apply_theme_config_writes_native_fields
def test_apply_theme_config_writes_native_fields(tmp_path) -> None:
    '''
    Verify native [theme] fields are written to config.toml and can be
    read back, satisfying the RFP's read-back verification requirement.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: Path
    '''

    # Declare a theme with native fields.
    theme = Theme(primary_color='#FF4B4B', text_color='#262730')
    config_path = tmp_path / '.streamlit' / 'config.toml'

    # Apply the theme config.
    apply_theme_config(theme, config_path=str(config_path))

    # Read the file back and assert the native fields were written.
    written = toml.load(config_path)
    assert written['theme']['primaryColor'] == '#FF4B4B'
    assert written['theme']['textColor'] == '#262730'

# ** test: apply_theme_config_merges_existing_content
def test_apply_theme_config_merges_existing_content(tmp_path) -> None:
    '''
    Verify the write merges into [theme] without clobbering unrelated
    existing sections or keys.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: Path
    '''

    # Seed an existing config.toml with unrelated settings.
    config_path = tmp_path / '.streamlit' / 'config.toml'
    config_path.parent.mkdir(parents=True)
    with config_path.open('w', encoding='utf-8') as file:
        toml.dump({
            'server': {'port': 8501},
            'theme': {'font': 'monospace'},
        }, file)

    # Apply a theme that only sets a different native field.
    theme = Theme(primary_color='#FF4B4B')
    apply_theme_config(theme, config_path=str(config_path))

    # Assert unrelated settings and untouched theme keys are preserved.
    written = toml.load(config_path)
    assert written['server']['port'] == 8501
    assert written['theme']['font'] == 'monospace'
    assert written['theme']['primaryColor'] == '#FF4B4B'

# ** test: apply_theme_config_noop_without_native_fields
def test_apply_theme_config_noop_without_native_fields(tmp_path) -> None:
    '''
    Verify no file is written when the theme declares no native fields.

    :param tmp_path: Pytest temporary directory fixture.
    :type tmp_path: Path
    '''

    # Declare a theme with only custom_css set.
    theme = Theme(custom_css='.stButton { color: red; }')
    config_path = tmp_path / '.streamlit' / 'config.toml'

    # Apply the theme config.
    apply_theme_config(theme, config_path=str(config_path))

    # Assert no file was created.
    assert not config_path.exists()

# *** tests: inject_theme_css

# ** test: inject_theme_css_injects_markdown
@patch('tiferet_streamlit.blueprints.streamlit.st')
def test_inject_theme_css_injects_markdown(mock_st: MagicMock) -> None:
    '''
    Verify custom_css is injected via st.markdown(unsafe_allow_html=True),
    asserting the exact injected markdown content.

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Declare a theme with custom CSS.
    theme = Theme(custom_css='.stButton { color: red; }')

    # Inject the CSS.
    inject_theme_css(theme)

    # Assert the markdown call and its content.
    mock_st.markdown.assert_called_once_with(
        '<style>.stButton { color: red; }</style>',
        unsafe_allow_html=True,
    )

# ** test: inject_theme_css_noop_without_custom_css
@patch('tiferet_streamlit.blueprints.streamlit.st')
def test_inject_theme_css_noop_without_custom_css(mock_st: MagicMock) -> None:
    '''
    Verify st.markdown is not called when no custom_css was declared.

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Declare a theme with no custom CSS.
    theme = Theme(primary_color='#FF4B4B')

    # Inject the CSS (a no-op in this case).
    inject_theme_css(theme)

    # Assert markdown was never called.
    mock_st.markdown.assert_not_called()

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

# ** test: build_streamlit_app_with_get_page_configs
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.realize_interface')
@patch('tiferet_streamlit.blueprints.streamlit.resolve_interface')
def test_build_streamlit_app_with_get_page_configs(
        mock_resolve: MagicMock,
        mock_realize: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify build_streamlit_app assembles pages via a get_page_configs handler.

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

    # Configure a handler standing in for a DI-resolved source (e.g. get_view_service(app).list_pages()).
    page_config = Page(
        route='/service',
        title='Service Page',
        view_module_path='tiferet_streamlit.blueprints.tests.test_streamlit',
        view_class_name='StubView',
    )
    mock_get_page_configs = MagicMock(return_value=[page_config])

    # Run with only a get_page_configs handler.
    build_streamlit_app('test_interface', get_page_configs=mock_get_page_configs)

    # Assert the handler was invoked with the realized app and navigation ran.
    mock_get_page_configs.assert_called_once_with(mock_app)
    mock_nav.run.assert_called_once()

# ** test: build_streamlit_app_page_configs_take_precedence_over_get_page_configs
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.realize_interface')
@patch('tiferet_streamlit.blueprints.streamlit.resolve_interface')
def test_build_streamlit_app_page_configs_take_precedence_over_get_page_configs(
        mock_resolve: MagicMock,
        mock_realize: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify page_configs/pages precedence is unchanged when get_page_configs is also given.

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

    # Create a page config and an unused get_page_configs handler.
    page_config = Page(
        route='/config',
        title='Config Page',
        view_module_path='tiferet_streamlit.blueprints.tests.test_streamlit',
        view_class_name='StubView',
    )
    mock_get_page_configs = MagicMock()

    # Run with both page_configs and get_page_configs.
    build_streamlit_app(
        'test_interface',
        page_configs=[page_config],
        get_page_configs=mock_get_page_configs,
    )

    # Assert the handler was never consulted since page_configs took precedence.
    mock_get_page_configs.assert_not_called()
    mock_st.Page.assert_called_once()
    call_kwargs = mock_st.Page.call_args[1]
    assert call_kwargs['url_path'] == '/config'

# ** test: build_streamlit_app_with_theme_applies_theme
@patch('tiferet_streamlit.blueprints.streamlit.inject_theme_css')
@patch('tiferet_streamlit.blueprints.streamlit.apply_theme_config')
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.realize_interface')
@patch('tiferet_streamlit.blueprints.streamlit.resolve_interface')
def test_build_streamlit_app_with_theme_applies_theme(
        mock_resolve: MagicMock,
        mock_realize: MagicMock,
        mock_st: MagicMock,
        mock_apply_theme_config: MagicMock,
        mock_inject_theme_css: MagicMock,
    ) -> None:
    '''
    Verify a supplied theme is applied via both the native config path
    and the CSS injection path on every call.

    :param mock_resolve: The mocked resolve_interface function.
    :type mock_resolve: MagicMock
    :param mock_realize: The mocked realize_interface function.
    :type mock_realize: MagicMock
    :param mock_st: The mocked streamlit module used by PageContext.
    :type mock_st: MagicMock
    :param mock_apply_theme_config: The mocked apply_theme_config function.
    :type mock_apply_theme_config: MagicMock
    :param mock_inject_theme_css: The mocked inject_theme_css function.
    :type mock_inject_theme_css: MagicMock
    '''

    # Configure mocks.
    mock_app_interface = MagicMock()
    mock_app = MagicMock()
    mock_resolve.return_value = (mock_app_interface, [])
    mock_realize.return_value = mock_app
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Run with a declared theme.
    theme = Theme(primary_color='#FF4B4B', custom_css='.stButton { color: red; }')
    build_streamlit_app('test_interface', pages={'/home': StubView}, theme=theme)

    # Assert both theme application paths were invoked with the theme.
    mock_apply_theme_config.assert_called_once_with(theme)
    mock_inject_theme_css.assert_called_once_with(theme)

# ** test: build_streamlit_app_without_theme_leaves_behavior_unchanged
@patch('tiferet_streamlit.blueprints.streamlit.inject_theme_css')
@patch('tiferet_streamlit.blueprints.streamlit.apply_theme_config')
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.realize_interface')
@patch('tiferet_streamlit.blueprints.streamlit.resolve_interface')
def test_build_streamlit_app_without_theme_leaves_behavior_unchanged(
        mock_resolve: MagicMock,
        mock_realize: MagicMock,
        mock_st: MagicMock,
        mock_apply_theme_config: MagicMock,
        mock_inject_theme_css: MagicMock,
    ) -> None:
    '''
    Verify omitting theme entirely results in no config write and no
    CSS injection, i.e. existing behavior is unchanged.

    :param mock_resolve: The mocked resolve_interface function.
    :type mock_resolve: MagicMock
    :param mock_realize: The mocked realize_interface function.
    :type mock_realize: MagicMock
    :param mock_st: The mocked streamlit module used by PageContext.
    :type mock_st: MagicMock
    :param mock_apply_theme_config: The mocked apply_theme_config function.
    :type mock_apply_theme_config: MagicMock
    :param mock_inject_theme_css: The mocked inject_theme_css function.
    :type mock_inject_theme_css: MagicMock
    '''

    # Configure mocks.
    mock_app_interface = MagicMock()
    mock_app = MagicMock()
    mock_resolve.return_value = (mock_app_interface, [])
    mock_realize.return_value = mock_app
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Run without a theme.
    build_streamlit_app('test_interface', pages={'/home': StubView})

    # Assert neither theme application path was invoked.
    mock_apply_theme_config.assert_not_called()
    mock_inject_theme_css.assert_not_called()
