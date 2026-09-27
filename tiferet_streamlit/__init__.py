'''Tiferet Streamlit'''

# *** exports

# Use a try-except block to avoid import errors on build systems.
try:
    from .domain import Page, Theme, DispatchAuditRecord
    from .interfaces import ViewService
    from .contexts import SessionCacheContext, ViewContext, ViewComponent, PageContext, get_view_service
    from .blueprints import (
        build_streamlit_app,
        inject_theme_css,
        build_streamlit_app as StreamlitApp,
    )
    from .blueprints.streamlit import assert_declared_tiferet_range

    # Enforce the declared tiferet range on every import.
    assert_declared_tiferet_range()

except Exception as e:
    import os, sys

    # Re-raise the declared-range error; it must not be swallowed below.
    try:
        from tiferet import TiferetError
    except Exception:
        TiferetError = None
    if TiferetError is not None and isinstance(e, TiferetError):
        raise

    # Only print warning if TIFERET_SILENT_IMPORTS is not set to a truthy value
    if not os.getenv('TIFERET_SILENT_IMPORTS'):
        print(f"Warning: Failed to import tiferet-streamlit core modules: {e}", file=sys.stderr)
    pass

# *** version

__version__ = '1.0.1'
