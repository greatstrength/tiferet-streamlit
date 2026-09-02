'''Tiferet Streamlit – View YAML Repository Tests'''

# *** imports

# ** core
from pathlib import Path

# ** infra
import pytest
import yaml

# ** app
from tiferet_streamlit.domain.view import Page
from tiferet_streamlit.repos.view import ViewYamlRepository

# *** constants

# ** constant: sample_pages_data
SAMPLE_PAGES_DATA = [
    dict(
        route='/home',
        title='Home',
        icon='🏠',
        layout='wide',
        view_module_path='tiferet_streamlit.domain.view',
        view_class_name='Page',
    ),
    dict(
        route='/about',
        title='About',
        view_module_path='tiferet_streamlit.domain.view',
        view_class_name='Page',
    ),
]

# *** fixtures

# ** fixture: view_yaml_file
@pytest.fixture
def view_yaml_file(tmp_path: Path) -> Path:
    '''
    Write SAMPLE_PAGES_DATA to a temporary YAML file under a "pages" key.

    :param tmp_path: The pytest temporary directory fixture.
    :type tmp_path: Path
    :return: The path to the written YAML configuration file.
    :rtype: Path
    '''

    # Write the sample pages data to a temporary YAML file.
    config_file = tmp_path / 'view.yml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(dict(pages=SAMPLE_PAGES_DATA), f)

    # Return the path to the file.
    return config_file


# ** fixture: repository
@pytest.fixture
def repository(view_yaml_file: Path) -> ViewYamlRepository:
    '''
    A ViewYamlRepository configured against the temporary YAML file.

    :param view_yaml_file: The temporary YAML configuration file.
    :type view_yaml_file: Path
    :return: The configured repository.
    :rtype: ViewYamlRepository
    '''

    return ViewYamlRepository(view_yaml_file=str(view_yaml_file))


# *** tests

# ** test_int: list_pages_round_trips_full_field_set
def test_int_list_pages_round_trips_full_field_set(repository: ViewYamlRepository) -> None:
    '''
    Verify list_pages() returns Page objects whose fields match what was written.

    :param repository: The ViewYamlRepository under test.
    :type repository: ViewYamlRepository
    '''

    # List all configured pages.
    pages = repository.list_pages()

    # Assert both pages were loaded as Page domain objects.
    assert len(pages) == 2
    assert all(isinstance(page, Page) for page in pages)

    # Assert the full field set round-trips for the first (non-default) entry.
    home = next(page for page in pages if page.route == '/home')
    assert home.title == 'Home'
    assert home.icon == '🏠'
    assert home.layout == 'wide'
    assert home.view_module_path == 'tiferet_streamlit.domain.view'
    assert home.view_class_name == 'Page'

    # Assert optional fields fall back to their declared defaults.
    about = next(page for page in pages if page.route == '/about')
    assert about.title == 'About'
    assert about.icon is None
    assert about.layout == 'centered'


# ** test_int: get_page_round_trips_matching_route
def test_int_get_page_round_trips_matching_route(repository: ViewYamlRepository) -> None:
    '''
    Verify get_page() returns the Page matching the requested route.

    :param repository: The ViewYamlRepository under test.
    :type repository: ViewYamlRepository
    '''

    # Retrieve the page by route.
    page = repository.get_page('/home')

    # Assert the fields match what was written.
    assert isinstance(page, Page)
    assert page.route == '/home'
    assert page.title == 'Home'
    assert page.icon == '🏠'
    assert page.layout == 'wide'


# ** test_int: get_page_returns_none_for_unknown_route
def test_int_get_page_returns_none_for_unknown_route(repository: ViewYamlRepository) -> None:
    '''
    Verify get_page() returns None for a route that is not configured.

    :param repository: The ViewYamlRepository under test.
    :type repository: ViewYamlRepository
    '''

    # Assert no page is found for an unknown route.
    assert repository.get_page('/nonexistent') is None
