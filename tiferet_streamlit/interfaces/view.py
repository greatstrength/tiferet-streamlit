"""Tiferet Streamlit View Interfaces"""

# *** imports

# ** core
from abc import abstractmethod
from typing import List

# ** app
from tiferet.interfaces.settings import Service
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
        Retrieve a page configuration by route.

        :param route: The page route.
        :type route: str
        :return: The page configuration.
        :rtype: Page
        '''

        raise NotImplementedError()

    # * method: list_pages
    @abstractmethod
    def list_pages(self) -> List[Page]:
        '''
        List all configured page definitions.

        :return: A list of page configurations.
        :rtype: List[Page]
        '''

        raise NotImplementedError()
