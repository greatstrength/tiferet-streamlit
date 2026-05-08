'''Tiferet Streamlit – View Interfaces'''

# *** imports

# ** core
from abc import abstractmethod
from typing import List

# ** infra
from tiferet.interfaces.settings import Service

# ** app
from ..domain.view import Page

# *** interfaces

# ** interface: view_service
class ViewService(Service):
    '''
    Service interface for managing view and page configurations.
    '''

    # * method: get_page
    @abstractmethod
    def get_page(self, route: str) -> Page:
        '''
        Retrieve a page configuration by its route string.

        :param route: The URL path for the page.
        :type route: str
        :return: The page domain object matching the route.
        :rtype: Page
        '''
        raise NotImplementedError()

    # * method: list_pages
    @abstractmethod
    def list_pages(self) -> List[Page]:
        '''
        Return all configured page definitions.

        :return: A list of all page domain objects.
        :rtype: List[Page]
        '''
        raise NotImplementedError()
