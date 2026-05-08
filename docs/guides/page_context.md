# PageContext Guide

## Overview

`PageContext` is the multi-page navigation manager. It maps page routes to `ViewContext` instances and handles navigation via Streamlit's `st.navigation` API.

## Constructor

```python
PageContext(pages=None)
```

- **`pages`** — Optional dict of pre-registered pages (default: `{}`).

## Methods

### `register_page(route, view, title=None, icon=None)`
Register a page. Title defaults to the route string. Icon defaults to `None`.

### `run()`
Build `st.Page` objects from registered pages, pass to `st.navigation()`, and call `.run()` on the result.

## Usage Example

```python
from tiferet_streamlit import PageContext, ViewContext

class HomeView(ViewContext):
    def render(self):
        st.title('Home')

class AboutView(ViewContext):
    def render(self):
        st.title('About')

# Manual registration
ctx = PageContext()
ctx.register_page('/', home_view, title='Home', icon='🏠')
ctx.register_page('/about', about_view, title='About', icon='ℹ️')
ctx.run()
```

## Integration

- Typically created by `StreamlitBuilder.build_pages()` or `StreamlitBuilder.build_pages_from_config()`.
- Each registered view is a `ViewContext` instance (already constructed with `app` and `key`).
- `run()` must be called from the main Streamlit script entry point.
