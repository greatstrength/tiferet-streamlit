"""Tiferet Streamlit Builder"""

# *** imports

# ** core
from typing import Any, Dict, List, Type

# ** infra
import streamlit as st

# ** app
from tiferet.builders.main import AppBuilder
from tiferet.contexts.app import AppInterfaceContext
from tiferet.events import RaiseError
from ..assets.constants import INVALID_VIEW_TYPE_ID, PAGE_NOT_FOUND_ID
from ..contexts.session import SessionCacheContext
from ..contexts.view import ViewContext
from ..contexts.page import PageContext
from ..domain.view import Page

# *** builders

# ** builder: streamlit_builder
class StreamlitBuilder(AppBuilder):
    '''
    Specialized application builder for Streamlit applications.

    Extends AppBuilder with Streamlit-specific lifecycle management:
    session state integration, page registration, and multi-page navigation.
    Mirrors the CliBuilder pattern for the Streamlit runtime.
    '''

    # * method: create_view
    def create_view(self,
            view_cls: Type[ViewContext],
            app: AppInterfaceContext,
            key: str,
            session: SessionCacheContext = None) -> ViewContext:
        '''
        Create a ViewContext instance for the given view class.

        :param view_cls: The ViewContext subclass to instantiate.
        :type view_cls: Type[ViewContext]
        :param app: The application interface context for feature dispatch.
        :type app: AppInterfaceContext
        :param key: The unique key for the view instance.
        :type key: str
        :param session: An optional session cache context.
        :type session: SessionCacheContext
        :return: The instantiated ViewContext.
        :rtype: ViewContext
        '''

        # Create a namespaced session for this view.
        view_session = session or SessionCacheContext(namespace=key)

        # Instantiate and return the view.
        return view_cls(app=app, key=key, session=view_session)

    # * method: build_pages
    def build_pages(self,
            app: AppInterfaceContext,
            pages: Dict[str, Type[ViewContext]]) -> PageContext:
        '''
        Build a PageContext from a dictionary of route-to-ViewContext class mappings.

        :param app: The application interface context.
        :type app: AppInterfaceContext
        :param pages: A dictionary mapping route strings to ViewContext subclasses.
        :type pages: Dict[str, Type[ViewContext]]
        :return: The configured page context.
        :rtype: PageContext
        '''

        # Create the page context.
        page_ctx = PageContext()

        # Register each page.
        for route, view_cls in pages.items():

            # Create the view instance.
            view = self.create_view(view_cls, app, key=route)

            # Register the page.
            page_ctx.register_page(route, view)

        # Return the configured page context.
        return page_ctx

    # * method: build_pages_from_config
    def build_pages_from_config(self,
            app: AppInterfaceContext,
            page_configs: List[Page]) -> PageContext:
        '''
        Build a PageContext from a list of Page domain objects.

        :param app: The application interface context.
        :type app: AppInterfaceContext
        :param page_configs: A list of Page domain objects with view metadata.
        :type page_configs: List[Page]
        :return: The configured page context.
        :rtype: PageContext
        '''

        # Create the page context.
        page_ctx = PageContext()

        # Register each page from its configuration.
        for page in page_configs:

            # Resolve the ViewContext class.
            view_cls = page.get_view_type()

            # Create the view instance.
            view = self.create_view(view_cls, app, key=page.route)

            # Register the page with its metadata.
            page_ctx.register_page(
                route=page.route,
                view=view,
                title=page.title,
                icon=page.icon,
            )

        # Return the configured page context.
        return page_ctx

    # * method: run
    def run(self,
            interface_id: str,
            pages: Dict[str, Type[ViewContext]] = None,
            page_configs: List[Page] = None) -> None:
        '''
        Build and run the Streamlit application.

        Loads the Tiferet interface, wires session state, registers pages,
        and starts Streamlit navigation.

        :param interface_id: The interface identifier from app.yml.
        :type interface_id: str
        :param pages: An optional dictionary mapping routes to ViewContext subclasses.
        :type pages: Dict[str, Type[ViewContext]]
        :param page_configs: An optional list of Page domain objects for YAML-driven configuration.
        :type page_configs: List[Page]
        '''

        # Load the Tiferet interface.
        interface = self.load_interface(interface_id)

        # Build pages from either programmatic or config-driven definitions.
        if page_configs:
            page_ctx = self.build_pages_from_config(interface, page_configs)
        elif pages:
            page_ctx = self.build_pages(interface, pages)
        else:
            RaiseError.execute(
                PAGE_NOT_FOUND_ID,
                'No pages provided. Supply either pages or page_configs.',
            )

        # Run the Streamlit navigation.
        page_ctx.run()
