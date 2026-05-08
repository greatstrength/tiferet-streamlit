"""Tiferet Streamlit Extension"""

# *** exports

# ** app
try:
    from .builders import StreamlitBuilder, StreamlitApp
    from .contexts import (
        SessionCacheContext,
        ViewContext,
        ViewComponent,
        PageContext,
    )
    from .domain import Page
    from .interfaces import ViewService
except Exception as e:
    import os, sys
    if not os.getenv('TIFERET_SILENT_IMPORTS'):
        print(f"Warning: Failed to import tiferet_streamlit modules: {e}", file=sys.stderr)
    pass

# *** version

__version__ = '0.1.0a1'