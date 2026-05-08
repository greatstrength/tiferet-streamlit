"""Tiferet Streamlit Page Context"""

# *** imports

# ** core
from typing import Dict

# ** infra
import streamlit as st

# ** app
from .view import ViewContext

# *** contexts

# ** context: page_context
class PageContext(object):
    '''
    Manages multi-page Streamlit applications.

    Maps page routes to ViewContext instances and handles navigation
    via Streamlit's st.navigation API.
    '''

    # * attribute: pages
    pages: Dict[str, ViewContext]

    # * init
    def __init__(self, pages: Dict[str, ViewContext] = None):
        '''
        Initialize the page context.

        :param pages: An optional dictionary mapping route strings to ViewContext instances.
        :type pages: Dict[str, ViewContext]
        '''

        # Initialize the pages dictionary.
        self.pages = pages or {}

    # * method: register_page
    def register_page(self, route: str, view: ViewContext, title: str = None, icon: str = None):
        '''
        Register a page with the given route and view context.

        :param route: The URL path for the page.
        :type route: str
        :param view: The ViewContext instance to render for this page.
        :type view: ViewContext
        :param title: An optional display title. Defaults to the route.
        :type title: str
        :param icon: An optional icon for the page navigation.
        :type icon: str
        '''

        # Store the view and metadata under the route key.
        self.pages[route] = dict(
            view=view,
            title=title or route,
            icon=icon,
        )

    # * method: run
    def run(self):
        '''
        Build st.Page objects from registered views and run Streamlit navigation.
        '''

        # Build st.Page objects from the registered pages.
        st_pages = []
        for route, page_info in self.pages.items():
            page_kwargs = dict(
                page=page_info['view'],
                title=page_info['title'],
                url_path=route,
            )

            # Add icon if provided.
            if page_info.get('icon'):
                page_kwargs['icon'] = page_info['icon']

            st_pages.append(st.Page(**page_kwargs))

        # Run navigation with the built pages.
        nav = st.navigation(st_pages)
        nav.run()
