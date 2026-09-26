# PageContext Guide

## Overview

`PageContext` is the multi-page navigation manager. It maps page routes to `ViewContext` instances and handles navigation via Streamlit's `st.navigation` API.

## Constructor

```python
PageContext(pages=None)
```

- **`pages`** — Optional dict of pre-registered pages (default: `{}`).

## Methods

### `register_page(route, view, title=None, icon=None, layout=None)`
Register a page. Title defaults to the route string. Icon defaults to `None`. Layout defaults to `None` and accepts `'centered'` or `'wide'`.

<a id="pagecontext-run"></a>
### `run(position='sidebar')`
Build `st.Page` objects from registered pages, pass to `st.navigation()`, and call `.run()` on the result.

`position` accepts `'sidebar'` (the default) or `'top'` and is passed through to `st.navigation()`. Any other value, including `'hidden'`, raises `INVALID_NAVIGATION_POSITION` and neither `st.navigation()` nor `st.set_page_config()` is called.

#### Layout rule

Before building any `st.Page`, `run()` may call `st.set_page_config(layout=...)` once, but only when all of these hold:

1. No Streamlit command has been issued yet in this script run (checked via the script-run context's tracked commands).
2. At least one registered page has a non-`None` `layout`.
3. Every non-`None` `layout` is the same value.

If a Streamlit command has already run, or if registered layouts differ, `run()` skips `set_page_config()` entirely and proceeds straight to building pages and navigating. There is no way to apply a per-page layout after `st.navigation()` has resolved the selected page.

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
ctx.register_page('/about', about_view, title='About')
ctx.run(position='top')
```

The icon example above (`🏠`) is a single emoji character — the only icon format this package documents. Emoji shortcodes such as `:house:` are rejected by Streamlit's icon validation and do not render.

## Integration

- Typically created by `build_pages()` or `build_pages_from_config()` from `tiferet_streamlit.blueprints`.
- Each registered view is a `ViewContext` instance (already constructed with `app` and `key`).
- `run()` must be called from the main Streamlit script entry point.
