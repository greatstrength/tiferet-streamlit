# ViewContext Guide

## Overview

`ViewContext` is the code-behind for a Streamlit page. It manages state via `SessionCacheContext`, dispatches Tiferet features via `AppInterfaceContext`, and defines Streamlit widgets through an overridable `render()` method.

## Constructor

```python
ViewContext(app, key, session=None)
```

- **`app`** — Tiferet `AppInterfaceContext` for feature dispatch.
- **`key`** — Unique identifier for this view (used as session namespace).
- **`session`** — Optional `SessionCacheContext`. Auto-created with `namespace=key` if not provided.

## Lifecycle

1. **Construction** — `__init__` sets `app`, `key`, and `session`. Calls `init_state()` once (guarded by `_initialized` flag).
2. **State Initialization** — Override `init_state()` to set default session values.
3. **Rendering** — Streamlit calls `render()` (or `__call__()`) on each rerun.

## Methods

### `init_state()`
Called once on first construction. Override to set initial state values. No-op by default.

### `dispatch(feature_id, headers=None, **data)`
Execute a Tiferet feature. Returns the feature result.

### `render()`
Define the Streamlit UI. Subclasses must override. Raises `NotImplementedError` by default.

### `__call__()`
Delegates to `render()`. Makes the view callable for `st.Page` composition.

## Usage Example

```python
import streamlit as st
from tiferet_streamlit import ViewContext

class DashboardView(ViewContext):
    def init_state(self):
        self.session.set('data', [])

    def render(self):
        st.title('Dashboard')
        data = self.session.get('data')
        if st.button('Load Data'):
            result = self.dispatch('data.load')
            self.session.set('data', result)
            st.rerun()
        st.dataframe(data)
```

## Integration

- Register views with `PageContext` or `StreamlitBuilder` for multi-page apps.
- Use `ViewComponent` for reusable sub-components within a view.
- Access session state via `self.session` (a `SessionCacheContext` instance).
