'''Tiferet Streamlit – View YAML Repository'''

# *** imports

# ** core
from typing import Any, Dict, List, Optional

# ** infra
from tiferet.utils import YamlLoader as Yaml

# ** app
from ..domain.view import Page
from ..interfaces.view import ViewService

# *** repos

# ** repo: view_yaml_repository
class ViewYamlRepository(ViewService):
    '''
    A YAML-backed implementation of ViewService, so a Page's route can be
    added or changed by editing a configuration file instead of requiring
    a code change and redeploy.
    '''

    # * attribute: yaml_file
    yaml_file: str

    # * attribute: encoding
    encoding: str

    # * attribute: default_role
    default_role: str

    # * init
    def __init__(self, view_yaml_file: str, encoding: str = 'utf-8') -> None:
        '''
        Initialize the view YAML repository.

        :param view_yaml_file: The YAML configuration file path.
        :type view_yaml_file: str
        :param encoding: The file encoding (default is 'utf-8').
        :type encoding: str
        '''

        # Set the repository attributes.
        self.yaml_file = view_yaml_file
        self.encoding = encoding
        self.default_role = 'to_data.yaml'

    # * method: get_page
    def get_page(self, route: str) -> Optional[Page]:
        '''
        Retrieve a page configuration by its route string.

        :param route: The URL path for the page.
        :type route: str
        :return: The page domain object matching the route, or None if not found.
        :rtype: Optional[Page]
        '''

        # Load the configured pages list from the configuration file.
        pages_data: List[Dict[str, Any]] = Yaml(
            self.yaml_file,
            encoding=self.encoding,
        ).load(
            start_node=lambda data: data.get('pages', [])
        )

        # Find the entry matching the requested route.
        page_data = next(
            (entry for entry in pages_data if entry.get('route') == route),
            None,
        )

        # Return None if no matching page was found.
        if not page_data:
            return None

        # Map the page data to a Page domain object and return it.
        return Page.model_validate(page_data)

    # * method: list_pages
    def list_pages(self) -> List[Page]:
        '''
        Return all configured page definitions.

        :return: A list of all page domain objects.
        :rtype: List[Page]
        '''

        # Load the configured pages list from the configuration file.
        pages_data: List[Dict[str, Any]] = Yaml(
            self.yaml_file,
            encoding=self.encoding,
        ).load(
            start_node=lambda data: data.get('pages', [])
        )

        # Map each entry to a Page domain object and return the list.
        return [Page.model_validate(page_data) for page_data in pages_data]
