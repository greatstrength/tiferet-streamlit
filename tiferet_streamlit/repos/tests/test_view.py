'''Tiferet Streamlit – View YAML Repository Tests'''

# *** imports

# ** core
from pathlib import Path

# ** infra
import pytest

# ** app
from tiferet_streamlit.domain.view import Page
from tiferet_streamlit.repos.view import ViewYamlRepository

# *** fixtures

# ** fixture: sample_view_config
@pytest.fixture
def sample_view_config(tmp_path: Path) -> Path:
    '''
    Two-page view configuration written to a temporary YAML file.

    :param tmp_path: Pytest temporary directory.
    :type tmp_path: Path
    :return: Path to the temporary YAML file.
    :rtype: Path
    '''

    # Write a real YAML file. Do not mock the loader.
    config = tmp_path / 'views.yaml'
    config.write_text(
        'pages:\n'
        '  - route: /home\n'
        '    title: Home\n'
        '    icon: null\n'
        '    layout: centered\n'
        '    view_module_path: app.views.home\n'
        '    view_class_name: HomeView\n'
        '  - route: /about\n'
        '    title: About\n'
        '    view_module_path: app.views.about\n'
        '    view_class_name: AboutView\n',
        encoding='utf-8',
    )
    return config

# ** fixture: view_repo
@pytest.fixture
def view_repo(sample_view_config: Path) -> ViewYamlRepository:
    '''
    ViewYamlRepository bound to the two-page configuration.

    :param sample_view_config: Path to the temporary YAML file.
    :type sample_view_config: Path
    :return: A repository reading that file.
    :rtype: ViewYamlRepository
    '''

    return ViewYamlRepository(view_config=str(sample_view_config))

# *** tests

# ** test: list_pages_returns_page_objects
def test_list_pages_returns_page_objects(view_repo: ViewYamlRepository) -> None:
    '''
    Verify two entries come back as Page instances.

    :param view_repo: Repository bound to the two-page file.
    :type view_repo: ViewYamlRepository
    '''

    # The write role is fixed even though this repository does not write.
    assert view_repo.default_role == 'to_data.yaml'

    # List the configured pages.
    pages = view_repo.list_pages()

    # Assert both entries are Page objects with the expected identity fields.
    assert len(pages) == 2
    assert isinstance(pages[0], Page)
    assert pages[0].route == '/home'
    assert pages[0].title == 'Home'
    assert pages[0].view_class_name == 'HomeView'
    assert isinstance(pages[1], Page)
    assert pages[1].route == '/about'
    assert pages[1].title == 'About'
    assert pages[1].view_class_name == 'AboutView'

# ** test: get_page_returns_match
def test_get_page_returns_match(view_repo: ViewYamlRepository) -> None:
    '''
    Verify the requested route returns that page.

    :param view_repo: Repository bound to the two-page file.
    :type view_repo: ViewYamlRepository
    '''

    # Request the second route so a first-entry shortcut cannot pass.
    page = view_repo.get_page('/about')

    # Assert the matching page is returned.
    assert isinstance(page, Page)
    assert page.route == '/about'
    assert page.title == 'About'
    assert page.view_class_name == 'AboutView'

# ** test: get_page_unknown_route_returns_none
def test_get_page_unknown_route_returns_none(view_repo: ViewYamlRepository) -> None:
    '''
    Verify a missing route returns None and does not raise.

    :param view_repo: Repository bound to the two-page file.
    :type view_repo: ViewYamlRepository
    '''

    # Request a route that is not in the file.
    page = view_repo.get_page('/missing')

    # Assert the miss is empty rather than an error.
    assert page is None

# ** test: missing_pages_key_lists_empty
def test_missing_pages_key_lists_empty(tmp_path: Path) -> None:
    '''
    Verify a document with no pages key lists no pages.

    :param tmp_path: Pytest temporary directory.
    :type tmp_path: Path
    '''

    # Write a real YAML document that has no pages key.
    config = tmp_path / 'views.yaml'
    config.write_text('name: demo\n', encoding='utf-8')

    # List pages from that file.
    pages = ViewYamlRepository(view_config=str(config)).list_pages()

    # Assert the absent key yields an empty list.
    assert pages == []
