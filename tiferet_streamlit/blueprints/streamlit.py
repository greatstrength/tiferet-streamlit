'''Tiferet Streamlit – Streamlit Blueprints'''

# *** imports

# ** core
from pathlib import Path
from typing import Callable, Dict, List, Type

# ** infra
import streamlit as st
import toml
from tiferet.blueprints.main import (
    resolve_interface,
    realize_interface,
)
from tiferet.events.static import RaiseError

# ** app
from ..assets.constants import PAGE_NOT_FOUND_ID
from ..contexts.session import SessionCacheContext
from ..contexts.view import ViewContext
from ..contexts.page import PageContext
from ..domain.view import Page
from ..domain.theme import Theme

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
    Write a declared theme's native [theme] fields into config.toml,
    merging into any existing file's [theme] section rather than
    overwriting unrelated settings (e.g. [server]).

    Streamlit reads config.toml once at process startup, so this write
    takes effect on the *next* Streamlit process start — it does not
    re-theme the currently running app.

    :param theme: The declared theme to apply.
    :type theme: Theme
    :param config_path: Path to Streamlit's config.toml file.
    :type config_path: str
    '''

    # Skip entirely if the theme declares no native fields.
    native_fields = theme.native_fields
    if not native_fields:
        return

    # Load any existing config so unrelated sections are preserved.
    config_file = Path(config_path)
    existing_config = toml.load(config_file) if config_file.exists() else {}

    # Merge the declared fields into the [theme] section only.
    existing_config.setdefault('theme', {}).update(native_fields)

    # Ensure the parent directory exists before writing.
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Write the merged config back to disk.
    with config_file.open('w', encoding='utf-8') as file:
        toml.dump(existing_config, file)

# ** blueprint: inject_theme_css
def inject_theme_css(theme: Theme) -> None:
    '''
    Inject a declared theme's raw CSS via Streamlit's own markdown/HTML
    mechanism. Unlike the native [theme] file, this applies immediately
    on every app run.

    :param theme: The declared theme to apply.
    :type theme: Theme
    '''

    # Skip entirely if no custom CSS was declared.
    if not theme.custom_css:
        return

    # Inject the CSS via Streamlit's markdown mechanism.
    st.markdown(f'<style>{theme.custom_css}</style>', unsafe_allow_html=True)

# ** blueprint: build_streamlit_app
def build_streamlit_app(
        interface_id: str,
        pages: Dict[str, Type[ViewContext]] = None,
        page_configs: List[Page] = None,
        get_page_configs: Callable[..., List[Page]] = None,
        theme: Theme = None,
        **parameters,
    ):
    '''
    Primary entry point. Resolves and realizes the Tiferet interface,
    builds pages, and runs the Streamlit application.

    :param interface_id: The Tiferet interface ID to load.
    :type interface_id: str
    :param pages: Optional dict mapping routes to ViewContext classes.
    :type pages: Dict[str, Type[ViewContext]]
    :param page_configs: Optional list of Page domain objects. Takes precedence over pages.
    :type page_configs: List[Page]
    :param get_page_configs: Optional callable invoked with the realized app interface
        context, returning a list of Page domain objects. Only consulted when neither
        page_configs nor pages is provided, so their existing precedence is unchanged.
        This is how a DI-resolved source (e.g. contexts.di.get_view_service(app).list_pages())
        plugs in without this blueprint importing any service interface directly.
    :type get_page_configs: Callable[..., List[Page]]
    :param theme: Optional declared theme. Omitting it leaves existing behavior unchanged.
    :type theme: Theme
    :param parameters: Additional keyword arguments passed to resolve_interface.
    :type parameters: dict
    '''

    # Apply the declared theme's native config and CSS, if provided.
    if theme is not None:
        apply_theme_config(theme)
        inject_theme_css(theme)

    # Resolve the interface definition.
    app_interface, _ = resolve_interface(interface_id, **parameters)

    # Realize the app interface context.
    app = realize_interface(app_interface, interface_id)

    # Build pages from config if provided (takes precedence).
    if page_configs is not None:
        page_ctx = build_pages_from_config(app, page_configs)

    # Otherwise build pages from dict.
    elif pages is not None:
        page_ctx = build_pages(app, pages)

    # Otherwise assemble pages via a caller-supplied handler.
    elif get_page_configs is not None:
        page_ctx = build_pages_from_config(app, get_page_configs(app))

    # Raise error if no pages provided.
    else:
        RaiseError.execute(
            error_code=PAGE_NOT_FOUND_ID,
        )

    # Run the page context.
    page_ctx.run()

# ** blueprint: run
def run(
        interface_id: str,
        pages: Dict[str, Type[ViewContext]] = None,
        page_configs: List[Page] = None,
        get_page_configs: Callable[..., List[Page]] = None,
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
    :param get_page_configs: Optional callable invoked with the realized app interface
        context, returning a list of Page domain objects.
    :type get_page_configs: Callable[..., List[Page]]
    :param theme: Optional declared theme. Omitting it leaves existing behavior unchanged.
    :type theme: Theme
    :param parameters: Additional keyword arguments.
    :type parameters: dict
    '''

    # Delegate to build_streamlit_app.
    build_streamlit_app(
        interface_id,
        pages=pages,
        page_configs=page_configs,
        get_page_configs=get_page_configs,
        theme=theme,
        **parameters,
    )
