# ViewComponent Guide

**Module:** `tiferet_streamlit.contexts.view`
**Import:** `from tiferet_streamlit import ViewComponent`

## Overview

`ViewComponent` is a lightweight, composable abstraction for reusable UI pieces — analogous to a React functional component. It receives props, accesses a parent `ViewContext` for state and actions, and renders Streamlit widgets.

Use `ViewComponent` when you want to extract a reusable piece of UI that multiple views can share.

## Structure

A `ViewComponent` has:

- `self.ctx` — the parent `ViewContext`, providing access to session state and feature dispatch
- `render(**props)` — the method you override to define widgets
- `__call__(**props)` — callable shorthand that delegates to `render()`

```python
from tiferet_streamlit import ViewComponent

class Greeting(ViewComponent):
    def render(self, name: str = 'World'):
        st.write(f'Hello, {name}!')
```

## Usage

Instantiate with a parent `ViewContext`, then call with props:

```python
class MyView(ViewContext):
    def render(self):
        Greeting(self)(name='Tiferet')
        # or equivalently:
        greeting = Greeting(self)
        greeting.render(name='Tiferet')
```

## Accessing State and Actions

Components access the parent view's session and dispatch through `self.ctx`:

```python
class ResultDisplay(ViewComponent):
    def render(self, **props):
        result = self.ctx.session.get('result')
        if result is not None:
            st.success(f'Result: {result}')

class ActionButton(ViewComponent):
    def render(self, label: str, feature_id: str, **data):
        if st.button(label, key=f'{self.ctx.key}.{label.lower()}'):
            result = self.ctx.dispatch(feature_id, **data)
            self.ctx.session.set('result', result)
```

## Widget Keys

Always namespace widget keys using `self.ctx.key` to avoid collisions:

```python
class NumberInput(ViewComponent):
    def render(self, label: str, state_key: str):
        st.number_input(label, key=f'{self.ctx.key}.{state_key}')

    @staticmethod
    def get_widget_value(ctx, state_key: str):
        '''Read the widget value from st.session_state.'''
        return st.session_state.get(f'{ctx.key}.{state_key}', 0.0)
```

Note the static helper pattern: since Streamlit widgets own their state, provide a `get_widget_value()` method to read values without conflicting with Streamlit's state model.

## Composition

Components can compose other components:

```python
class FormRow(ViewComponent):
    def render(self, label_a: str, label_b: str):
        col1, col2 = st.columns(2)
        with col1:
            NumberInput(self.ctx)(label=label_a, state_key='a')
        with col2:
            NumberInput(self.ctx)(label=label_b, state_key='b')
```

## Full Example

```python
import streamlit as st
from tiferet_streamlit import ViewContext, ViewComponent

class NumberInput(ViewComponent):
    def render(self, label: str, state_key: str, default: float = 0.0):
        st.number_input(label, value=default, step=1.0,
                        key=f'{self.ctx.key}.{state_key}')

    @staticmethod
    def get_widget_value(ctx, state_key: str):
        return st.session_state.get(f'{ctx.key}.{state_key}', 0.0)

class ResultDisplay(ViewComponent):
    def render(self, **props):
        result = self.ctx.session.get('result')
        error = self.ctx.session.get('error')
        if error:
            st.error(error)
        elif result is not None:
            st.success(f'Result: {result}')

class CalculatorView(ViewContext):
    def init_state(self):
        self.session.set('result', None)
        self.session.set('error', None)

    def render(self):
        NumberInput(self)(label='A', state_key='a')
        NumberInput(self)(label='B', state_key='b')

        if st.button('Add', key=f'{self.key}.add'):
            a = NumberInput.get_widget_value(self, 'a')
            b = NumberInput.get_widget_value(self, 'b')
            result = self.dispatch('calc.add', a=a, b=b)
            self.session.set('result', result)

        ResultDisplay(self)()
```

## Testing

```python
from unittest import mock
from tiferet_streamlit import ViewContext, ViewComponent

class TrackingComponent(ViewComponent):
    def render(self, label: str = 'default', **props):
        self.ctx.session.set(f'rendered_{label}', True)

def test_component_renders():
    with mock.patch('streamlit.session_state', {}):
        app = mock.MagicMock()
        class StubView(ViewContext):
            def render(self): pass
        view = StubView(app=app, key='test')
        TrackingComponent(view)(label='btn')
        assert view.session.get('rendered_btn') is True
```
