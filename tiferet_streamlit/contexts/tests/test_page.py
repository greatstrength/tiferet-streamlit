'''Tiferet Streamlit – Page Context Tests'''

# *** imports

# ** infra
import pytest
from unittest.mock import MagicMock, patch, call

# ** app
from tiferet_streamlit.contexts.view import ViewContext
from tiferet_streamlit.contexts.page import PageContext

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

# ** fixture: mock_app
@pytest.fixture
def mock_app() -> MagicMock:
    '''
    MagicMock standing in for AppInterfaceContext.

    :return: A mocked app context.
    :rtype: MagicMock
    '''
    return MagicMock()


# ** fixture: page_context
@pytest.fixture
def page_context() -> PageContext:
    '''
    Empty PageContext instance.

    :return: A PageContext with no registered pages.
    :rtype: PageContext
    '''
    return PageContext()


# *** tests

# ** test: empty_pages_by_default
def test_empty_pages_by_default(page_context: PageContext) -> None:
    '''
    Verify pages dict starts empty.

    :param page_context: The page context instance.
    :type page_context: PageContext
    '''

    # Assert the pages dict is empty.
    assert page_context.pages == {}


# ** test: register_page_stores_view
def test_register_page_stores_view(page_context: PageContext, mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify view is stored under route key.

    :param page_context: The page context instance.
    :type page_context: PageContext
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a stub view and register it.
    view = StubView(app=mock_app, key='home')
    page_context.register_page('/home', view)

    # Assert the view is stored.
    assert page_context.pages['/home']['view'] is view


# ** test: register_page_default_title
def test_register_page_default_title(page_context: PageContext, mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify title defaults to route.

    :param page_context: The page context instance.
    :type page_context: PageContext
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Register a page without a title.
    view = StubView(app=mock_app, key='about')
    page_context.register_page('/about', view)

    # Assert the title defaults to the route.
    assert page_context.pages['/about']['title'] == '/about'


# ** test: register_page_custom_title
def test_register_page_custom_title(page_context: PageContext, mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify custom title is stored.

    :param page_context: The page context instance.
    :type page_context: PageContext
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Register a page with a custom title.
    view = StubView(app=mock_app, key='home')
    page_context.register_page('/home', view, title='Home Page')

    # Assert the custom title is stored.
    assert page_context.pages['/home']['title'] == 'Home Page'


# ** test: register_page_icon
def test_register_page_icon(page_context: PageContext, mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify icon is stored.

    :param page_context: The page context instance.
    :type page_context: PageContext
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Register a page with an icon.
    view = StubView(app=mock_app, key='home')
    page_context.register_page('/home', view, icon='🏠')

    # Assert the icon is stored.
    assert page_context.pages['/home']['icon'] == '🏠'


# ** test: register_page_default_icon_none
def test_register_page_default_icon_none(page_context: PageContext, mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify icon defaults to None.

    :param page_context: The page context instance.
    :type page_context: PageContext
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Register a page without an icon.
    view = StubView(app=mock_app, key='home')
    page_context.register_page('/home', view)

    # Assert the icon defaults to None.
    assert page_context.pages['/home']['icon'] is None


# ** test: register_multiple_pages
def test_register_multiple_pages(page_context: PageContext, mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify multiple pages can be registered.

    :param page_context: The page context instance.
    :type page_context: PageContext
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Register multiple pages.
    view_a = StubView(app=mock_app, key='a')
    view_b = StubView(app=mock_app, key='b')
    page_context.register_page('/a', view_a)
    page_context.register_page('/b', view_b)

    # Assert both pages are registered.
    assert len(page_context.pages) == 2
    assert '/a' in page_context.pages
    assert '/b' in page_context.pages


# ** test: register_page_overwrites_existing
def test_register_page_overwrites_existing(page_context: PageContext, mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify re-registering a route overwrites.

    :param page_context: The page context instance.
    :type page_context: PageContext
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Register a page, then overwrite it.
    view1 = StubView(app=mock_app, key='v1')
    view2 = StubView(app=mock_app, key='v2')
    page_context.register_page('/home', view1, title='Old')
    page_context.register_page('/home', view2, title='New')

    # Assert the overwritten values.
    assert page_context.pages['/home']['view'] is view2
    assert page_context.pages['/home']['title'] == 'New'


# ** test: run_calls_st_navigation
@patch('tiferet_streamlit.contexts.page.st')
def test_run_calls_st_navigation(mock_st: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify st.Page, st.navigation, and nav.run() are called correctly.

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Set up mock navigation.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav
    mock_st.Page.return_value = 'page_obj'

    # Create a page context with a registered page.
    ctx = PageContext()
    view = MagicMock()
    ctx.register_page('/home', view, title='Home')

    # Run the page context.
    ctx.run()

    # Assert st.Page was called correctly.
    mock_st.Page.assert_called_once_with(
        page=view,
        title='Home',
        url_path='/home',
    )

    # Assert st.navigation was called with the page list.
    mock_st.navigation.assert_called_once_with(['page_obj'])

    # Assert nav.run() was called.
    mock_nav.run.assert_called_once()


# ** test: run_with_icon
@patch('tiferet_streamlit.contexts.page.st')
def test_run_with_icon(mock_st: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify icon kwarg is included in st.Page.

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Set up mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav
    mock_st.Page.return_value = 'page_obj'

    # Register a page with icon.
    ctx = PageContext()
    view = MagicMock()
    ctx.register_page('/home', view, title='Home', icon='🏠')

    # Run.
    ctx.run()

    # Assert st.Page was called with icon.
    mock_st.Page.assert_called_once_with(
        page=view,
        title='Home',
        url_path='/home',
        icon='🏠',
    )


# ** test: run_multiple_pages_order
@patch('tiferet_streamlit.contexts.page.st')
def test_run_multiple_pages_order(mock_st: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify st.Page is called for each registered page.

    :param mock_st: The mocked streamlit module.
    :type mock_st: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Set up mocks.
    mock_nav = MagicMock()
    mock_st.navigation.return_value = mock_nav
    mock_st.Page.side_effect = lambda **kw: f"page_{kw['url_path']}"

    # Register multiple pages.
    ctx = PageContext()
    ctx.register_page('/a', MagicMock(), title='A')
    ctx.register_page('/b', MagicMock(), title='B')

    # Run.
    ctx.run()

    # Assert st.Page was called twice.
    assert mock_st.Page.call_count == 2

    # Assert navigation received both page objects.
    mock_st.navigation.assert_called_once_with(['page_/a', 'page_/b'])
