# tiferet-streamlit

A Streamlit extension for the [Tiferet Framework](https://github.com/greatstrength/tiferet) — build multi-page Streamlit applications with Domain-Driven Design.

## Installation

```bash
pip install tiferet-streamlit
```

## Quick Start

```python
import streamlit as st
from tiferet_streamlit import StreamlitApp, ViewContext

class HomeView(ViewContext):
    def init_state(self):
        self.session.set('count', 0)

    def render(self):
        count = self.session.get('count')
        st.title('Home')
        st.write(f'Count: {count}')
        if st.button('Increment'):
            self.session.set('count', count + 1)
            st.rerun()

app = StreamlitApp()
app.load_app_service()
app.run('my_interface', pages={'/': HomeView})
```

## Core Concepts

### ViewContext

The code-behind for a Streamlit page. Manages state via `SessionCacheContext`, dispatches Tiferet features via `AppInterfaceContext`, and defines UI through `render()`.

- **`init_state()`** — Called once on first construction. Override to set initial state.
- **`dispatch(feature_id, headers=None, **data)`** — Execute a Tiferet feature.
- **`render()`** — Override to define Streamlit widgets.
- **`__call__()`** — Makes the view callable for `st.Page` composition.

### ViewComponent

A lightweight, prop-driven sub-component with parent `ViewContext` access.

```python
from tiferet_streamlit import ViewComponent

class Counter(ViewComponent):
    def render(self, label='Count', start=0):
        count = self.ctx.session.get('count') or start
        st.write(f'{label}: {count}')
```

### SessionCacheContext

Cache backed by `st.session_state` with namespace isolation for multi-page apps.

```python
from tiferet_streamlit import SessionCacheContext

cache = SessionCacheContext(namespace='my_view')
cache.set('key', 'value')
cache.get('key')  # 'value'
```

### Multi-Page Applications

Use `PageContext` to register multiple views with routes:

```python
app.run('my_interface', pages={
    '/': HomeView,
    '/about': AboutView,
    '/settings': SettingsView,
})
```

### Config-Driven Pages

Define pages as `Page` domain objects for YAML-driven configuration:

```python
from tiferet_streamlit import Page

pages = [
    Page(route='/', title='Home', icon='🏠',
         view_module_path='app.views.home', view_class_name='HomeView'),
    Page(route='/about', title='About', icon='ℹ️',
         view_module_path='app.views.about', view_class_name='AboutView'),
]

app.run('my_interface', page_configs=pages)
```

### Feature Dispatch

Views dispatch Tiferet features for backend logic:

```python
class CalcView(ViewContext):
    def render(self):
        a = st.number_input('a')
        b = st.number_input('b')
        if st.button('Add'):
            result = self.dispatch('calc.add', a=a, b=b)
            st.write(f'Result: {result}')
```

## API Reference

| Class | Module | Description |
|-------|--------|-------------|
| `Page` | `domain.view` | Page configuration domain object |
| `ViewService` | `interfaces.view` | Abstract service for page management |
| `SessionCacheContext` | `contexts.session` | Session-state-backed cache with namespacing |
| `ViewContext` | `contexts.view` | Page code-behind with lifecycle management |
| `ViewComponent` | `contexts.view` | Prop-driven sub-component |
| `PageContext` | `contexts.page` | Multi-page navigation manager |
| `StreamlitBuilder` | `builders.main` | Application entry point (also aliased as `StreamlitApp`) |

## Development

```bash
# Clone and set up
git clone https://github.com/greatstrength/tiferet-streamlit.git
cd tiferet-streamlit
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]

# Run tests
pytest --verbose
```

## License

MIT
