'''Tiferet Streamlit – Streamlit Builder'''

# *** imports

# ** core
from typing import Dict, List, Type

# ** infra
from tiferet.builders.main import AppBuilder
from tiferet.events.static import RaiseError

# ** app
from ..assets.constants import PAGE_NOT_FOUND_ID
from ..contexts.session import SessionCacheContext
from ..contexts.view import ViewContext
from ..contexts.page import PageContext
from ..domain.view import Page

# *** builders

# ** builder: streamlit_builder
class StreamlitBuilder(AppBuilder):
    '''
    Application entry point extending Tiferet's AppBuilder with
    Streamlit-specific lifecycle management. Provides methods to
    create ViewContext instances, build multi-page configurations,
    and run the Streamlit application.
    '''

    # * method: create_view
    def create_view(self,
            view_cls: Type[ViewContext],
            app,
            key: str,
            session: SessionCacheContext = None,
        ) -> ViewContext:
        '''
        Instantiate a ViewContext subclass.

        :param view_cls: The ViewContext subclass to instantiate.
        :type view_cls: Type[ViewContext]
        :param app: The Tiferet app interface context.
        :type app: AppInterfaceContext
        :param key: Unique identifier for this view instance.
        :type key: str
        :param session: Optional session cache. Auto-created with namespace=key if not provided.
        :type session: SessionCacheContext
        :return: The constructed view.
        :rtype: ViewContext
        '''

        # Create the session if not provided.
        session = session or SessionCacheContext(namespace=key)

        # Instantiate and return the view.
        return view_cls(app=app, key=key, session=session)

    # * method: build_pages
    def build_pages(self,
            app,
            pages: Dict[str, Type[ViewContext]],
        ) -> PageContext:
        '''
        Build a PageContext from a route-to-ViewContext class mapping.

        :param app: The Tiferet app interface context.
        :type app: AppInterfaceContext
        :param pages: Dictionary mapping route strings to ViewContext classes.
        :type pages: Dict[str, Type[ViewContext]]
        :return: The configured page context.
        :rtype: PageContext
        '''

        # Create a new page context.
        page_ctx = PageContext()

        # Register each route and view.
        for route, view_cls in pages.items():

            # Create the view instance.
            view = self.create_view(view_cls, app, key=route)

            # Register the page.
            page_ctx.register_page(route, view)

        # Return the page context.
        return page_ctx

    # * method: build_pages_from_config
    def build_pages_from_config(self,
            app,
            page_configs: List[Page],
        ) -> PageContext:
        '''
        Build a PageContext from Page domain objects.

        :param app: The Tiferet app interface context.
        :type app: AppInterfaceContext
        :param page_configs: List of Page domain objects.
        :type page_configs: List[Page]
        :return: The configured page context.
        :rtype: PageContext
        '''

        # Create a new page context.
        page_ctx = PageContext()

        # Register each page config.
        for page in page_configs:

            # Resolve the ViewContext class.
            view_cls = page.get_view_type()

            # Create the view instance.
            view = self.create_view(view_cls, app, key=page.route)

            # Register the page with metadata.
            page_ctx.register_page(
                page.route,
                view,
                title=page.title,
                icon=page.icon,
            )

        # Return the page context.
        return page_ctx

    # * method: run
    def run(self,
            interface_id: str,
            pages: Dict[str, Type[ViewContext]] = None,
            page_configs: List[Page] = None,
        ):
        '''
        Load the Tiferet interface and run the Streamlit application.

        :param interface_id: The Tiferet interface ID to load.
        :type interface_id: str
        :param pages: Optional dict mapping routes to ViewContext classes.
        :type pages: Dict[str, Type[ViewContext]]
        :param page_configs: Optional list of Page domain objects. Takes precedence over pages.
        :type page_configs: List[Page]
        '''

        # Load the Tiferet interface.
        app = self.load_interface(interface_id)

        # Build pages from config if provided (takes precedence).
        if page_configs is not None:
            page_ctx = self.build_pages_from_config(app, page_configs)

        # Otherwise build pages from dict.
        elif pages is not None:
            page_ctx = self.build_pages(app, pages)

        # Raise error if no pages provided.
        else:
            RaiseError.execute(
                error_code=PAGE_NOT_FOUND_ID,
            )

        # Run the page context.
        page_ctx.run()
