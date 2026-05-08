# ViewComponent Guide

## Overview

`ViewComponent` is a lightweight, prop-driven sub-component that accesses a parent `ViewContext` for state and feature dispatch. Analogous to a React functional component.

## Constructor

```python
ViewComponent(ctx)
```

- **`ctx`** — Parent `ViewContext` instance.

## Methods

### `render(**props)`
Define the component UI. Subclasses must override. Receives keyword arguments as props.

### `__call__(**props)`
Delegates to `render(**props)`. Makes the component callable.

## Usage Example

```python
import streamlit as st
from tiferet_streamlit import ViewComponent

class UserCard(ViewComponent):
    def render(self, name='Guest', role='User'):
        st.subheader(name)
        st.caption(role)
        if st.button(f'Greet {name}'):
            result = self.ctx.dispatch('greet.user', name=name)
            st.write(result)
```

### Using in a ViewContext

```python
class TeamView(ViewContext):
    def render(self):
        st.title('Team')
        card = UserCard(ctx=self)
        card(name='Alice', role='Engineer')
        card(name='Bob', role='Designer')
```

## Integration

- Components access parent state via `self.ctx.session`.
- Components dispatch features via `self.ctx.dispatch()`.
- Components are stateless by design — state lives in the parent `ViewContext`.
