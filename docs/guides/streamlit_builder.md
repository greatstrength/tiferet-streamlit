# StreamlitBuilder Guide

## Overview

`StreamlitBuilder` (aliased as `StreamlitApp`) is the application entry point. It extends Tiferet's `AppBuilder` with Streamlit-specific lifecycle management for creating views, building multi-page configurations, and running the application.

## Constructor

```python
StreamlitBuilder()
```

Inherits from `AppBuilder`. Initializes cache and service provider.

## Methods

### `create_view(view_cls, app, key, session=None) -> ViewContext`
Instantiate a `ViewContext` subclass with the given app context and key. Auto-creates a `SessionCacheContext` if `session` is not provided.

### `build_pages(app, pages) -> PageContext`
Build a `PageContext` from a `Dict[str, Type[ViewContext]]` mapping routes to view classes.

### `build_pages_from_config(app, page_configs) -> PageContext`
Build a `PageContext` from a list of `Page` domain objects. Resolves view classes via `page.get_view_type()` and registers with title and icon metadata.

### `run(interface_id, pages=None, page_configs=None)`
Load the Tiferet interface and run the Streamlit application.
- `page_configs` takes precedence over `pages` when both are provided.
- Raises `TiferetError(PAGE_NOT_FOUND_ID)` if neither is provided.

## Usage Examples

### Programmatic Pages

```python
from tiferet_streamlit import StreamlitApp, ViewContext

class HomeView(ViewContext):
    def render(self):
        st.title('Home')

app = StreamlitApp()
app.load_app_service()
app.run('my_interface', pages={'/': HomeView})
```

### Config-Driven Pages

```python
from tiferet_streamlit import StreamlitApp, Page

pages = [
    Page(route='/', title='Home', icon='🏠',
         view_module_path='app.views.home', view_class_name='HomeView'),
]

app = StreamlitApp()
app.load_app_service()
app.run('my_interface', page_configs=pages)
```

## Integration

- Call `load_app_service()` before `run()` to initialize the Tiferet application service.
- The `StreamlitApp` alias provides a more intuitive name for application scripts.
- Views receive the loaded `AppInterfaceContext` for feature dispatch.
