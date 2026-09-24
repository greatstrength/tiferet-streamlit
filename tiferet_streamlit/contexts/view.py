'''Tiferet Streamlit – View Contexts'''

# *** imports

# ** core
from typing import Any, Callable, Dict, List

# ** infra
from tiferet import TiferetError
from tiferet.contexts.app import AppSessionContext

# ** app
from ..assets.constants import VIEW_RENDER_FAILED_ID
from ..domain import DispatchAuditRecord
from .session import SessionCacheContext

# *** functions

# ** function: _bind_widget
def _bind_widget(
        session: SessionCacheContext,
        key: str,
        widget: Callable,
        value_param: str = 'value',
        default: Any = None,
        **kwargs,
    ) -> Any:
    '''
    Sync a widget value with session state.

    :param session: Session cache that stores the widget value.
    :type session: SessionCacheContext
    :param key: Session key for the stored value.
    :type key: str
    :param widget: Callable that draws the widget and returns its value.
    :type widget: Callable
    :param value_param: Keyword passed to the widget as the current value.
    :type value_param: str
    :param default: Value used when the session key is missing.
    :type default: Any
    :param kwargs: Additional keyword arguments forwarded to the widget.
    :type kwargs: dict
    :return: The value returned by the widget.
    :rtype: Any
    '''

    # Read the stored value.
    current = session.get(key)

    # Fall back to the default only when the stored value is None.
    if current is None:
        current = default

    # Pass the current value into the widget and draw it.
    kwargs[value_param] = current
    new_value = widget(**kwargs)

    # Write the widget result back.
    session.set(key, new_value)

    # Return the widget result.
    return new_value

# ** function: _bind_widget_dispatch
def _bind_widget_dispatch(
        session: SessionCacheContext,
        dispatch: Callable,
        key: str,
        widget: Callable,
        feature_id: str,
        value_param: str = 'value',
        default: Any = None,
        dispatch_data: Callable[[Any], Dict] = None,
        **kwargs,
    ) -> Any:
    '''
    Sync a widget value and dispatch when it changes.

    :param session: Session cache that stores the widget value.
    :type session: SessionCacheContext
    :param dispatch: Callable that runs a feature.
    :type dispatch: Callable
    :param key: Session key for the stored value.
    :type key: str
    :param widget: Callable that draws the widget and returns its value.
    :type widget: Callable
    :param feature_id: Feature to dispatch when the value changes.
    :type feature_id: str
    :param value_param: Keyword passed to the widget as the current value.
    :type value_param: str
    :param default: Value used when the session key is missing.
    :type default: Any
    :param dispatch_data: Optional mapper from the new value to dispatch keywords.
    :type dispatch_data: Callable[[Any], Dict]
    :param kwargs: Additional keyword arguments forwarded to the widget.
    :type kwargs: dict
    :return: The value returned by the widget.
    :rtype: Any
    '''

    # Capture the value before the widget runs.
    before = session.get(key)

    # Sync the widget with session state.
    new_value = _bind_widget(
        session,
        key,
        widget,
        value_param=value_param,
        default=default,
        **kwargs,
    )

    # Skip dispatch when the value did not change.
    if new_value == before:
        return new_value

    # Build the dispatch payload from the mapper, or from the key.
    if dispatch_data is not None:
        data = dispatch_data(new_value)
    else:
        data = {key: new_value}

    # Dispatch the feature with the payload.
    dispatch(feature_id, **data)

    # Return the widget result.
    return new_value

# ** function: _bind_trigger
def _bind_trigger(
        dispatch: Callable,
        widget: Callable,
        feature_id: str,
        dispatch_data: Callable[[], Dict] = None,
        **kwargs,
    ) -> Any:
    '''
    Dispatch a feature when a widget returns a truthy value.

    :param dispatch: Callable that runs a feature.
    :type dispatch: Callable
    :param widget: Callable that draws the widget and returns its result.
    :type widget: Callable
    :param feature_id: Feature to dispatch when the widget result is truthy.
    :type feature_id: str
    :param dispatch_data: Optional zero-argument mapper to dispatch keywords.
    :type dispatch_data: Callable[[], Dict]
    :param kwargs: Additional keyword arguments forwarded to the widget.
    :type kwargs: dict
    :return: The value returned by the widget.
    :rtype: Any
    '''

    # Draw the widget without reading or writing session state.
    triggered = widget(**kwargs)

    # Dispatch only when the widget result is truthy.
    if triggered:
        dispatch(
            feature_id,
            **(dispatch_data() if dispatch_data else {}),
        )

    # Return the widget result either way.
    return triggered

# *** contexts

# ** context: view_context
class ViewContext(object):
    '''
    The code-behind for a Streamlit page. Manages state via
    SessionCacheContext, dispatches Tiferet features via
    AppSessionContext, and defines Streamlit widgets through
    an overridable render() method.
    '''

    # * attribute: app
    app: AppSessionContext

    # * attribute: key
    key: str

    # * attribute: session
    session: SessionCacheContext

    # * init
    def __init__(self,
            app: AppSessionContext,
            key: str,
            session: SessionCacheContext = None,
        ):
        '''
        Initialize the view context.

        :param app: Tiferet app session context for feature dispatch.
        :type app: AppSessionContext
        :param key: Unique identifier for this view instance.
        :type key: str
        :param session: Optional session cache. Auto-created with namespace=key if not provided.
        :type session: SessionCacheContext
        '''

        # Set the app context.
        self.app = app

        # Set the view key.
        self.key = key

        # Set or create the session cache.
        self.session = session or SessionCacheContext(namespace=key)

        # Guard one-time initialization.
        if not self.session.get('_initialized'):
            self.init_state()
            self.session.set('_initialized', True)

    # * method: init_state
    def init_state(self):
        '''
        Initialize view state. No-op by default.
        Subclasses override to set initial state values.
        '''
        pass

    # * method: dispatch
    def dispatch(self,
            feature_id: str,
            headers: Dict[str, str] = None,
            **data,
        ) -> Any:
        '''
        Dispatch a Tiferet feature via the app context.

        :param feature_id: The feature identifier to execute.
        :type feature_id: str
        :param headers: Optional request headers.
        :type headers: Dict[str, str]
        :param data: Keyword arguments passed as feature data.
        :type data: dict
        :return: The feature result.
        :rtype: Any
        '''

        try:
            # Delegate to the app context run method.
            result = self.app.run(
                feature_id=feature_id,
                headers=headers or {},
                data=data,
            )

        except Exception as exception:
            # Record the failed dispatch before re-raising.
            self._log_dispatch(
                feature_id=feature_id,
                data=data,
                outcome='error',
                result=str(exception),
            )

            # Re-raise the original exception.
            raise

        # Record the successful dispatch.
        self._log_dispatch(
            feature_id=feature_id,
            data=data,
            outcome='success',
            result=result,
        )

        # Return the same feature result.
        return result

    # * method: _log_dispatch
    def _log_dispatch(self,
            feature_id: str,
            data: Dict[str, Any],
            outcome: str,
            result: Any,
        ) -> None:
        '''
        Append one dispatch audit record to this view's session cache.

        :param feature_id: Feature that was dispatched.
        :type feature_id: str
        :param data: Keyword arguments passed as feature data.
        :type data: Dict[str, Any]
        :param outcome: Whether the dispatch succeeded or raised.
        :type outcome: str
        :param result: Feature result, or the exception text.
        :type result: Any
        '''

        # Build the audit record from the dispatch outcome.
        record = DispatchAuditRecord(
            feature_id=feature_id,
            arguments=data,
            outcome=outcome,
            result=result,
        )

        # Read the existing log, or start an empty one.
        log = self.session.get('_audit_log') or []

        # Append the serialized record.
        log.append(record.model_dump())

        # Store the updated log under the literal session key.
        self.session.set('_audit_log', log)

    # * method: audit_log (property)
    @property
    def audit_log(self) -> List[DispatchAuditRecord]:
        '''
        Reconstruct stored dispatch records in append order.

        A missing log returns an empty list. Reading does not clear the log.

        :return: Dispatch audit records, oldest first.
        :rtype: List[DispatchAuditRecord]
        '''

        # Read stored records, or an empty list when the key is missing.
        records = self.session.get('_audit_log') or []

        # Reconstruct domain objects without clearing the log.
        return [
            DispatchAuditRecord(**record)
            for record in records
        ]

    # * method: bind_widget
    # >> see: @guides/widgets.md#viewcontext-bind-widget
    def bind_widget(self,
            key: str,
            widget: Callable,
            value_param: str = 'value',
            default: Any = None,
            **kwargs,
        ) -> Any:
        '''
        Sync a widget value with this view's session.

        :param key: Session key for the stored value.
        :type key: str
        :param widget: Callable that draws the widget and returns its value.
        :type widget: Callable
        :param value_param: Keyword passed to the widget as the current value.
        :type value_param: str
        :param default: Value used when the session key is missing.
        :type default: Any
        :param kwargs: Additional keyword arguments forwarded to the widget.
        :type kwargs: dict
        :return: The value returned by the widget.
        :rtype: Any
        '''

        # Delegate value sync to the shared helper.
        return _bind_widget(
            self.session,
            key,
            widget,
            value_param=value_param,
            default=default,
            **kwargs,
        )

    # * method: bind_widget_dispatch
    # >> see: @guides/widgets.md#viewcontext-bind-widget-dispatch
    def bind_widget_dispatch(self,
            key: str,
            widget: Callable,
            feature_id: str,
            value_param: str = 'value',
            default: Any = None,
            dispatch_data: Callable[[Any], Dict] = None,
            **kwargs,
        ) -> Any:
        '''
        Sync a widget value and dispatch when it changes.

        :param key: Session key for the stored value.
        :type key: str
        :param widget: Callable that draws the widget and returns its value.
        :type widget: Callable
        :param feature_id: Feature to dispatch when the value changes.
        :type feature_id: str
        :param value_param: Keyword passed to the widget as the current value.
        :type value_param: str
        :param default: Value used when the session key is missing.
        :type default: Any
        :param dispatch_data: Optional mapper from the new value to dispatch keywords.
        :type dispatch_data: Callable[[Any], Dict]
        :param kwargs: Additional keyword arguments forwarded to the widget.
        :type kwargs: dict
        :return: The value returned by the widget.
        :rtype: Any
        '''

        # Delegate change-triggered dispatch to the shared helper.
        return _bind_widget_dispatch(
            self.session,
            self.dispatch,
            key,
            widget,
            feature_id,
            value_param=value_param,
            default=default,
            dispatch_data=dispatch_data,
            **kwargs,
        )

    # * method: bind_trigger
    # >> see: @guides/widgets.md#viewcontext-bind-trigger
    def bind_trigger(self,
            widget: Callable,
            feature_id: str,
            dispatch_data: Callable[[], Dict] = None,
            **kwargs,
        ) -> Any:
        '''
        Dispatch a feature when a widget returns a truthy value.

        :param widget: Callable that draws the widget and returns its result.
        :type widget: Callable
        :param feature_id: Feature to dispatch when the widget result is truthy.
        :type feature_id: str
        :param dispatch_data: Optional zero-argument mapper to dispatch keywords.
        :type dispatch_data: Callable[[], Dict]
        :param kwargs: Additional keyword arguments forwarded to the widget.
        :type kwargs: dict
        :return: The value returned by the widget.
        :rtype: Any
        '''

        # Delegate the truthy trigger to the shared helper.
        return _bind_trigger(
            self.dispatch,
            widget,
            feature_id,
            dispatch_data=dispatch_data,
            **kwargs,
        )

    # * method: render
    def render(self):
        '''
        Define the Streamlit UI for this view.
        Subclasses must override this method.

        :raises NotImplementedError: Always, unless overridden.
        '''
        raise NotImplementedError()

    # * method: __call__
    def __call__(self):
        '''
        Make the view callable for Streamlit composition.

        Delegates to render(). A successful result, including None, is
        returned unchanged. NotImplementedError from the default render
        path is re-raised. Any other exception is wrapped as a view render
        failure chained from the original exception.

        :return: The result of render().
        :rtype: Any
        :raises NotImplementedError: When render() is not overridden.
        :raises TiferetError: When render() raises any other exception.
        '''

        # Delegate to render, wrapping a concrete failure.
        try:
            return self.render()
        except NotImplementedError:
            raise
        except Exception as err:
            try:
                TiferetError.raise_error(
                    VIEW_RENDER_FAILED_ID,
                    view_key=self.key,
                )
            except TiferetError as failure:
                raise failure from err

# ** context: view_component
class ViewComponent(object):
    '''
    A lightweight, prop-driven sub-component that accesses a parent
    ViewContext for state and actions.
    '''

    # * attribute: ctx
    ctx: ViewContext

    # * init
    def __init__(self, ctx: ViewContext):
        '''
        Initialize the view component.

        :param ctx: The parent view context.
        :type ctx: ViewContext
        '''

        # Set the parent view context.
        self.ctx = ctx

    # * method: bind_widget
    # >> see: @guides/widgets.md#viewcomponent-bind-widget
    def bind_widget(self,
            key: str,
            widget: Callable,
            value_param: str = 'value',
            default: Any = None,
            **kwargs,
        ) -> Any:
        '''
        Sync a widget value with the parent view's session.

        :param key: Session key for the stored value.
        :type key: str
        :param widget: Callable that draws the widget and returns its value.
        :type widget: Callable
        :param value_param: Keyword passed to the widget as the current value.
        :type value_param: str
        :param default: Value used when the session key is missing.
        :type default: Any
        :param kwargs: Additional keyword arguments forwarded to the widget.
        :type kwargs: dict
        :return: The value returned by the widget.
        :rtype: Any
        '''

        # Delegate value sync to the parent view's shared helper.
        return _bind_widget(
            self.ctx.session,
            key,
            widget,
            value_param=value_param,
            default=default,
            **kwargs,
        )

    # * method: bind_widget_dispatch
    # >> see: @guides/widgets.md#viewcomponent-bind-widget-dispatch
    def bind_widget_dispatch(self,
            key: str,
            widget: Callable,
            feature_id: str,
            value_param: str = 'value',
            default: Any = None,
            dispatch_data: Callable[[Any], Dict] = None,
            **kwargs,
        ) -> Any:
        '''
        Sync a widget value and dispatch on the parent view when it changes.

        :param key: Session key for the stored value.
        :type key: str
        :param widget: Callable that draws the widget and returns its value.
        :type widget: Callable
        :param feature_id: Feature to dispatch when the value changes.
        :type feature_id: str
        :param value_param: Keyword passed to the widget as the current value.
        :type value_param: str
        :param default: Value used when the session key is missing.
        :type default: Any
        :param dispatch_data: Optional mapper from the new value to dispatch keywords.
        :type dispatch_data: Callable[[Any], Dict]
        :param kwargs: Additional keyword arguments forwarded to the widget.
        :type kwargs: dict
        :return: The value returned by the widget.
        :rtype: Any
        '''

        # Delegate change-triggered dispatch to the parent view.
        return _bind_widget_dispatch(
            self.ctx.session,
            self.ctx.dispatch,
            key,
            widget,
            feature_id,
            value_param=value_param,
            default=default,
            dispatch_data=dispatch_data,
            **kwargs,
        )

    # * method: bind_trigger
    # >> see: @guides/widgets.md#viewcomponent-bind-trigger
    def bind_trigger(self,
            widget: Callable,
            feature_id: str,
            dispatch_data: Callable[[], Dict] = None,
            **kwargs,
        ) -> Any:
        '''
        Dispatch a feature on the parent view when a widget returns a truthy value.

        :param widget: Callable that draws the widget and returns its result.
        :type widget: Callable
        :param feature_id: Feature to dispatch when the widget result is truthy.
        :type feature_id: str
        :param dispatch_data: Optional zero-argument mapper to dispatch keywords.
        :type dispatch_data: Callable[[], Dict]
        :param kwargs: Additional keyword arguments forwarded to the widget.
        :type kwargs: dict
        :return: The value returned by the widget.
        :rtype: Any
        '''

        # Delegate the truthy trigger to the parent view.
        return _bind_trigger(
            self.ctx.dispatch,
            widget,
            feature_id,
            dispatch_data=dispatch_data,
            **kwargs,
        )

    # * method: render
    def render(self, **props):
        '''
        Define the component UI. Subclasses must override this method.

        :param props: Keyword arguments passed as component properties.
        :type props: dict
        :raises NotImplementedError: Always, unless overridden.
        '''
        raise NotImplementedError()

    # * method: __call__
    def __call__(self, **props):
        '''
        Make the component callable. Delegates to render(**props).

        :param props: Keyword arguments passed as component properties.
        :type props: dict
        '''

        # Delegate to render.
        return self.render(**props)
