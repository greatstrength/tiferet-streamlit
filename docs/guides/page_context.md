# PageContext & Page Guide

**Modules:**
- `tiferet_streamlit.contexts.page` — `PageContext`
- `tiferet_streamlit.domain.view` — `Page`

**Imports:**
```python
from tiferet_streamlit import PageContext, Page
```

## Overview

`PageContext` manages multi-page Streamlit applications by mapping routes to `ViewContext` instances and delegating to Streamlit's `st.navigation` API. The `Page` domain object provides configuration-driven page metadata.

In most cases, you interact with these through `StreamlitBuilder.run()` rather than directly.

## PageContext

### Registration

```python
from tiferet_streamlit import PageContext

page_ctx = PageContext()
page_ctx.register_page('home', home_view, title='Home', icon=':house:')
page_ctx.register_page('calculator', calc_view, title='Calculator')
```

Parameters:
- `route` — URL path for the page
- `view` — a `ViewContext` instance (callable)
- `title` — display title (defaults to route)
- `icon` — optional Streamlit icon string

### Running

```python
page_ctx.run()
```

This builds `st.Page` objects from all registered pages and calls `st.navigation(...).run()`.

### Direct Usage

While `StreamlitBuilder` handles page context creation automatically, you can use `PageContext` directly for custom setups:

```python
from tiferet_streamlit import PageContext, SessionCacheContext
from tiferet.contexts.app import AppInterfaceContext

# Assume `interface` is a loaded AppInterfaceContext
page_ctx = PageContext()

home = HomeView(app=interface, key='home')
calc = CalculatorView(app=interface, key='calculator')

page_ctx.register_page('home', home, title='Home', icon=':house:')
page_ctx.register_page('calculator', calc, title='Calculator', icon=':abacus:')
page_ctx.run()
```

## Page Domain Object

`Page` is a Tiferet `DomainObject` for configuration-driven page metadata:

```python
from tiferet_streamlit import Page

page = Page(
    route='calculator',
    title='Calculator',
    icon=':abacus:',
    layout='wide',
    view_module_path='views',
    view_class_name='CalculatorView',
)
```

### Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `route` | `str` | required | URL path for the page |
| `title` | `str` | required | Display title |
| `icon` | `str \| None` | `None` | Optional Streamlit icon |
| `layout` | `str` | `'centered'` | Page layout (`'centered'` or `'wide'`) |
| `view_module_path` | `str` | required | Python module path to the ViewContext class |
| `view_class_name` | `str` | required | Class name of the ViewContext |

### Dynamic Class Resolution

`Page.get_view_type()` imports and returns the `ViewContext` class at runtime:

```python
view_cls = page.get_view_type()  # resolves views.CalculatorView
```

This is used internally by `StreamlitBuilder.build_pages_from_config()`.

### Usage with StreamlitBuilder

```python
from tiferet_streamlit import StreamlitApp, Page

pages = [
    Page(route='home', title='Home', icon=':house:',
         view_module_path='views', view_class_name='HomeView'),
    Page(route='calculator', title='Calculator', icon=':abacus:',
         view_module_path='views', view_class_name='CalculatorView'),
]

app = StreamlitApp()
app.load_app_service(app_yaml_file='config.yml')
app.run('my_app', page_configs=pages)
```

## Testing

```python
from unittest import mock
from tiferet_streamlit import PageContext, ViewContext

class StubView(ViewContext):
    def render(self): pass

def test_register_and_run():
    with mock.patch('streamlit.session_state', {}):
        app = mock.MagicMock()
        page_ctx = PageContext()
        view = StubView(app=app, key='home')
        page_ctx.register_page('home', view, title='Home')

        assert 'home' in page_ctx.pages
        assert page_ctx.pages['home']['title'] == 'Home'
```
