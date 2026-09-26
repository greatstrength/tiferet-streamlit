'''Tiferet Streamlit – Page Context'''

# *** imports

# ** core
from typing import Dict

# ** infra
import streamlit as st
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
from tiferet import TiferetError

# ** app
from ..assets.constants import INVALID_NAVIGATION_POSITION_ID
from .view import ViewContext

# *** functions

# ** function: _page_config_can_precede_first_streamlit_call
def _page_config_can_precede_first_streamlit_call() -> bool:
    '''
    Check whether st.set_page_config can still be the first Streamlit command
    issued during the current script run.

    :return: True when a script run context exists and no commands have been tracked yet.
    :rtype: bool
    '''

    # Resolve the current script run context.
    ctx = get_script_run_ctx()

    # A missing context means no Streamlit call can safely go first.
    if ctx is None:
        return False

    # Only a context with no tracked commands can still go first.
    return not ctx.tracked_commands

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
            layout: str = None,
        ):
        '''
        Register a page with its route, view, title, icon, and layout.

        :param route: The URL path for the page.
        :type route: str
        :param view: The ViewContext instance for this page.
        :type view: ViewContext
        :param title: Optional display title. Defaults to the route string.
        :type title: str
        :param icon: Optional icon for navigation.
        :type icon: str
        :param layout: Optional page layout ("centered" or "wide") applied via set_page_config when uniform across pages.
        :type layout: str
        '''

        # Store the view and metadata under the route key.
        self.pages[route] = dict(
            view=view,
            title=title or route,
            icon=icon,
            layout=layout,
        )

    # * method: run
    # >> see: @guides/page_context.md#pagecontext-run
    def run(self, position: str = 'sidebar'):
        '''
        Build st.Page objects from registered pages, pass them to
        st.navigation(), and run the selected page.

        :param position: Where Streamlit renders navigation: "sidebar" or "top".
        :type position: str
        :raises TiferetError: If position is not "sidebar" or "top".
        '''

        # Reject any position other than sidebar or top.
        if position not in ('sidebar', 'top'):
            TiferetError.raise_error(
                INVALID_NAVIGATION_POSITION_ID,
                message='position must be "sidebar" or "top".',
                position=position,
            )

        # Apply a shared layout before the first Streamlit call, when eligible.
        layouts = {
            meta['layout'] for meta in self.pages.values()
            if meta['layout'] is not None
        }
        if _page_config_can_precede_first_streamlit_call() and len(layouts) == 1:
            st.set_page_config(layout=layouts.pop())

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
        nav = st.navigation(page_list, position=position)

        # Run the selected page.
        nav.run()
