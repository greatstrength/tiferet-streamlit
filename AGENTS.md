# AGENTS.md — Tiferet Streamlit (v1.0.0a8)

## Project Overview

**Tiferet Streamlit** is a Streamlit extension for the Tiferet framework, providing multi-page Streamlit application assembly with Domain-Driven Design. It offers blueprint functions for app assembly, view lifecycle management with dispatch audit logging and widget binding, session-state-backed caching, config-driven page routing (including a `ViewService`-backed configuration store), and config-driven theming.

- **Repository:** https://github.com/greatstrength/tiferet-streamlit
- **Branch:** `main` (trunk) / `v1.x-proto` (prototype strand, currently ahead of trunk)
- **Python:** ≥ 3.10
- **Version:** `1.0.0a8`
- **Dependencies:** `tiferet >= 2.0.3`, `streamlit >= 1.30.0`, `toml >= 0.10`

## Architecture

### Package Layout

```
tiferet_streamlit/
├── __init__.py          — Version and public exports
├── assets/              — Constants (error codes, session key prefix, service ID)
├── blueprints/          — Stateless blueprint functions (create_view, build_pages, build_streamlit_app, run)
├── contexts/            — Runtime contexts (ViewContext, ViewComponent, SessionCacheContext, PageContext, get_view_service)
├── domain/              — Domain objects (Page, DispatchAuditRecord, Theme)
├── interfaces/          — Service interfaces (ViewService)
├── mappers/             — Mapper layer (reserved for future use)
├── repos/               — Repository layer (ViewYamlRepository, a YAML-backed ViewService implementation)
└── utils/               — Utilities (widgets.py is currently a placeholder; widget binding lives on ViewContext/ViewComponent — see Key Concepts)
```

### Key Concepts

- **Blueprint functions** (`blueprints/streamlit.py`): Stateless functions that assemble a Streamlit multi-page app. Functions: `create_view(view_cls, app, key, session)`, `build_pages(app, pages)`, `build_pages_from_config(app, page_configs)`, `build_streamlit_app(interface_id, pages, page_configs, get_page_configs, theme, **parameters)`, `run(interface_id, ...)`. `build_streamlit_app` is exported as the `StreamlitApp` alias. Blueprints never import service interfaces (e.g. `ViewService`) directly — `get_page_configs` is a caller-supplied `Callable[[AppSessionContext], List[Page]]` handler, letting a DI-resolved source plug in (see `get_view_service` below) without the blueprint layer holding any service reference.
- **ViewContext** (`contexts/view.py`): Page code-behind class. Manages state via `SessionCacheContext`, dispatches Tiferet features via `AppSessionContext` (every `dispatch()` call — success or failure — is recorded to an in-session audit log), and defines Streamlit UI through an overridable `render()` method. `init_state()` is called once on first construction. `bind_widget`/`bind_widget_dispatch`/`bind_trigger` sync a native Streamlit widget's value to session state and optionally dispatch a feature on change.
- **ViewComponent** (`contexts/view.py`): Lightweight, prop-driven sub-component with parent `ViewContext` access. Callable via `__call__(**props)`. Exposes the same `bind_widget`/`bind_widget_dispatch`/`bind_trigger` methods, delegating to `self.ctx`.
- **SessionCacheContext** (`contexts/session.py`): Cache backed by `st.session_state` with namespace isolation. Extends `tiferet.contexts.cache.CacheContext`. Methods: `get(key)`, `set(key, value)`, `delete(key)`, `clear()`.
- **PageContext** (`contexts/page.py`): Multi-page navigation manager. `register_page(route, view, title, icon)` adds pages; `run()` builds `st.Page` objects and delegates to `st.navigation()`.
- **Page** (`domain/view.py`): Pydantic domain object for config-driven page metadata. Fields: `route`, `title`, `icon`, `layout`, `view_module_path`, `view_class_name`. `get_view_type()` dynamically imports the ViewContext class, raising a structured `INVALID_VIEW_TYPE_ID` error (not a raw import exception) on a bad path or class name.
- **Theme** (`domain/theme.py`): Pydantic domain object declaring an app's appearance as data — native `[theme]` fields (`base`, `primary_color`, `background_color`, `secondary_background_color`, `text_color`, `font`) plus `custom_css`. Applied via `apply_theme_config()` (writes into `.streamlit/config.toml`'s `[theme]` section, effective on the next process start) and `inject_theme_css()` (immediate, every rerun).
- **DispatchAuditRecord** (`domain/audit.py`): Pydantic domain object recording a single `dispatch()` outcome (`feature_id`, `arguments`, `outcome`, `result`). Read back via `ViewContext.audit_log`.
- **ViewService** (`interfaces/view.py`): Abstract service interface for page management, implemented by `ViewYamlRepository` (`repos/view.py`), a YAML-backed repository. Never imported directly by blueprints — reached only via `get_view_service`.
- **get_view_service** (`contexts/di.py`): DI-mediated accessor that resolves a `ViewService` dependency by configuration ID (`app.get_dependency(service_id, *flags)`) and verifies the resolved object actually implements `ViewService`, raising `INVALID_VIEW_SERVICE_ID` otherwise. This is the sole sanctioned path to a `ViewService` instance.
- **is_app_context_compatible** (`blueprints/streamlit.py`): Duck-type check confirming the app object `build_app()` constructed exposes a `run(feature_id, headers, data)`-shaped callable. Runs at `build_streamlit_app()` assembly time, raising `INCOMPATIBLE_APP_CONTEXT_ID` on mismatch instead of letting an unstructured error surface later from inside `dispatch()`.

### Runtime Flow

1. `StreamlitApp(interface_id, pages=..., page_configs=..., theme=...)` (alias for `build_streamlit_app`) is called.
2. If a `theme` is declared, `apply_theme_config()` and `inject_theme_css()` run first.
3. `tiferet.blueprints.app.build_app(interface_id, **parameters)` constructs the fully resolved `AppSessionContext` in a single call.
4. `is_app_context_compatible(app)` verifies the constructed app exposes the expected `run()` shape before any page renders.
5. Pages are built via `build_pages_from_config(app, page_configs)` (if `page_configs` provided), `build_pages(app, pages)` (if `pages` dict provided), or `build_pages_from_config(app, get_page_configs(app))` (if a `get_page_configs` handler is provided, e.g. one backed by `get_view_service(app).list_pages()`). Raises `PAGE_NOT_FOUND_ID` if none is given.
6. Each page calls `create_view(view_cls, app, key)` which instantiates the `ViewContext` subclass with a `SessionCacheContext`.
7. `page_ctx.run()` builds `st.Page` objects and delegates to `st.navigation()` for Streamlit's multi-page routing.
8. When a page is selected, `ViewContext.__call__()` → `render()` executes the view's Streamlit UI, with any exception from a concrete `render()` wrapped into a structured `VIEW_RENDER_FAILED_ID` error (chained via `raise ... from`) carrying the view's key.

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
- **Test location:** Co-located in `<package>/tests/` directories (e.g., `blueprints/tests/`, `contexts/tests/`, `domain/tests/`, `assets/tests/`, `repos/tests/`).
- **Run tests:** `pytest tiferet_streamlit/ -v`
- **Patterns:**
  - Blueprint tests mock `tiferet.blueprints.app.build_app`.
  - Context tests use `mock.patch('streamlit.session_state', {})` to isolate session state.
  - A `StubView(ViewContext)` helper provides a minimal testable view subclass.

## Key Files

- `tiferet_streamlit/__init__.py` — Version and public exports
- `tiferet_streamlit/blueprints/streamlit.py` — Blueprint functions (build_streamlit_app, create_view, build_pages, build_pages_from_config, apply_theme_config, inject_theme_css, run)
- `tiferet_streamlit/contexts/view.py` — ViewContext, ViewComponent, and the widget-binding helpers
- `tiferet_streamlit/contexts/session.py` — SessionCacheContext
- `tiferet_streamlit/contexts/page.py` — PageContext
- `tiferet_streamlit/contexts/di.py` — get_view_service
- `tiferet_streamlit/domain/view.py` — Page domain object
- `tiferet_streamlit/domain/theme.py` — Theme domain object
- `tiferet_streamlit/domain/audit.py` — DispatchAuditRecord domain object
- `tiferet_streamlit/interfaces/view.py` — ViewService interface
- `tiferet_streamlit/repos/view.py` — ViewYamlRepository
- `tiferet_streamlit/assets/constants.py` — Error code constants

## Migration Notes

- **v0.1.x → v0.2.0 (Builders → Blueprints):** The `StreamlitBuilder(AppBuilder)` class was replaced by stateless blueprint functions in `blueprints/streamlit.py`. `from tiferet_streamlit import StreamlitBuilder` → `from tiferet_streamlit import StreamlitApp` (or `build_streamlit_app`). `app = StreamlitApp(); app.load_app_service(); app.run(id, pages=...)` → `StreamlitApp(id, pages=...)` (single call). `builders/` removed, replaced by `blueprints/`.
- **v0.2.0 → v1.0.0b1 prototype round (AppInterfaceContext → AppSessionContext):** `tiferet>=2.0.3` replaced `tiferet.blueprints.main`'s `resolve_interface`/`realize_interface` with `tiferet.blueprints.app.build_app(interface_id, ...) -> AppSessionContext`. `ViewContext.app` is now typed as `AppSessionContext`; `dispatch()`'s call shape (`run(feature_id, headers, data)`) is unchanged. This round also added widget binding (`bind_widget`/`bind_widget_dispatch`/`bind_trigger`), dispatch audit logging (`audit_log`), config-driven theming (`Theme`), a `ViewService`-backed page configuration store (`ViewYamlRepository`, `get_view_service`), and `VIEW_RENDER_FAILED_ID`/`INCOMPATIBLE_APP_CONTEXT_ID` structured error handling.

## Contributing

See `CONTRIBUTING.md` for the full workflow, including RFP authoring/implementation on the prototype strand and TRD-based reconstruction on trunk.
