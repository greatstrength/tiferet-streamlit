'''Tiferet Streamlit'''

# *** exports

try:
    # ** export: domain
    from .domain import Page, DispatchAuditRecord, Theme

    # ** export: interfaces
    from .interfaces import ViewService

    # ** export: contexts
    from .contexts import SessionCacheContext, ViewContext, ViewComponent, PageContext, get_view_service

    # ** export: blueprints
    from .blueprints import build_streamlit_app, build_streamlit_app as StreamlitApp

except Exception as e:
    import os, sys
    # Only print warning if TIFERET_SILENT_IMPORTS is not set to a truthy value
    if not os.getenv('TIFERET_SILENT_IMPORTS'):
        print(f"Warning: Failed to import tiferet-streamlit core modules: {e}", file=sys.stderr)
    pass

# *** version

__version__ = '1.0.0a5'
