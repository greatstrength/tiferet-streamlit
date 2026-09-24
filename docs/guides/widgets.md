# Widget Binding Guide

## Overview

Page code reads a session value, draws a widget, writes the value back, and then decides whether to dispatch. Widget binding collapses that sequence into one call on the view that already owns the session and the feature dispatch.

`bind_widget`, `bind_widget_dispatch`, and `bind_trigger` live on `ViewContext` and `ViewComponent`. They are not defined in `tiferet_streamlit/utils/widgets.py`, which stays a placeholder. The caller passes the widget callable, so these methods do not import Streamlit.

**Module:** `tiferet_streamlit/contexts/view.py`
**Vision:** See the `ViewContext` and `ViewComponent` class docstrings in `tiferet_streamlit/contexts/view.py` for the value statements this guide distills.

## Ubiquitous Language

- **Widget binding** — One call that draws a caller-supplied widget and applies the matching session or dispatch rule.
- **Value sync** — Read the stored value, pass it into the widget, and write the widget result back.
- **Change-triggered dispatch** — Call `dispatch` only when the widget result differs from the value stored before the call.
- **Truthy trigger** — Dispatch only when the widget result is truthy, without reading or writing session state.

## Value Sync

<a id="viewcontext-bind-widget"></a>
<a id="viewcomponent-bind-widget"></a>
**`bind_widget(key, widget, value_param='value', default=None, **kwargs) -> Any`**

Reads the stored value and passes it to the widget as `value_param`. Only `None` falls back to `default`, so a stored `0`, `False`, or `''` is kept. The widget result is written back and returned.

```python
name = self.bind_widget('name', st.text_input, default='')
```

## Change-Triggered Dispatch

<a id="viewcontext-bind-widget-dispatch"></a>
<a id="viewcomponent-bind-widget-dispatch"></a>
**`bind_widget_dispatch(key, widget, feature_id, value_param='value', default=None, dispatch_data=None, **kwargs) -> Any`**

Syncs the widget, then compares the result with the value read before the call. An equal value does not dispatch. A changed value dispatches once. With no `dispatch_data`, the payload is `{key: new_value}`. Otherwise `dispatch_data(new_value)` supplies the keywords.

```python
amount = self.bind_widget_dispatch(
    'amount',
    st.number_input,
    'calc.update',
    default=0,
)
```

## Truthy Trigger

<a id="viewcontext-bind-trigger"></a>
<a id="viewcomponent-bind-trigger"></a>
**`bind_trigger(widget, feature_id, dispatch_data=None, **kwargs) -> Any`**

Calls the widget and returns its result either way. A falsy result does not dispatch. A truthy result dispatches with `dispatch_data()` when that callable is given, otherwise with no extra keywords. Session state is not read or written.

```python
self.bind_trigger(st.button, 'data.load', label='Load')
```

`ViewComponent` exposes the same three methods. A component call uses the parent view's session and `dispatch`; the call site is still `self.bind_*`.

## Boundaries

**Inside this domain:** Binding a caller-supplied widget callable to a view session and, when asked, to that view's `dispatch`.
**Outside this domain:** Drawing widgets (Streamlit), running the feature (`ViewContext.dispatch`), and any widget catalog (`tiferet_streamlit/utils/widgets.py` remains a placeholder and defines no `bind_*` function).

## Related Documentation

- [ViewContext Guide](view_context.md) — Page code-behind that owns session state and feature dispatch
- [ViewComponent Guide](view_component.md) — Prop-driven sub-component that delegates to a parent view
