# tiferet-streamlit

A Streamlit UI extension for the [Tiferet](https://github.com/greatstrength/tiferet) framework. Build structured, domain-driven Streamlit applications with composable views, session-backed state management, and Tiferet's feature dispatch system.

## Installation

```bash
pip install tiferet-streamlit
```

Requires Python 3.10+ and installs `tiferet>=2.0.0b1` and `streamlit>=1.30.0` automatically.

## Quick Start

### 1. Set Up Your Tiferet App

Create a standard Tiferet project structure with your domain events and configuration:

```
project_root/
├── app.py
└── app/
    └── configs/
        ├── app.yml
        ├── container.yml
        ├── error.yml
        └── feature.yml
```

Define a Streamlit interface in `app/configs/app.yml`:

```yaml
interfaces:
  my_app:
    name: My Streamlit App
    description: A Streamlit app powered by Tiferet
```

### 2. Create a View

A `ViewContext` is the code-behind for a Streamlit page. It manages state, dispatches Tiferet features, and renders widgets:

```python
# views.py
import streamlit as st
from tiferet_streamlit import ViewContext

class HomeView(ViewContext):

    def init_state(self):
        """Called once on first render. Set initial state here."""
        self.session.set('greeting', 'Hello, Tiferet!')

    def render(self):
        """Called on every Streamlit rerun. Define your UI here."""
        st.title(self.session.get('greeting'))

        name = st.text_input('Your name', key=f'{self.key}.name')
        if st.button('Greet', key=f'{self.key}.greet'):
            self.session.set('greeting', f'Hello, {name}!')
            st.rerun()
```

### 3. Run the App

```python
# app.py
from tiferet_streamlit import StreamlitApp
from views import HomeView

app = StreamlitApp()
app.load_app_service()
app.run('my_app', pages={
    'home': HomeView,
})
```

Launch with:

```bash
streamlit run app.py
```

## Core Concepts

### ViewContext — The Code-Behind

`ViewContext` is the central abstraction, analogous to a React class component. Each view has:

- **State** — managed via `self.session` (a `SessionCacheContext`), persists across Streamlit reruns.
- **Actions** — dispatch Tiferet features via `self.dispatch(feature_id, **data)`.
- **Rendering** — override `render()` to define Streamlit widgets.
- **Lifecycle** — `init_state()` runs once on first render; `render()` runs on every rerun.

```python
class CalculatorView(ViewContext):

    def init_state(self):
        self.session.set('result', None)

    def render(self):
        a = st.number_input('A', key=f'{self.key}.a')
        b = st.number_input('B', key=f'{self.key}.b')

        if st.button('Add', key=f'{self.key}.add'):
            result = self.dispatch('calc.add', a=a, b=b)
            self.session.set('result', result)

        result = self.session.get('result')
        if result is not None:
            st.success(f'Result: {result}')
```

### ViewComponent — Composable Sub-Components

`ViewComponent` is a lighter-weight, prop-driven abstraction for reusable UI pieces. It accesses a parent `ViewContext` for state and actions:

```python
from tiferet_streamlit import ViewComponent

class NumberInput(ViewComponent):

    def render(self, label: str, state_key: str):
        value = st.number_input(label, key=f'{self.ctx.key}.{state_key}')
        self.ctx.session.set(state_key, value)


class CalculatorView(ViewContext):

    def render(self):
        NumberInput(self)(label='A', state_key='a')
        NumberInput(self)(label='B', state_key='b')

        if st.button('Add', key=f'{self.key}.add'):
            result = self.dispatch('calc.add',
                a=self.session.get('a'),
                b=self.session.get('b'))
            self.session.set('result', result)
```

### SessionCacheContext — State Bridge

`SessionCacheContext` bridges Streamlit's `st.session_state` with Tiferet's `CacheContext` interface. It supports namespaced keys to isolate state between views:

```python
from tiferet_streamlit import SessionCacheContext

# Global session
session = SessionCacheContext()
session.set('user', 'Alice')
session.get('user')  # 'Alice'

# Namespaced session (used automatically by ViewContext)
view_session = SessionCacheContext(namespace='calculator')
view_session.set('result', 42)
# Stored as 'calculator.result' in st.session_state
```

### Multi-Page Apps

Register multiple `ViewContext` subclasses as pages. The `StreamlitBuilder` handles navigation via `st.navigation`:

```python
from tiferet_streamlit import StreamlitApp
from views import HomeView, CalculatorView, SettingsView

app = StreamlitApp()
app.load_app_service()
app.run('my_app', pages={
    'home': HomeView,
    'calculator': CalculatorView,
    'settings': SettingsView,
})
```

### Configuration-Driven Pages

Pages can also be defined as `Page` domain objects for YAML-driven configuration:

```python
from tiferet_streamlit import StreamlitApp, Page

page_configs = [
    Page(
        route='home',
        title='Home',
        icon=':house:',
        view_module_path='views',
        view_class_name='HomeView',
    ),
    Page(
        route='calculator',
        title='Calculator',
        icon=':abacus:',
        layout='wide',
        view_module_path='views',
        view_class_name='CalculatorView',
    ),
]

app = StreamlitApp()
app.load_app_service()
app.run('my_app', page_configs=page_configs)
```

### Dispatching Tiferet Features

The `dispatch()` method on `ViewContext` executes Tiferet features defined in your `feature.yml` configuration:

```python
# In your ViewContext subclass:
result = self.dispatch('calc.add', a=1, b=2)
```

This calls `AppInterfaceContext.run()` under the hood, executing the feature's domain event pipeline and returning the result. All your domain logic stays in Tiferet events — views only handle rendering and user interaction.

## API Reference

| Export | Module | Description |
|---|---|---|
| `StreamlitBuilder` / `StreamlitApp` | `builders.main` | App entry point, extends Tiferet's `AppBuilder` |
| `ViewContext` | `contexts.view` | Code-behind base class for views |
| `ViewComponent` | `contexts.view` | Composable prop-driven sub-component |
| `SessionCacheContext` | `contexts.session` | `st.session_state` ↔ `CacheContext` bridge |
| `PageContext` | `contexts.page` | Multi-page navigation manager |
| `Page` | `domain.view` | Domain object for page metadata |
| `ViewService` | `interfaces.view` | Abstract service contract for view operations |

## Development

```bash
# Clone and set up
git clone https://github.com/greatstrength/tiferet-streamlit.git
cd tiferet-streamlit
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e .[test]

# Run tests
pytest --verbose
```

## License

BSD-3-Clause
