'''Tiferet Streamlit – View YAML Repository'''

# *** imports

# ** core
from typing import List, Optional

# ** infra
from tiferet.utils import YamlLoader as Yaml

# ** app
from ..domain.view import Page
from ..interfaces.view import ViewService

# *** repos

# ** repo: view_yaml_repository
class ViewYamlRepository(ViewService):
    '''
    YAML-backed page store so a route can be added by editing a config file.

    The pages list deserializes into Page objects. This repository is
    resolved through dependency injection and is not a package export.
    '''

    # * attribute: yaml_file
    yaml_file: str

    # * attribute: encoding
    encoding: str

    # * attribute: default_role
    default_role: str

    # * init
    def __init__(self, view_config: str, encoding: str = 'utf-8') -> None:
        '''
        Initialize the view YAML repository.

        :param view_config: Path to the view configuration file.
        :type view_config: str
        :param encoding: File encoding.
        :type encoding: str
        '''

        # Assign the foundation attributes without reading the file.
        self.yaml_file = view_config
        self.encoding = encoding
        self.default_role = 'to_data.yaml'

    # * method: get_page
    def get_page(self, route: str) -> Optional[Page]:
        '''
        Retrieve a page configuration by its route string.

        :param route: The URL path for the page.
        :type route: str
        :return: The matching page, or None when the route is absent.
        :rtype: Optional[Page]
        '''

        # Load the pages list. A missing pages key yields an empty list.
        pages_data = Yaml(self.yaml_file, encoding=self.encoding).load(
            start_node=lambda data: data.get('pages', []),
        )

        # Find the first entry whose route equals the argument.
        page_data = None
        for entry in pages_data:
            if entry.get('route') == route:
                page_data = entry
                break

        # Return None when there is no match.
        if page_data is None:
            return None

        # Return the matching entry as a Page.
        return Page.model_validate(page_data)

    # * method: list_pages
    def list_pages(self) -> List[Page]:
        '''
        Return all configured page definitions.

        :return: Every page in the configuration file.
        :rtype: List[Page]
        '''

        # Load the pages list. A missing pages key yields an empty list.
        pages_data = Yaml(self.yaml_file, encoding=self.encoding).load(
            start_node=lambda data: data.get('pages', []),
        )

        # Validate each entry as a Page.
        return [Page.model_validate(page_data) for page_data in pages_data]
