# Widget Binding Helpers Guide

## Overview

`ViewContext.bind_widget`, `bind_widget_dispatch`, and `bind_trigger` bind a native Streamlit widget's value to the view's own `SessionCacheContext` and, optionally, dispatch a Tiferet feature when that value changes — replacing the hand-wired read/draw/write/dispatch pattern every widget would otherwise repeat. This is a thin data-binding/dispatch convenience layer over Streamlit's own widgets, not a widget catalog and not a custom Components-API widget.

Three methods cover the interaction models Streamlit widgets expose:

- **`bind_widget`** — value-sync only.
- **`bind_widget_dispatch`** — value-sync plus change-triggered dispatch.
- **`bind_trigger`** — unconditional dispatch for click-style widgets.

All three live on `ViewContext`. `ViewComponent` exposes identically-signed methods that delegate to `self.ctx`, so a component author calls `self.bind_widget(...)` the same way a view author calls `self.bind_widget(...)` — no duck-typing or type-branching needed, since each method already lives on the class whose state (`self.session`, `self.dispatch`) it uses.

## Methods

### `bind_widget(key, widget, value_param='value', default=None, **kwargs) -> Any`

Reads the value stored at `key` (or `default` if unset), passes it to `widget` under the `value_param` keyword, and writes the widget's return value back to `key`. Any extra `kwargs` are forwarded to `widget` untouched.

Use `value_param` to match widgets that don't seed their current value via `value=` (e.g. pass `value_param='index'` for `st.selectbox`).

### `bind_widget_dispatch(key, widget, feature_id, value_param='value', default=None, dispatch_data=None, **kwargs) -> Any`

Composes `bind_widget` with a change comparison: the value stored at `key` is captured *before* the widget renders on this rerun, and `self.dispatch(feature_id, ...)` is only called when the synced value differs from that captured value. This avoids dispatching once per script rerun instead of once per real user action.

The dispatch payload defaults to `{key: new_value}`. Pass `dispatch_data=lambda value: {...}` to supply a different shape.

### `bind_trigger(widget, feature_id, dispatch_data=None, **kwargs) -> Any`

For click-style widgets (`st.button`, `st.form_submit_button`) that have no persisted value to compare against. Dispatches `self.dispatch(feature_id, ...)` unconditionally whenever `widget(**kwargs)` returns truthy. Writes nothing to the session cache.

The dispatch payload defaults to `{}`. Pass `dispatch_data=lambda: {...}` to supply arguments.

## Usage Example

Replacing the README Quick Start's hand-wired counter:

```python
import streamlit as st
from tiferet_streamlit import ViewContext

class HomeView(ViewContext):
    def init_state(self):
        self.session.set('count', 0)

    def render(self):
        st.title('Home')
        st.write(f"Count: {self.session.get('count')}")
        if self.bind_trigger(st.button, 'counter.increment', label='Increment'):
            self.session.set('count', self.session.get('count') + 1)
```

Replacing the README Feature Dispatch calculator, with dispatch only firing when an input actually changes:

```python
import streamlit as st
from tiferet_streamlit import ViewContext

class CalcView(ViewContext):
    def render(self):
        a = self.bind_widget_dispatch('a', st.number_input, 'calc.add', label='a')
        b = self.bind_widget_dispatch('b', st.number_input, 'calc.add', label='b')
        st.write(f'a={a}, b={b}')
```

Using the methods from a `ViewComponent` works identically, since they delegate to `self.ctx`:

```python
from tiferet_streamlit import ViewComponent

class NameField(ViewComponent):
    def render(self, label='Name', **props):
        return self.bind_widget('name', st.text_input, default='', label=label, **props)
```

## Integration

- Methods only read/write through the `SessionCacheContext` the view/component already owns (`self.session`) — they create no new cache, namespace, or global state, and require no bootstrap-time seeding.
- Methods accept any native Streamlit widget callable and forward widget-specific keyword arguments untouched; they do not reimplement, subclass, or wrap individual widget types. No widget configuration, catalog, or domain object is introduced.
- No module or subpackage beyond `ViewContext`/`ViewComponent` is required to use the methods on an existing view.
