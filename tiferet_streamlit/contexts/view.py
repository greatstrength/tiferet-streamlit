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
    Keep a native Streamlit widget's displayed value in sync with a
    SessionCacheContext key, replacing the hand-wired read/draw/write
    pattern every widget would otherwise repeat. Shared by
    ViewContext.bind_widget and ViewComponent.bind_widget.

    :param session: The session cache to read from and write back to.
    :type session: SessionCacheContext
    :param key: The session cache key to read from and write back to.
    :type key: str
    :param widget: The native Streamlit widget callable (e.g. st.text_input).
    :type widget: Callable
    :param value_param: The widget kwarg used to seed its current value.
    :type value_param: str
    :param default: The value to seed the widget with before it is ever set.
    :type default: Any
    :param kwargs: Additional keyword arguments forwarded to the widget untouched.
    :type kwargs: dict
    :return: The widget's return value, already written back to the cache.
    :rtype: Any
    '''

    # Read the stored value before rendering, falling back to the default.
    current = session.get(key)
    if current is None:
        current = default

    # Draw the widget, seeding it with the current value.
    kwargs[value_param] = current
    new_value = widget(**kwargs)

    # Write the widget's return value back to the cache.
    session.set(key, new_value)

    # Return the synced value.
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
    Compose _bind_widget with a change-triggered dispatch: after syncing,
    call dispatch(feature_id, ...) only when the value actually changed
    on this rerun. Shared by ViewContext.bind_widget_dispatch and
    ViewComponent.bind_widget_dispatch.

    :param session: The session cache to read from and write back to.
    :type session: SessionCacheContext
    :param dispatch: The dispatch callable to invoke on change.
    :type dispatch: Callable
    :param key: The session cache key to read from and write back to.
    :type key: str
    :param widget: The native Streamlit widget callable (e.g. st.number_input).
    :type widget: Callable
    :param feature_id: The Tiferet feature to dispatch on change.
    :type feature_id: str
    :param value_param: The widget kwarg used to seed its current value.
    :type value_param: str
    :param default: The value to seed the widget with before it is ever set.
    :type default: Any
    :param dispatch_data: Optional callable mapping the new value to dispatch kwargs.
        Defaults to a fixed {key: new_value} payload.
    :type dispatch_data: Callable[[Any], Dict]
    :param kwargs: Additional keyword arguments forwarded to the widget untouched.
    :type kwargs: dict
    :return: The widget's return value, already written back to the cache.
    :rtype: Any
    '''

    # Capture the prior value before this rerun's widget draw overwrites it.
    before = session.get(key)

    # Sync the widget's value as usual.
    new_value = _bind_widget(
        session,
        key,
        widget,
        value_param=value_param,
        default=default,
        **kwargs,
    )

    # Only dispatch when the value actually changed on this rerun.
    if new_value == before:
        return new_value

    # Build the dispatch payload and call the feature.
    data = dispatch_data(new_value) if dispatch_data else {key: new_value}
    dispatch(feature_id, **data)

    # Return the synced value.
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
    Dispatch unconditionally when a trigger-style widget (e.g. st.button,
    st.form_submit_button) returns truthy, with no reliance on a stored
    previous value. Shared by ViewContext.bind_trigger and
    ViewComponent.bind_trigger.

    :param dispatch: The dispatch callable to invoke on a truthy return.
    :type dispatch: Callable
    :param widget: The native trigger-style Streamlit widget callable.
    :type widget: Callable
    :param feature_id: The Tiferet feature to dispatch on trigger.
    :type feature_id: str
    :param dispatch_data: Optional callable returning dispatch kwargs.
        Defaults to an empty payload.
    :type dispatch_data: Callable[[], Dict]
    :param kwargs: Additional keyword arguments forwarded to the widget untouched.
    :type kwargs: dict
    :return: The widget's return value.
    :rtype: Any
    '''

    # Draw the trigger widget.
    triggered = widget(**kwargs)

    # Dispatch unconditionally on a truthy return.
    if triggered:
        data = dispatch_data() if dispatch_data else {}
        dispatch(feature_id, **data)

    # Return the widget's return value.
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
        Dispatch a Tiferet feature via the app context, recording every
        attempt to the view's in-session audit log.

        :param feature_id: The feature identifier to execute.
        :type feature_id: str
        :param headers: Optional request headers.
        :type headers: Dict[str, str]
        :param data: Keyword arguments passed as feature data.
        :type data: dict
        :return: The feature result.
        :rtype: Any
        '''

        # Delegate to the app context run method, capturing the outcome.
        try:
            result = self.app.run(
                feature_id=feature_id,
                headers=headers or {},
                data=data,
            )
        except Exception as exception:

            # Record the failed dispatch before re-raising unchanged.
            self._log_dispatch(
                feature_id=feature_id,
                data=data,
                outcome='error',
                result=str(exception),
            )
            raise

        # Record the successful dispatch.
        self._log_dispatch(
            feature_id=feature_id,
            data=data,
            outcome='success',
            result=result,
        )

        # Return the feature result unchanged.
        return result

    # * method: _log_dispatch
    def _log_dispatch(self,
            feature_id: str,
            data: Dict[str, Any],
            outcome: str,
            result: Any,
        ):
        '''
        Append a dispatch outcome record to this view's audit log.

        :param feature_id: The feature identifier that was dispatched.
        :type feature_id: str
        :param data: The arguments passed to the feature.
        :type data: Dict[str, Any]
        :param outcome: Either 'success' or 'error'.
        :type outcome: str
        :param result: The feature result, or an error summary.
        :type result: Any
        '''

        # Build the audit record domain object.
        record = DispatchAuditRecord(
            feature_id=feature_id,
            arguments=data,
            outcome=outcome,
            result=result,
        )

        # Append the record's primitive form to this view's namespaced audit log.
        log = self.session.get('_audit_log') or []
        log.append(record.model_dump())
        self.session.set('_audit_log', log)

    # * method: audit_log (property)
    @property
    def audit_log(self) -> List[DispatchAuditRecord]:
        '''
        This view's dispatch audit log, oldest first.

        :return: The recorded dispatch outcomes as domain objects.
        :rtype: List[DispatchAuditRecord]
        '''

        # Reconstruct domain objects from the namespaced primitive log.
        return [
            DispatchAuditRecord(**record)
            for record in (self.session.get('_audit_log') or [])
        ]

    # * method: bind_widget
    def bind_widget(self,
            key: str,
            widget: Callable,
            value_param: str = 'value',
            default: Any = None,
            **kwargs,
        ) -> Any:
        '''
        Keep a native Streamlit widget's displayed value in sync with a
        SessionCacheContext key owned by this view, replacing the
        hand-wired read/draw/write pattern every widget would otherwise
        repeat.

        :param key: The session cache key to read from and write back to.
        :type key: str
        :param widget: The native Streamlit widget callable (e.g. st.text_input).
        :type widget: Callable
        :param value_param: The widget kwarg used to seed its current value.
        :type value_param: str
        :param default: The value to seed the widget with before it is ever set.
        :type default: Any
        :param kwargs: Additional keyword arguments forwarded to the widget untouched.
        :type kwargs: dict
        :return: The widget's return value, already written back to the cache.
        :rtype: Any
        '''

        # Delegate to the shared module-level implementation.
        return _bind_widget(self.session, key, widget, value_param=value_param, default=default, **kwargs)

    # * method: bind_widget_dispatch
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
        Compose bind_widget with a change-triggered dispatch: after syncing,
        call self.dispatch(feature_id, ...) only when the value actually
        changed on this rerun.

        :param key: The session cache key to read from and write back to.
        :type key: str
        :param widget: The native Streamlit widget callable (e.g. st.number_input).
        :type widget: Callable
        :param feature_id: The Tiferet feature to dispatch on change.
        :type feature_id: str
        :param value_param: The widget kwarg used to seed its current value.
        :type value_param: str
        :param default: The value to seed the widget with before it is ever set.
        :type default: Any
        :param dispatch_data: Optional callable mapping the new value to dispatch kwargs.
            Defaults to a fixed {key: new_value} payload.
        :type dispatch_data: Callable[[Any], Dict]
        :param kwargs: Additional keyword arguments forwarded to the widget untouched.
        :type kwargs: dict
        :return: The widget's return value, already written back to the cache.
        :rtype: Any
        '''

        # Delegate to the shared module-level implementation.
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
    def bind_trigger(self,
            widget: Callable,
            feature_id: str,
            dispatch_data: Callable[[], Dict] = None,
            **kwargs,
        ) -> Any:
        '''
        Dispatch unconditionally when a trigger-style widget (e.g. st.button,
        st.form_submit_button) returns truthy, with no reliance on a stored
        previous value.

        :param widget: The native trigger-style Streamlit widget callable.
        :type widget: Callable
        :param feature_id: The Tiferet feature to dispatch on trigger.
        :type feature_id: str
        :param dispatch_data: Optional callable returning dispatch kwargs.
            Defaults to an empty payload.
        :type dispatch_data: Callable[[], Dict]
        :param kwargs: Additional keyword arguments forwarded to the widget untouched.
        :type kwargs: dict
        :return: The widget's return value.
        :rtype: Any
        '''

        # Delegate to the shared module-level implementation.
        return _bind_trigger(self.dispatch, widget, feature_id, dispatch_data=dispatch_data, **kwargs)

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
        Delegates to render(), wrapping a concrete subclass's render()
        failure into a structured error so operators can trace it back
        to the failing view. A well-formed render() is unaffected.

        :raises NotImplementedError: If render() is not overridden by a subclass.
        :raises TiferetError: If an overridden render() raises any other exception,
            carrying VIEW_RENDER_FAILED_ID and the original exception chained via
            raise ... from.
        '''

        # Delegate to render, leaving the default, unoverridden render()'s
        # NotImplementedError unwrapped since it signals an incomplete
        # implementation rather than a runtime failure.
        try:
            return self.render()
        except NotImplementedError:
            raise

        # Wrap any other render() failure as a structured, chained error.
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
    def bind_widget(self,
            key: str,
            widget: Callable,
            value_param: str = 'value',
            default: Any = None,
            **kwargs,
        ) -> Any:
        '''
        Keep a native Streamlit widget's displayed value in sync with a
        SessionCacheContext key owned by the parent ctx, replacing the
        hand-wired read/draw/write pattern every widget would otherwise
        repeat.

        :param key: The session cache key to read from and write back to.
        :type key: str
        :param widget: The native Streamlit widget callable (e.g. st.text_input).
        :type widget: Callable
        :param value_param: The widget kwarg used to seed its current value.
        :type value_param: str
        :param default: The value to seed the widget with before it is ever set.
        :type default: Any
        :param kwargs: Additional keyword arguments forwarded to the widget untouched.
        :type kwargs: dict
        :return: The widget's return value, already written back to the cache.
        :rtype: Any
        '''

        # Delegate to the shared module-level implementation.
        return _bind_widget(self.ctx.session, key, widget, value_param=value_param, default=default, **kwargs)

    # * method: bind_widget_dispatch
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
        Compose bind_widget with a change-triggered dispatch: after syncing,
        call the parent ctx's dispatch(feature_id, ...) only when the value
        actually changed on this rerun.

        :param key: The session cache key to read from and write back to.
        :type key: str
        :param widget: The native Streamlit widget callable (e.g. st.number_input).
        :type widget: Callable
        :param feature_id: The Tiferet feature to dispatch on change.
        :type feature_id: str
        :param value_param: The widget kwarg used to seed its current value.
        :type value_param: str
        :param default: The value to seed the widget with before it is ever set.
        :type default: Any
        :param dispatch_data: Optional callable mapping the new value to dispatch kwargs.
            Defaults to a fixed {key: new_value} payload.
        :type dispatch_data: Callable[[Any], Dict]
        :param kwargs: Additional keyword arguments forwarded to the widget untouched.
        :type kwargs: dict
        :return: The widget's return value, already written back to the cache.
        :rtype: Any
        '''

        # Delegate to the shared module-level implementation.
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
    def bind_trigger(self,
            widget: Callable,
            feature_id: str,
            dispatch_data: Callable[[], Dict] = None,
            **kwargs,
        ) -> Any:
        '''
        Dispatch unconditionally when a trigger-style widget (e.g. st.button,
        st.form_submit_button) returns truthy, with no reliance on a stored
        previous value.

        :param widget: The native trigger-style Streamlit widget callable.
        :type widget: Callable
        :param feature_id: The Tiferet feature to dispatch on trigger.
        :type feature_id: str
        :param dispatch_data: Optional callable returning dispatch kwargs.
            Defaults to an empty payload.
        :type dispatch_data: Callable[[], Dict]
        :param kwargs: Additional keyword arguments forwarded to the widget untouched.
        :type kwargs: dict
        :return: The widget's return value.
        :rtype: Any
        '''

        # Delegate to the shared module-level implementation.
        return _bind_trigger(self.ctx.dispatch, widget, feature_id, dispatch_data=dispatch_data, **kwargs)

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
