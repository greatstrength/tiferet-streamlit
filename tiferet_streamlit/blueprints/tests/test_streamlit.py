'''Tiferet Streamlit – Streamlit Blueprint Tests'''

# *** imports

# ** core
from pathlib import Path

# ** infra
import pytest
import toml
from unittest.mock import MagicMock, patch
from tiferet.contexts.app import AppSessionContext

# ** app
from tiferet import TiferetError
from tiferet_streamlit.assets.constants import (
    INCOMPATIBLE_APP_CONTEXT_ID,
    PAGE_NOT_FOUND_ID,
)
from tiferet_streamlit.contexts.session import SessionCacheContext
from tiferet_streamlit.contexts.view import ViewContext
from tiferet_streamlit.contexts.page import PageContext
from tiferet_streamlit.domain.theme import Theme
from tiferet_streamlit.domain.view import Page
from tiferet_streamlit.blueprints.streamlit import (
    create_view,
    build_pages,
    build_pages_from_config,
    build_streamlit_app,
    is_app_context_compatible,
    apply_theme_config,
    inject_theme_css,
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
    AppSessionContext double exposing run, used as the view app.

    :return: A mocked AppSessionContext.
    :rtype: MagicMock
    '''

    # Create an app-session double that exposes run.
    return MagicMock(spec=AppSessionContext)

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
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_with_pages(
        mock_build_app: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify build_streamlit_app with pages dict calls page_ctx.run().

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure the app returned by build_app.
    mock_app = MagicMock()
    mock_build_app.return_value = mock_app

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Run with pages.
    build_streamlit_app('test_interface', pages={'/home': StubView})

    # Assert build_app was called once.
    mock_build_app.assert_called_once_with('test_interface')

    # Assert navigation ran.
    mock_nav.run.assert_called_once()

# ** test: build_streamlit_app_with_page_configs
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_with_page_configs(
        mock_build_app: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify build_streamlit_app with page_configs list calls page_ctx.run().

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure the app returned by build_app.
    mock_build_app.return_value = MagicMock()

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

# ** test: build_streamlit_app_with_get_page_configs
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_with_get_page_configs(
        mock_build_app: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify omitted pages and page_configs invoke the callable once with the app.

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure the app returned by build_app.
    mock_app = MagicMock()
    mock_build_app.return_value = mock_app

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav
    mock_st.Page.return_value = 'page_obj'

    # Return one page from the injected callable.
    page_config = Page(
        route='/callable',
        title='Callable Page',
        view_module_path='tiferet_streamlit.blueprints.tests.test_streamlit',
        view_class_name='StubView',
    )
    get_page_configs = MagicMock(return_value=[page_config])

    # Run with only the callable.
    build_streamlit_app(
        'test_interface',
        get_page_configs=get_page_configs,
    )

    # Assert the callable received the built app once.
    get_page_configs.assert_called_once_with(mock_app)

    # Assert the returned list was registered.
    mock_st.Page.assert_called_once()
    call_kwargs = mock_st.Page.call_args[1]
    assert call_kwargs['url_path'] == '/callable'
    assert call_kwargs['title'] == 'Callable Page'

# ** test: build_streamlit_app_page_configs_take_precedence_over_get_page_configs
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_page_configs_take_precedence_over_get_page_configs(
        mock_build_app: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify a non-None page_configs list wins and the callable is not called.

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure the app returned by build_app.
    mock_build_app.return_value = MagicMock()

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav
    mock_st.Page.return_value = 'page_obj'

    # Create a page config distinct from anything the callable might return.
    page_config = Page(
        route='/config',
        title='Config Page',
        view_module_path='tiferet_streamlit.blueprints.tests.test_streamlit',
        view_class_name='StubView',
    )
    get_page_configs = MagicMock()

    # Run with both a list and a callable.
    build_streamlit_app(
        'test_interface',
        page_configs=[page_config],
        get_page_configs=get_page_configs,
    )

    # Assert the callable was skipped and the list was registered.
    get_page_configs.assert_not_called()
    mock_st.Page.assert_called_once()
    call_kwargs = mock_st.Page.call_args[1]
    assert call_kwargs['url_path'] == '/config'
    assert call_kwargs['title'] == 'Config Page'

# ** test: build_streamlit_app_pages_take_precedence_over_get_page_configs
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_pages_take_precedence_over_get_page_configs(
        mock_build_app: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify a non-None pages dict wins and the callable is not called.

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure the app returned by build_app.
    mock_build_app.return_value = MagicMock()

    # Set up st mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav
    mock_st.Page.return_value = 'page_obj'

    # Provide a callable that must not be invoked.
    get_page_configs = MagicMock()

    # Run with a pages dict and a callable.
    build_streamlit_app(
        'test_interface',
        pages={'/dict': StubView},
        get_page_configs=get_page_configs,
    )

    # Assert the callable was skipped and the dict route was registered.
    get_page_configs.assert_not_called()
    mock_st.Page.assert_called_once()
    call_kwargs = mock_st.Page.call_args[1]
    assert call_kwargs['url_path'] == '/dict'

# ** test: build_streamlit_app_no_pages_raises_error
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_no_pages_raises_error(
        mock_build_app: MagicMock,
    ) -> None:
    '''
    Verify TiferetError is raised when pages, page_configs, and get_page_configs are omitted.

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    '''

    # Configure a compatible app so the missing-pages path is reached.
    mock_build_app.return_value = MagicMock()

    # Assert TiferetError with PAGE_NOT_FOUND_ID is raised.
    with pytest.raises(TiferetError) as exc_info:
        build_streamlit_app('test_interface')

    assert exc_info.value.error_code == PAGE_NOT_FOUND_ID

# ** test: build_streamlit_app_page_configs_take_precedence
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_page_configs_take_precedence(
        mock_build_app: MagicMock,
        mock_st: MagicMock,
    ) -> None:
    '''
    Verify page_configs preferred over pages when both given.

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Configure the app returned by build_app.
    mock_build_app.return_value = MagicMock()

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

# ** test: build_streamlit_app_raises_on_incompatible_app_context
@patch('tiferet_streamlit.blueprints.streamlit.build_pages_from_config')
@patch('tiferet_streamlit.blueprints.streamlit.build_pages')
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_raises_on_incompatible_app_context(
        mock_build_app: MagicMock,
        mock_build_pages: MagicMock,
        mock_build_pages_from_config: MagicMock,
    ) -> None:
    '''
    Verify an incompatible app raises before any page is built.

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_build_pages: The mocked build_pages function.
    :type mock_build_pages: MagicMock
    :param mock_build_pages_from_config: The mocked build_pages_from_config function.
    :type mock_build_pages_from_config: MagicMock
    '''

    # Return an app with no run method.
    mock_build_app.return_value = object()

    # Assert the incompatible-app error is raised.
    with pytest.raises(TiferetError) as exc_info:
        build_streamlit_app('test_interface', pages={'/home': StubView})

    assert exc_info.value.error_code == INCOMPATIBLE_APP_CONTEXT_ID

    # Assert no pages were built.
    mock_build_pages.assert_not_called()
    mock_build_pages_from_config.assert_not_called()

# *** tests: is_app_context_compatible

# ** test: is_app_context_compatible_accepts_matching_run
def test_is_app_context_compatible_accepts_matching_run() -> None:
    '''
    Verify a run method that accepts (feature_id, headers, data) is compatible.
    '''

    # Build an app whose run method matches the required call shape.
    class CompatibleApp(object):
        def run(self, feature_id, headers, data):
            return None

    # Assert the call shape is accepted.
    assert is_app_context_compatible(CompatibleApp()) is True

# ** test: is_app_context_compatible_rejects_missing_run
def test_is_app_context_compatible_rejects_missing_run() -> None:
    '''
    Verify an object with no run method is incompatible.
    '''

    # Assert a bare object is rejected.
    assert is_app_context_compatible(object()) is False

# ** test: is_app_context_compatible_rejects_wrong_shaped_run
def test_is_app_context_compatible_rejects_wrong_shaped_run() -> None:
    '''
    Verify a run method that cannot bind the required call shape is incompatible.
    '''

    # Build an app whose run method cannot accept headers and data.
    class WrongShapedApp(object):
        def run(self, feature_id):
            return None

    # Assert the call shape is rejected.
    assert is_app_context_compatible(WrongShapedApp()) is False

# *** tests: apply_theme_config

# ** test: apply_theme_config_writes_native_fields
def test_apply_theme_config_writes_native_fields(tmp_path: Path) -> None:
    '''
    Verify a temporary config gains theme keys from native_fields.

    :param tmp_path: Temporary directory that holds the config file.
    :type tmp_path: Path
    '''

    # Point at a config path that does not exist yet.
    config_path = tmp_path / '.streamlit' / 'config.toml'
    theme = Theme(
        base='dark',
        primary_color='#ff4b4b',
        background_color='#0e1117',
        secondary_background_color='#262730',
        text_color='#fafafa',
        font='serif',
        custom_css='h1 { color: red; }',
    )

    # Write the native fields.
    apply_theme_config(theme, config_path=str(config_path))

    # Assert the theme table matches the native fields.
    document = toml.load(str(config_path))
    assert document['theme'] == theme.native_fields

# ** test: apply_theme_config_merges_existing_content
def test_apply_theme_config_merges_existing_content(tmp_path: Path) -> None:
    '''
    Verify an existing server section survives and a theme sibling is kept.

    :param tmp_path: Temporary directory that holds the config file.
    :type tmp_path: Path
    '''

    # Seed a config with a sibling section and an existing theme key.
    config_path = tmp_path / 'config.toml'
    with config_path.open('w', encoding='utf-8') as config_file:
        toml.dump({
            'server': {
                'port': 8501,
            },
            'theme': {
                'base': 'light',
                'font': 'sans serif',
            },
        }, config_file)

    # Update one theme key and add another.
    apply_theme_config(
        Theme(
            primary_color='#ff4b4b',
            font='serif',
        ),
        config_path=str(config_path),
    )

    # Assert the server section survives and the untouched theme key remains.
    document = toml.load(str(config_path))
    assert document['server'] == {'port': 8501}
    assert document['theme']['base'] == 'light'
    assert document['theme']['font'] == 'serif'
    assert document['theme']['primaryColor'] == '#ff4b4b'

# ** test: apply_theme_config_noop_without_native_fields
def test_apply_theme_config_noop_without_native_fields(tmp_path: Path) -> None:
    '''
    Verify a CSS-only theme does not create the config file.

    :param tmp_path: Temporary directory that must stay untouched.
    :type tmp_path: Path
    '''

    # Point at a nested path that must not be created.
    config_path = tmp_path / '.streamlit' / 'config.toml'

    # Apply a theme with no native fields.
    apply_theme_config(
        Theme(custom_css='x'),
        config_path=str(config_path),
    )

    # Assert the file was not created.
    assert not config_path.exists()

# *** tests: inject_theme_css

# ** test: inject_theme_css_injects_markdown
@patch('tiferet_streamlit.blueprints.streamlit.st')
def test_inject_theme_css_injects_markdown(mock_st: MagicMock) -> None:
    '''
    Verify custom CSS is injected once as an unsafe HTML style block.

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Inject a theme that carries custom CSS.
    inject_theme_css(Theme(custom_css='h1 { color: red; }'))

    # Assert markdown was called once with the style block.
    mock_st.markdown.assert_called_once_with(
        '<style>h1 { color: red; }</style>',
        unsafe_allow_html=True,
    )

# ** test: inject_theme_css_noop_without_custom_css
@patch('tiferet_streamlit.blueprints.streamlit.st')
def test_inject_theme_css_noop_without_custom_css(mock_st: MagicMock) -> None:
    '''
    Verify markdown is not called when custom CSS is absent.

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    '''

    # Inject themes whose custom CSS is missing or empty.
    inject_theme_css(Theme())
    inject_theme_css(Theme(custom_css=''))

    # Assert markdown was not called.
    mock_st.markdown.assert_not_called()

# *** tests: build_streamlit_app theme

# ** test: build_streamlit_app_with_theme_applies_theme
@patch('tiferet_streamlit.blueprints.streamlit.inject_theme_css')
@patch('tiferet_streamlit.blueprints.streamlit.apply_theme_config')
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_with_theme_applies_theme(
        mock_build_app: MagicMock,
        mock_st: MagicMock,
        mock_apply_theme_config: MagicMock,
        mock_inject_theme_css: MagicMock,
    ) -> None:
    '''
    Verify both theme helpers run when a theme is passed.

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_st: The mocked streamlit module used by page navigation.
    :type mock_st: MagicMock
    :param mock_apply_theme_config: The mocked config writer.
    :type mock_apply_theme_config: MagicMock
    :param mock_inject_theme_css: The mocked CSS injector.
    :type mock_inject_theme_css: MagicMock
    '''

    # Record call order so theme helpers must precede app construction.
    order = []

    def _record_apply(theme):
        order.append('apply')

    def _record_inject(theme):
        order.append('inject')

    def _record_build(*args, **kwargs):
        order.append('build')
        return MagicMock()

    mock_apply_theme_config.side_effect = _record_apply
    mock_inject_theme_css.side_effect = _record_inject
    mock_build_app.side_effect = _record_build

    # Set up navigation so page_ctx.run() completes.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Build with a theme.
    theme = Theme(
        primary_color='#ff4b4b',
        custom_css='h1 { color: red; }',
    )
    build_streamlit_app(
        'test_interface',
        pages={'/home': StubView},
        theme=theme,
    )

    # Assert both helpers ran with that theme, before the app was built.
    mock_apply_theme_config.assert_called_once_with(theme)
    mock_inject_theme_css.assert_called_once_with(theme)
    assert order == ['apply', 'inject', 'build']

# ** test: build_streamlit_app_without_theme_leaves_behavior_unchanged
@patch('tiferet_streamlit.blueprints.streamlit.inject_theme_css')
@patch('tiferet_streamlit.blueprints.streamlit.apply_theme_config')
@patch('tiferet_streamlit.contexts.page.st')
@patch('tiferet_streamlit.blueprints.streamlit.build_app')
def test_build_streamlit_app_without_theme_leaves_behavior_unchanged(
        mock_build_app: MagicMock,
        mock_st: MagicMock,
        mock_apply_theme_config: MagicMock,
        mock_inject_theme_css: MagicMock,
    ) -> None:
    '''
    Verify neither theme helper runs when theme is omitted.

    :param mock_build_app: The mocked build_app function.
    :type mock_build_app: MagicMock
    :param mock_st: The mocked streamlit module used by page navigation.
    :type mock_st: MagicMock
    :param mock_apply_theme_config: The mocked config writer.
    :type mock_apply_theme_config: MagicMock
    :param mock_inject_theme_css: The mocked CSS injector.
    :type mock_inject_theme_css: MagicMock
    '''

    # Configure the app returned by build_app.
    mock_build_app.return_value = MagicMock()

    # Set up navigation so page_ctx.run() completes.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav

    # Build without a theme.
    build_streamlit_app('test_interface', pages={'/home': StubView})

    # Assert theme helpers were skipped and navigation still ran.
    mock_apply_theme_config.assert_not_called()
    mock_inject_theme_css.assert_not_called()
    mock_build_app.assert_called_once_with('test_interface')
    mock_nav.run.assert_called_once()
