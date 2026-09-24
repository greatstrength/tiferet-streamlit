'''Tiferet Streamlit'''

# *** exports

# Use a try-except block to avoid import errors on build systems.
try:
    # Domain objects.
    from .domain import Page, Theme, DispatchAuditRecord

    # Service interfaces.
    from .interfaces import ViewService

    # Runtime contexts.
    from .contexts import SessionCacheContext, ViewContext, ViewComponent, PageContext, get_view_service

    # Blueprint functions.
    from .blueprints import build_streamlit_app, build_streamlit_app as StreamlitApp

except Exception as e:
    import os, sys
    # Only print warning if TIFERET_SILENT_IMPORTS is not set to a truthy value
    if not os.getenv('TIFERET_SILENT_IMPORTS'):
        print(f"Warning: Failed to import tiferet-streamlit core modules: {e}", file=sys.stderr)
    pass

# *** version

__version__ = '1.0.0'
