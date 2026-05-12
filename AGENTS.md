# AGENTS.md — Tiferet Streamlit (v0.2.0)

## Project Overview

**Tiferet Streamlit** is a Streamlit extension for the Tiferet framework, providing multi-page Streamlit application assembly with Domain-Driven Design. It offers blueprint functions for interface resolution, view lifecycle management, session-state-backed caching, and config-driven page routing.

- **Repository:** https://github.com/greatstrength/tiferet-streamlit
- **Branch:** `main`
- **Python:** ≥ 3.10
- **Version:** `0.2.0`
- **Dependencies:** `tiferet >= 2.0.0b3`, `streamlit >= 1.30.0`

## Architecture

### Package Layout

```
tiferet_streamlit/
├── __init__.py          — Version (0.2.0) and public exports
├── assets/              — Constants (error codes, session key prefix)
├── blueprints/          — Stateless blueprint functions (create_view, build_pages, build_streamlit_app, run)
├── contexts/            — Runtime contexts (ViewContext, ViewComponent, SessionCacheContext, PageContext)
├── domain/              — Domain objects (Page)
├── interfaces/          — Service interfaces (ViewService)
├── mappers/             — Mapper layer (reserved for future use)
├── repos/               — Repository layer (reserved for future use)
└── utils/               — Utilities (widgets)
```

### Key Concepts

- **Blueprint functions** (`blueprints/streamlit.py`): Stateless functions that assemble a Streamlit multi-page app. Functions: `create_view(view_cls, app, key, session)`, `build_pages(app, pages)`, `build_pages_from_config(app, page_configs)`, `build_streamlit_app(interface_id, pages, page_configs, **parameters)`, `run(interface_id, ...)`. `build_streamlit_app` is exported as the `StreamlitApp` alias.
- **ViewContext** (`contexts/view.py`): Page code-behind class. Manages state via `SessionCacheContext`, dispatches Tiferet features via `AppInterfaceContext`, and defines Streamlit UI through an overridable `render()` method. `init_state()` is called once on first construction.
- **ViewComponent** (`contexts/view.py`): Lightweight, prop-driven sub-component with parent `ViewContext` access. Callable via `__call__(**props)`.
- **SessionCacheContext** (`contexts/session.py`): Cache backed by `st.session_state` with namespace isolation. Extends `tiferet.contexts.cache.CacheContext`. Methods: `get(key)`, `set(key, value)`, `delete(key)`, `clear()`.
- **PageContext** (`contexts/page.py`): Multi-page navigation manager. `register_page(route, view, title, icon)` adds pages; `run()` builds `st.Page` objects and delegates to `st.navigation()`.
- **Page** (`domain/view.py`): Pydantic domain object for config-driven page metadata. Fields: `route`, `title`, `icon`, `layout`, `view_module_path`, `view_class_name`. `get_view_type()` dynamically imports the ViewContext class.
- **ViewService** (`interfaces/view.py`): Abstract service interface for page management (reserved for future repository-backed page loading).

### Runtime Flow

1. `StreamlitApp(interface_id, pages=..., page_configs=...)` (alias for `build_streamlit_app`) is called.
2. `resolve_interface(interface_id)` from `tiferet.blueprints.main` loads the app service and resolves the interface definition.
3. `realize_interface(app_interface, interface_id)` builds and validates the concrete `AppInterfaceContext`.
4. Pages are built via `build_pages_from_config(app, page_configs)` (if `page_configs` provided) or `build_pages(app, pages)` (if `pages` dict provided). Raises `PAGE_NOT_FOUND` error if neither is given.
5. Each page calls `create_view(view_cls, app, key)` which instantiates the `ViewContext` subclass with a `SessionCacheContext`.
6. `page_ctx.run()` builds `st.Page` objects and delegates to `st.navigation()` for Streamlit's multi-page routing.
7. When a page is selected, `ViewContext.__call__()` → `render()` executes the view's Streamlit UI.

### Configuration

Applications are configured via a consolidated YAML file (e.g., `config.yml`):

```yaml
interfaces:
  my_app:
    name: My App
    description: A Streamlit app powered by Tiferet

services:
  my_event:
    module_path: app.events.my_module
    class_name: MyEvent

features:
  my_group:
    my_feature:
      name: My Feature
      commands:
        - attribute_id: my_event
          name: Execute my event

errors:
  my_error:
    name: My Error
    message:
      - lang: en_US
        text: 'Something went wrong'
```

## Structured Code Style

All code follows tiferet v2 artifact comment conventions (`# ***`, `# **`, `# *`). See the [tiferet AGENTS.md](https://github.com/greatstrength/tiferet) for the full style guide.

## Testing

- **Framework:** `pytest`
- **Test location:** Co-located in `<package>/tests/` directories (e.g., `blueprints/tests/`, `contexts/tests/`, `domain/tests/`, `assets/tests/`).
- **Run tests:** `pytest tiferet_streamlit/ -v`
- **Patterns:**
  - Blueprint tests mock `resolve_interface` and `realize_interface` from `tiferet.blueprints.main`.
  - Context tests use `mock.patch('streamlit.session_state', {})` to isolate session state.
  - A `StubView(ViewContext)` helper provides a minimal testable view subclass.

## Key Files

- `tiferet_streamlit/__init__.py` — Version and public exports
- `tiferet_streamlit/blueprints/streamlit.py` — Blueprint functions (build_streamlit_app, create_view, build_pages, run)
- `tiferet_streamlit/contexts/view.py` — ViewContext and ViewComponent
- `tiferet_streamlit/contexts/session.py` — SessionCacheContext
- `tiferet_streamlit/contexts/page.py` — PageContext
- `tiferet_streamlit/domain/view.py` — Page domain object
- `tiferet_streamlit/assets/constants.py` — Error code constants

## Migration from v0.1.x

- **Builders → Blueprints:** The `StreamlitBuilder(AppBuilder)` class has been replaced by stateless blueprint functions in `blueprints/streamlit.py`. No more class instantiation or `load_app_service()` calls.
- **Imports:** `from tiferet_streamlit import StreamlitBuilder` → `from tiferet_streamlit import StreamlitApp` (or `build_streamlit_app`).
- **Usage:** `app = StreamlitApp(); app.load_app_service(); app.run(id, pages=...)` → `StreamlitApp(id, pages=...)` (single call).
- **Dependencies:** `tiferet>=2.0.0b1` → `tiferet>=2.0.0b3` (required for `tiferet.blueprints.main`).
- **Package layout:** `builders/` removed, replaced by `blueprints/`.
