# SessionCacheContext Guide

**Module:** `tiferet_streamlit.contexts.session`
**Import:** `from tiferet_streamlit import SessionCacheContext`

## Overview

`SessionCacheContext` bridges Streamlit's `st.session_state` with Tiferet's `CacheContext` interface. It is a drop-in replacement for `CacheContext` in the DI graph, enabling all Tiferet contexts to use Streamlit's persistence transparently.

## Basic Usage

```python
from tiferet_streamlit import SessionCacheContext

session = SessionCacheContext()
session.set('user', 'Alice')
session.get('user')      # 'Alice'
session.delete('user')
session.get('user')      # None
session.clear()          # removes everything
```

## Namespacing

Namespaces prevent key collisions between views. Each `ViewContext` automatically creates a `SessionCacheContext` with its view key as namespace:

```python
# Two views with different namespaces
view_a = SessionCacheContext(namespace='calculator')
view_b = SessionCacheContext(namespace='settings')

view_a.set('count', 10)
view_b.set('count', 20)

view_a.get('count')  # 10
view_b.get('count')  # 20
```

Under the hood, keys are prefixed: `calculator.count` and `settings.count` in `st.session_state`.

### Namespaced `clear()`

`clear()` only removes keys belonging to the namespace:

```python
view_a = SessionCacheContext(namespace='view_a')
view_b = SessionCacheContext(namespace='view_b')

view_a.set('x', 1)
view_b.set('y', 2)

view_a.clear()
# view_a.get('x') → None
# view_b.get('y') → 2 (untouched)
```

A `SessionCacheContext` with no namespace (or `namespace=''`) operates on the global `st.session_state` directly.

## Widget State vs. Session State

This is the most important distinction in tiferet-streamlit:

- **Widget state** — owned by Streamlit widgets via their `key` parameter. You **cannot** write to these keys after the widget is instantiated.
- **Session state** — managed by `SessionCacheContext`. Use for non-widget values like computation results, error messages, flags, and any data that doesn't directly back a widget.

```python
# WRONG — will raise StreamlitAPIException
st.number_input('A', key='calculator.a')
self.session.set('a', 42)  # ← Error: can't modify widget key

# RIGHT — use session for non-widget state
st.number_input('A', key=f'{self.key}.a')
if st.button('Compute'):
    a = st.session_state.get(f'{self.key}.a', 0)  # read widget value
    result = self.dispatch('calc.sqrt', a=a)
    self.session.set('result', result)  # store in session (non-widget)
```

## API

| Method | Description |
|---|---|
| `get(key)` | Retrieve a value, or `None` if not found |
| `set(key, value)` | Store a value |
| `delete(key)` | Remove a key (safe if nonexistent) |
| `clear()` | Remove all keys in this namespace |

## Complex Values

Session state can store any Python object — dicts, lists, domain models:

```python
session.set('data', {'items': [1, 2, 3], 'nested': {'a': True}})
result = session.get('data')  # {'items': [1, 2, 3], 'nested': {'a': True}}
```

## Testing

Mock `st.session_state` with a plain dict:

```python
from unittest import mock
from tiferet_streamlit import SessionCacheContext

def test_namespaced_isolation():
    with mock.patch('streamlit.session_state', {}):
        a = SessionCacheContext(namespace='a')
        b = SessionCacheContext(namespace='b')
        a.set('x', 1)
        b.set('x', 2)
        assert a.get('x') == 1
        assert b.get('x') == 2
```
