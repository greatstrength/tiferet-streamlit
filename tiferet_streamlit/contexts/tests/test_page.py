"""Tiferet Streamlit Page Context Tests"""

# *** imports

# ** core
from unittest import mock

# ** infra
import pytest

# ** app
from ..view import ViewContext
from ..page import PageContext

# *** helpers

# ** helper: stub_view
class StubView(ViewContext):
    '''
    A minimal ViewContext subclass for page tests.
    '''

    def render(self):
        pass


# *** fixtures

# ** fixture: mock_app
@pytest.fixture
def mock_app():
    '''
    A mock AppInterfaceContext.
    '''
    return mock.MagicMock()


# ** fixture: page_context
@pytest.fixture
def page_context() -> PageContext:
    '''
    An empty PageContext instance.
    '''
    return PageContext()


# *** tests

# ** test: empty_pages_by_default
def test_empty_pages_by_default(page_context: PageContext) -> None:
    '''
    Test that PageContext starts with an empty pages dict.
    '''

    assert page_context.pages == {}


# ** test: register_page_stores_view
def test_register_page_stores_view(page_context: PageContext, mock_app) -> None:
    '''
    Test that register_page stores the view under the route key.
    '''

    view = StubView(app=mock_app, key='home')
    page_context.register_page('home', view)

    assert 'home' in page_context.pages
    assert page_context.pages['home']['view'] is view


# ** test: register_page_default_title
def test_register_page_default_title(page_context: PageContext, mock_app) -> None:
    '''
    Test that title defaults to the route when not specified.
    '''

    view = StubView(app=mock_app, key='about')
    page_context.register_page('about', view)

    assert page_context.pages['about']['title'] == 'about'


# ** test: register_page_custom_title
def test_register_page_custom_title(page_context: PageContext, mock_app) -> None:
    '''
    Test that a custom title is stored correctly.
    '''

    view = StubView(app=mock_app, key='home')
    page_context.register_page('home', view, title='Home Page')

    assert page_context.pages['home']['title'] == 'Home Page'


# ** test: register_page_icon
def test_register_page_icon(page_context: PageContext, mock_app) -> None:
    '''
    Test that an icon is stored correctly.
    '''

    view = StubView(app=mock_app, key='settings')
    page_context.register_page('settings', view, icon=':gear:')

    assert page_context.pages['settings']['icon'] == ':gear:'


# ** test: register_page_default_icon_none
def test_register_page_default_icon_none(page_context: PageContext, mock_app) -> None:
    '''
    Test that icon defaults to None.
    '''

    view = StubView(app=mock_app, key='home')
    page_context.register_page('home', view)

    assert page_context.pages['home']['icon'] is None


# ** test: register_multiple_pages
def test_register_multiple_pages(page_context: PageContext, mock_app) -> None:
    '''
    Test that multiple pages can be registered.
    '''

    view_home = StubView(app=mock_app, key='home')
    view_calc = StubView(app=mock_app, key='calculator')
    page_context.register_page('home', view_home)
    page_context.register_page('calculator', view_calc)

    assert len(page_context.pages) == 2
    assert 'home' in page_context.pages
    assert 'calculator' in page_context.pages


# ** test: register_page_overwrites_existing
def test_register_page_overwrites_existing(page_context: PageContext, mock_app) -> None:
    '''
    Test that registering a page with an existing route overwrites it.
    '''

    view1 = StubView(app=mock_app, key='home')
    view2 = StubView(app=mock_app, key='home_v2')

    page_context.register_page('home', view1, title='Old Home')
    page_context.register_page('home', view2, title='New Home')

    assert page_context.pages['home']['view'] is view2
    assert page_context.pages['home']['title'] == 'New Home'


# ** test: run_calls_st_navigation
def test_run_calls_st_navigation(page_context: PageContext, mock_app) -> None:
    '''
    Test that run() builds st.Page objects and calls st.navigation().run().
    '''

    view = StubView(app=mock_app, key='home')
    page_context.register_page('home', view, title='Home')

    with mock.patch('streamlit.Page') as mock_page, \
         mock.patch('streamlit.navigation') as mock_nav:

        mock_nav_instance = mock.MagicMock()
        mock_nav.return_value = mock_nav_instance

        page_context.run()

        # st.Page should have been called once for the one registered page.
        mock_page.assert_called_once_with(
            page=view,
            title='Home',
            url_path='home',
        )

        # st.navigation should have been called with the page list.
        mock_nav.assert_called_once()

        # nav.run() should have been called.
        mock_nav_instance.run.assert_called_once()


# ** test: run_with_icon
def test_run_with_icon(page_context: PageContext, mock_app) -> None:
    '''
    Test that run() includes the icon kwarg when set.
    '''

    view = StubView(app=mock_app, key='settings')
    page_context.register_page('settings', view, title='Settings', icon=':gear:')

    with mock.patch('streamlit.Page') as mock_page, \
         mock.patch('streamlit.navigation') as mock_nav:

        mock_nav.return_value = mock.MagicMock()

        page_context.run()

        mock_page.assert_called_once_with(
            page=view,
            title='Settings',
            url_path='settings',
            icon=':gear:',
        )


# ** test: run_multiple_pages_order
def test_run_multiple_pages_order(page_context: PageContext, mock_app) -> None:
    '''
    Test that run() creates st.Page for each registered page.
    '''

    for route in ['home', 'calculator', 'settings']:
        view = StubView(app=mock_app, key=route)
        page_context.register_page(route, view, title=route.title())

    with mock.patch('streamlit.Page') as mock_page, \
         mock.patch('streamlit.navigation') as mock_nav:

        mock_nav.return_value = mock.MagicMock()

        page_context.run()

        assert mock_page.call_count == 3
