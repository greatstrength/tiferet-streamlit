# ViewContext Guide

**Module:** `tiferet_streamlit.contexts.view`
**Import:** `from tiferet_streamlit import ViewContext`

## Overview

`ViewContext` is the central abstraction in tiferet-streamlit — the "code-behind" for a Streamlit page. It bridges Tiferet's domain-driven feature system with Streamlit's rerun-based UI model, providing structured state management, feature dispatch, and a clear rendering lifecycle.

Think of it as a React class component: it has state, actions, and a render method.

## Lifecycle

### `init_state()`

Called **once**, on first render. Use it to set initial session values:

```python
class MyView(ViewContext):
    def init_state(self):
        self.session.set('count', 0)
        self.session.set('error', None)
```

The framework tracks initialization via a `_initialized` flag in session state, so `init_state()` will not run again on subsequent Streamlit reruns — even though the `ViewContext` is re-constructed each time.

### `render()`

Called on **every** Streamlit rerun. This is where you define your UI:

```python
class MyView(ViewContext):
    def render(self):
        st.title('My Page')
        count = self.session.get('count')
        st.write(f'Count: {count}')
```

You **must** override `render()` — the base class raises `NotImplementedError`.

## State Management

Each `ViewContext` has a `self.session` attribute — a `SessionCacheContext` namespaced to the view's key. This prevents state collisions between views:

```python
# In a view with key='calculator':
self.session.set('result', 42)
# Stored as 'calculator.result' in st.session_state
```

### Widget State vs. Session State

Streamlit widgets own their state via their `key` parameter. You **cannot** write back to a widget's key after the widget is instantiated. Use `self.session` for non-widget state (results, errors, flags) and read widget values directly from `st.session_state`:

```python
def render(self):
    st.number_input('A', key=f'{self.key}.a')

    if st.button('Go'):
        # Read widget value directly — don't use self.session for widget keys
        a = st.session_state.get(f'{self.key}.a', 0)
        result = self.dispatch('calc.sqrt', a=a)
        # Store result in session (non-widget state)
        self.session.set('result', result)
```

## Dispatching Features

`dispatch()` executes a Tiferet feature by ID and returns the result:

```python
result = self.dispatch('calc.add', a=1, b=2)
```

This calls `AppInterfaceContext.run()` under the hood, executing the feature's domain event pipeline. You can also pass custom headers:

```python
result = self.dispatch('calc.add', headers={'lang': 'es_ES'}, a=1, b=2)
```

## Key Attributes

- `self.app` — the `AppInterfaceContext` for feature execution
- `self.key` — the unique view identifier (used for widget key namespacing)
- `self.session` — the `SessionCacheContext` for persistent state

## Callable Interface

`ViewContext` implements `__call__`, delegating to `render()`. This makes it compatible with `st.Page` and other Streamlit APIs that expect a callable:

```python
view = MyView(app=interface, key='home')
view()  # same as view.render()
```

## Full Example

```python
import streamlit as st
from tiferet_streamlit import ViewContext
from tiferet import TiferetError

class CalculatorView(ViewContext):

    def init_state(self):
        self.session.set('result', None)
        self.session.set('error', None)

    def render(self):
        st.header('Calculator')

        st.number_input('A', key=f'{self.key}.a')
        st.number_input('B', key=f'{self.key}.b')

        if st.button('Add'):
            a = st.session_state.get(f'{self.key}.a', 0)
            b = st.session_state.get(f'{self.key}.b', 0)
            try:
                result = self.dispatch('calc.add', a=a, b=b)
                self.session.set('result', result)
                self.session.set('error', None)
            except TiferetError as e:
                self.session.set('error', str(e))

        result = self.session.get('result')
        error = self.session.get('error')

        if error:
            st.error(error)
        elif result is not None:
            st.success(f'Result: {result}')
```

## Testing

Mock the `AppInterfaceContext` and `st.session_state` in tests:

```python
from unittest import mock
from tiferet_streamlit import ViewContext

class StubView(ViewContext):
    def init_state(self):
        self.session.set('ready', True)
    def render(self):
        pass

def test_init_state():
    with mock.patch('streamlit.session_state', {}):
        app = mock.MagicMock()
        view = StubView(app=app, key='test')
        assert view.session.get('ready') is True
```
