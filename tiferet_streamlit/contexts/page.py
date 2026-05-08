'''Tiferet Streamlit – Page Context'''

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
    Multi-page navigation manager for Streamlit applications.
    Maps page routes to ViewContext instances and handles navigation
    via Streamlit's st.navigation API.
    '''

    # * attribute: pages
    pages: Dict[str, dict]

    # * init
    def __init__(self, pages: Dict[str, dict] = None):
        '''
        Initialize the page context.

        :param pages: Optional dictionary mapping route keys to page metadata dicts.
        :type pages: Dict[str, dict]
        '''

        # Initialize the pages registry.
        self.pages = pages or {}

    # * method: register_page
    def register_page(self,
            route: str,
            view: ViewContext,
            title: str = None,
            icon: str = None,
        ):
        '''
        Register a page with its route, view, title, and icon.

        :param route: The URL path for the page.
        :type route: str
        :param view: The ViewContext instance for this page.
        :type view: ViewContext
        :param title: Optional display title. Defaults to the route string.
        :type title: str
        :param icon: Optional icon for navigation.
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
        Build st.Page objects from registered pages, pass them to
        st.navigation(), and run the selected page.
        '''

        # Build st.Page objects for each registered page.
        page_list = []
        for route, meta in self.pages.items():

            # Build kwargs for st.Page.
            page_kwargs = dict(
                page=meta['view'],
                title=meta['title'],
                url_path=route,
            )

            # Include icon if set.
            if meta['icon']:
                page_kwargs['icon'] = meta['icon']

            # Create the st.Page object.
            page_list.append(st.Page(**page_kwargs))

        # Delegate to Streamlit navigation.
        nav = st.navigation(page_list)

        # Run the selected page.
        nav.run()
