# SessionCacheContext Guide

## Overview

`SessionCacheContext` bridges Tiferet's `CacheContext` with Streamlit's `st.session_state`. It supports namespaced keys to prevent collisions between views in multi-page applications.

## Constructor

```python
SessionCacheContext(namespace='')
```

- **`namespace`** — Optional prefix for key isolation. Keys are stored as `{namespace}.{key}`.

## Methods

### `get(key) -> Any`
Retrieve a value. Returns `None` if not found.

### `set(key, value)`
Store a value in session state.

### `delete(key)`
Remove a key. No error if absent.

### `clear()`
If namespaced, removes only keys with the namespace prefix. Otherwise clears all session state.

## Usage Example

```python
from tiferet_streamlit import SessionCacheContext

# Namespaced cache for a specific view
cache = SessionCacheContext(namespace='settings_view')
cache.set('theme', 'dark')
cache.get('theme')  # 'dark'

# Another view's cache is isolated
other = SessionCacheContext(namespace='home_view')
other.get('theme')  # None

# Clear only settings_view keys
cache.clear()
```

## Integration

- `ViewContext` auto-creates a `SessionCacheContext` with `namespace=key`.
- Pass a custom `SessionCacheContext` to `ViewContext` for shared state between views.
- Use without namespace for global session state access.
