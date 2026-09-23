'''Tiferet Streamlit – Streamlit Blueprints'''

# *** imports

# ** core
import inspect
from pathlib import Path
from typing import Any, Dict, List, Type

# ** infra
import streamlit as st
import toml
from tiferet import TiferetError
from tiferet.blueprints.app import build_app

# ** app
from ..assets.constants import (
    INCOMPATIBLE_APP_CONTEXT_ID,
    PAGE_NOT_FOUND_ID,
)
from ..contexts.session import SessionCacheContext
from ..contexts.view import ViewContext
from ..contexts.page import PageContext
from ..domain.theme import Theme
from ..domain.view import Page

# *** functions

# ** function: is_app_context_compatible
def is_app_context_compatible(app: Any) -> bool:
    '''
    Check whether an app exposes a run(feature_id, headers, data)-shaped callable.

    :param app: The object returned by build_app.
    :type app: Any
    :return: True when run accepts that call shape, otherwise False.
    :rtype: bool
    '''

    # Resolve the run method.
    run_method = getattr(app, 'run', None)

    # Reject a missing or non-callable run.
    if not callable(run_method):
        return False

    # Bind the required call shape.
    try:
        inspect.signature(run_method).bind(
            'feature_id',
            headers={},
            data={},
        )
    except (TypeError, ValueError):
        return False

    # Accept a matching call shape.
    return True


# *** blueprints

# ** blueprint: create_view
def create_view(
        view_cls: Type[ViewContext],
        app,
        key: str,
        session: SessionCacheContext = None,
    ) -> ViewContext:
    '''
    Instantiate a ViewContext subclass with a SessionCacheContext.

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


# ** blueprint: build_pages
def build_pages(
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
        view = create_view(view_cls, app, key=route)

        # Register the page.
        page_ctx.register_page(route, view)

    # Return the page context.
    return page_ctx


# ** blueprint: build_pages_from_config
def build_pages_from_config(
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
        view = create_view(view_cls, app, key=page.route)

        # Register the page with metadata.
        page_ctx.register_page(
            page.route,
            view,
            title=page.title,
            icon=page.icon,
        )

    # Return the page context.
    return page_ctx


# ** blueprint: apply_theme_config
def apply_theme_config(
        theme: Theme,
        config_path: str = '.streamlit/config.toml',
    ) -> None:
    '''
    Merge a theme's native fields into the Streamlit config file.

    Streamlit reads this file at process startup, so the write does not
    re-theme the current process.

    :param theme: The theme whose native fields are written.
    :type theme: Theme
    :param config_path: Path of the Streamlit config file to merge into.
    :type config_path: str
    :return: None.
    :rtype: None
    '''

    # Skip the write when there are no native fields.
    native_fields = theme.native_fields
    if not native_fields:
        return

    # Load an existing document, or start from an empty one.
    path = Path(config_path)
    if path.exists():
        with path.open(encoding='utf-8') as config_file:
            document = toml.load(config_file)
    else:
        document = {}

    # Merge native fields without replacing sibling sections.
    document.setdefault('theme', {}).update(native_fields)

    # Ensure the parent directory exists.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write the merged document.
    with path.open('w', encoding='utf-8') as config_file:
        toml.dump(document, config_file)


# ** blueprint: inject_theme_css
def inject_theme_css(theme: Theme) -> None:
    '''
    Inject a theme's custom CSS into the current Streamlit run.

    :param theme: The theme whose custom CSS is injected.
    :type theme: Theme
    :return: None.
    :rtype: None
    '''

    # Skip injection when custom CSS is missing or empty.
    if not theme.custom_css:
        return

    # Inject the style block for this run.
    st.markdown(
        f'<style>{theme.custom_css}</style>',
        unsafe_allow_html=True,
    )


# ** blueprint: build_streamlit_app
def build_streamlit_app(
        interface_id: str,
        pages: Dict[str, Type[ViewContext]] = None,
        page_configs: List[Page] = None,
        theme: Theme = None,
        **parameters,
    ):
    '''
    Primary entry point. Builds the Tiferet app, builds pages,
    and runs the Streamlit application.

    :param interface_id: The Tiferet interface ID to load.
    :type interface_id: str
    :param pages: Optional dict mapping routes to ViewContext classes.
    :type pages: Dict[str, Type[ViewContext]]
    :param page_configs: Optional list of Page domain objects. Takes precedence over pages.
    :type page_configs: List[Page]
    :param theme: Optional theme applied before the app is built. None performs no theme I/O.
    :type theme: Theme
    :param parameters: Additional keyword arguments passed to build_app.
    :type parameters: dict
    '''

    # Apply the declared theme before the app is built.
    if theme is not None:
        apply_theme_config(theme)
        inject_theme_css(theme)

    # Build the app from the interface identifier.
    app = build_app(interface_id, **parameters)

    # Reject an app that cannot accept run(feature_id, headers, data).
    if not is_app_context_compatible(app):
        TiferetError.raise_error(
            INCOMPATIBLE_APP_CONTEXT_ID,
            message=f'The app built for interface "{interface_id}" does not expose a run(feature_id, headers, data)-shaped callable; the installed tiferet version may be incompatible with tiferet-streamlit.',
            interface_id=interface_id,
        )

    # Build pages from config if provided (takes precedence).
    if page_configs is not None:
        page_ctx = build_pages_from_config(app, page_configs)

    # Otherwise build pages from dict.
    elif pages is not None:
        page_ctx = build_pages(app, pages)

    # Raise error if no pages provided.
    else:
        TiferetError.raise_error(PAGE_NOT_FOUND_ID)

    # Run the page context.
    page_ctx.run()


# ** blueprint: run
def run(
        interface_id: str,
        pages: Dict[str, Type[ViewContext]] = None,
        page_configs: List[Page] = None,
        theme: Theme = None,
        **parameters,
    ):
    '''
    Convenience alias that delegates to build_streamlit_app.

    :param interface_id: The Tiferet interface ID to load.
    :type interface_id: str
    :param pages: Optional dict mapping routes to ViewContext classes.
    :type pages: Dict[str, Type[ViewContext]]
    :param page_configs: Optional list of Page domain objects.
    :type page_configs: List[Page]
    :param theme: Optional theme forwarded to build_streamlit_app.
    :type theme: Theme
    :param parameters: Additional keyword arguments.
    :type parameters: dict
    '''

    # Delegate to build_streamlit_app.
    build_streamlit_app(
        interface_id,
        pages=pages,
        page_configs=page_configs,
        theme=theme,
        **parameters,
    )
