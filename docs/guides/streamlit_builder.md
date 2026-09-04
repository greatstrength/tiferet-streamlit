# build_streamlit_app / StreamlitApp Guide

## Overview

`build_streamlit_app` (aliased as `StreamlitApp`) is the application entry point blueprint function. It constructs the Tiferet `AppSessionContext` via `tiferet.blueprints.app.build_app(...)`, applies any declared `Theme`, verifies the constructed app is dispatch-compatible, assembles pages, and runs the Streamlit application — all in a single call. There is no builder class or constructor to instantiate; the prior `StreamlitBuilder` class-based API was replaced by these stateless blueprint functions (see AGENTS.md's Migration Notes).

## Signature

```python
build_streamlit_app(
    interface_id: str,
    pages: Dict[str, Type[ViewContext]] = None,
    page_configs: List[Page] = None,
    get_page_configs: Callable[..., List[Page]] = None,
    theme: Theme = None,
    **parameters,
)
```

## Related Blueprint Functions

### `create_view(view_cls, app, key, session=None) -> ViewContext`
Instantiate a `ViewContext` subclass with the given app context and key. Auto-creates a `SessionCacheContext` if `session` is not provided.

### `build_pages(app, pages) -> PageContext`
Build a `PageContext` from a `Dict[str, Type[ViewContext]]` mapping routes to view classes.

### `build_pages_from_config(app, page_configs) -> PageContext`
Build a `PageContext` from a list of `Page` domain objects. Resolves view classes via `page.get_view_type()` and registers with title and icon metadata.

### `apply_theme_config(theme, config_path='.streamlit/config.toml')` / `inject_theme_css(theme)`
Apply a declared `Theme`'s native `[theme]` fields and raw CSS, respectively. See the README's [Config-Driven Theming](../../README.md#config-driven-theming) section for the full theming behavior.

### `run(interface_id, pages=None, page_configs=None, get_page_configs=None, theme=None, **parameters)`
Convenience alias that delegates to `build_streamlit_app`.

## Behavior

- `page_configs` takes precedence over `pages`, which takes precedence over `get_page_configs`, when more than one is provided.
- Raises `TiferetError(PAGE_NOT_FOUND_ID)` if none of `pages`, `page_configs`, or `get_page_configs` is provided.
- Raises `TiferetError(INCOMPATIBLE_APP_CONTEXT_ID)` if the app object `build_app()` constructed does not expose a `run(feature_id, headers, data)`-shaped callable.

## Usage Examples

### Programmatic Pages

```python
from tiferet_streamlit import StreamlitApp, ViewContext

class HomeView(ViewContext):
    def render(self):
        st.title('Home')

StreamlitApp('my_interface', pages={'/': HomeView})
```

### Config-Driven Pages

```python
from tiferet_streamlit import StreamlitApp, Page

pages = [
    Page(route='/', title='Home', icon='🏠',
         view_module_path='app.views.home', view_class_name='HomeView'),
]

StreamlitApp('my_interface', page_configs=pages)
```

### ViewService-Backed Pages

```python
from tiferet_streamlit import StreamlitApp, get_view_service

StreamlitApp(
    'my_interface',
    get_page_configs=lambda app: get_view_service(app).list_pages(),
)
```

## Integration

- `StreamlitApp` is a single-call entry point — no separate load/initialize step is required.
- Views receive the constructed `AppSessionContext` for feature dispatch.
- See [docs/guides/widgets.md](widgets.md) for widget binding, [docs/guides/view_context.md](view_context.md) for `ViewContext`'s lifecycle, and the README's Config-Driven Theming and ViewService-Backed Page Configuration sections for `theme`/`get_page_configs` usage.
