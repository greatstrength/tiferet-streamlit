'''Tiferet Streamlit – View Context Tests'''

# *** imports

# ** infra
import pytest
from unittest.mock import MagicMock
from tiferet import TiferetError
from tiferet.contexts.app import AppSessionContext

# ** app
from tiferet_streamlit.contexts.session import SessionCacheContext
from tiferet_streamlit.contexts.view import ViewContext, ViewComponent
from tiferet_streamlit.domain import DispatchAuditRecord

# *** helpers

# ** helper: sample_view
class SampleView(ViewContext):
    '''
    Concrete ViewContext for testing. Tracks init_state calls.
    '''

    # * method: init_state
    def init_state(self):
        '''Set initial state values.'''

        # Track that init_state was called.
        self.session.set('init_called', True)

    # * method: render
    def render(self):
        '''Render the view.'''
        return 'rendered'

# ** helper: rendering_view
class RenderingView(ViewContext):
    '''
    ViewContext that tracks render count in session state.
    '''

    # * method: init_state
    def init_state(self):
        '''Initialize the render counter.'''

        # Initialize the render counter.
        self.session.set('render_count', 0)

    # * method: render
    def render(self):
        '''Increment and return the render count.'''

        # Increment the render count.
        count = self.session.get('render_count') + 1
        self.session.set('render_count', count)

        # Return the current count.
        return count

# ** helper: sample_component
class SampleComponent(ViewComponent):
    '''
    Concrete ViewComponent for testing.
    '''

    # * method: render
    def render(self, **props):
        '''Render the component with props.'''
        return props

# ** helper: recording_widget
def recording_widget(calls, result):
    '''
    Build a widget callable that records kwargs and returns a scripted value.

    :param calls: List that receives each kwargs dict.
    :type calls: list
    :param result: Value the widget returns.
    :type result: Any
    :return: A widget callable.
    :rtype: Callable
    '''

    def widget(**kwargs):
        '''Record kwargs and return the scripted value.'''

        # Record the forwarded keyword arguments.
        calls.append(kwargs)

        # Return the scripted widget value.
        return result

    # Return the fake widget.
    return widget

# *** fixtures

# ** fixture: mock_app
@pytest.fixture
def mock_app() -> MagicMock:
    '''
    AppSessionContext double exposing run.

    :return: A mocked AppSessionContext whose run returns 'mock_result'.
    :rtype: MagicMock
    '''

    # Create an app-session double that exposes run.
    app = MagicMock(spec=AppSessionContext)
    app.run.return_value = 'mock_result'
    return app

# ** fixture: sample_view
@pytest.fixture
def sample_view(mock_app: MagicMock, mock_session_state: dict) -> SampleView:
    '''
    SampleView instance for testing.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    :return: A SampleView instance.
    :rtype: SampleView
    '''

    return SampleView(app=mock_app, key='test_view')

# *** tests: view_context lifecycle

# ** test: init_state_called_once
def test_init_state_called_once(sample_view: SampleView, mock_session_state: dict) -> None:
    '''
    Verify init_state() runs on first construction.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Assert init_state was called.
    assert sample_view.session.get('init_called') is True

# ** test: init_state_not_called_again
def test_init_state_not_called_again(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify second construction with same key skips init_state().

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # First construction triggers init_state.
    view1 = SampleView(app=mock_app, key='shared_key')
    assert view1.session.get('init_called') is True

    # Overwrite init_called to detect if init_state runs again.
    view1.session.set('init_called', False)

    # Second construction with same key should skip init_state.
    view2 = SampleView(app=mock_app, key='shared_key')
    assert view2.session.get('init_called') is False

# ** test: default_init_state_is_noop
def test_default_init_state_is_noop(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify base init_state() sets only _initialized.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a plain ViewContext (not subclassed with custom init_state).
    class PlainView(ViewContext):
        def render(self):
            return 'plain'

    view = PlainView(app=mock_app, key='plain_key')

    # Assert only _initialized is set in the namespace.
    assert view.session.get('_initialized') is True

    # Assert no other keys exist in this namespace.
    ns_keys = [k for k in mock_session_state.keys() if k.startswith('plain_key.')]
    assert len(ns_keys) == 1

# *** tests: view_context dispatch

# ** test: dispatch_calls_app_run
def test_dispatch_calls_app_run(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify app.run is called with correct args.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Dispatch a feature.
    result = sample_view.dispatch('calc.add', a=1, b=2)

    # Assert the result.
    assert result == 'mock_result'

    # Assert app.run was called correctly.
    mock_app.run.assert_called_once_with(
        feature_id='calc.add',
        headers={},
        data={'a': 1, 'b': 2},
    )

# ** test: dispatch_with_headers
def test_dispatch_with_headers(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify custom headers are passed.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Dispatch with custom headers.
    sample_view.dispatch('feat.x', headers={'lang': 'en_US'}, x=10)

    # Assert app.run was called with the headers.
    mock_app.run.assert_called_once_with(
        feature_id='feat.x',
        headers={'lang': 'en_US'},
        data={'x': 10},
    )

# ** test: dispatch_logs_success
def test_dispatch_logs_success(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify a successful dispatch appends one record and returns the run value.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Dispatch a feature.
    result = sample_view.dispatch('calc.add', a=1, b=2)

    # Assert dispatch returns the same run result.
    assert result is mock_app.run.return_value
    assert result == 'mock_result'

    # Assert exactly one success record was stored under the literal key.
    stored = sample_view.session.get('_audit_log')
    assert len(stored) == 1
    assert stored[0]['feature_id'] == 'calc.add'
    assert stored[0]['arguments'] == {'a': 1, 'b': 2}
    assert stored[0]['outcome'] == 'success'
    assert stored[0]['result'] == 'mock_result'

    # Assert the public log reconstructs that record.
    records = sample_view.audit_log
    assert len(records) == 1
    assert isinstance(records[0], DispatchAuditRecord)
    assert records[0].feature_id == 'calc.add'
    assert records[0].arguments == {'a': 1, 'b': 2}
    assert records[0].outcome == 'success'
    assert records[0].result == 'mock_result'

# ** test: dispatch_logs_error_and_reraises
def test_dispatch_logs_error_and_reraises(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify a raised dispatch is logged and the same exception propagates.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Configure run to raise a specific error.
    error = RuntimeError('boom')
    mock_app.run.side_effect = error

    # Assert the same RuntimeError propagates.
    with pytest.raises(RuntimeError) as exc_info:
        sample_view.dispatch('calc.add', a=1)

    assert exc_info.value is error

    # Assert exactly one error record was stored.
    records = sample_view.audit_log
    assert len(records) == 1
    assert records[0].outcome == 'error'
    assert records[0].result == 'boom'

# ** test: audit_log_empty_before_dispatch
def test_audit_log_empty_before_dispatch(sample_view: SampleView) -> None:
    '''
    Verify audit_log is empty before any dispatch.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Assert no records exist yet.
    assert sample_view.audit_log == []

# ** test: audit_log_is_namespaced
def test_audit_log_is_namespaced(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify two views with different keys do not see each other's records.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create two views with different keys.
    left = SampleView(app=mock_app, key='left_view')
    right = SampleView(app=mock_app, key='right_view')

    # Dispatch a different feature on each view.
    left.dispatch('calc.add', a=1)
    right.dispatch('calc.sub', a=2)

    # Assert each view sees only its own record.
    assert len(left.audit_log) == 1
    assert left.audit_log[0].feature_id == 'calc.add'
    assert left.audit_log[0].arguments == {'a': 1}
    assert len(right.audit_log) == 1
    assert right.audit_log[0].feature_id == 'calc.sub'
    assert right.audit_log[0].arguments == {'a': 2}

    # Assert the stored key inside each namespace is the literal _audit_log.
    assert 'left_view._audit_log' in mock_session_state
    assert 'right_view._audit_log' in mock_session_state
    assert mock_session_state['left_view._audit_log'][0]['feature_id'] == 'calc.add'
    assert mock_session_state['right_view._audit_log'][0]['feature_id'] == 'calc.sub'

# *** tests: view_context render

# ** test: render_raises_not_implemented
def test_render_raises_not_implemented(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify base render() raises NotImplementedError.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a base ViewContext (render not overridden).
    class BareView(ViewContext):
        pass

    view = BareView(app=mock_app, key='bare')

    # Assert render raises NotImplementedError.
    with pytest.raises(NotImplementedError):
        view.render()

# ** test: callable_delegates_to_render
def test_callable_delegates_to_render(sample_view: SampleView) -> None:
    '''
    Verify view() invokes render().

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Call the view as a callable.
    result = sample_view()

    # Assert it delegated to render.
    assert result == 'rendered'

# ** test: call_wraps_render_exception
def test_call_wraps_render_exception(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify a concrete render failure becomes a chained view render error.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Define a view whose render raises a specific runtime error.
    error = RuntimeError('render failed')

    class FailingView(ViewContext):
        def render(self):
            raise error

    view = FailingView(app=mock_app, key='failing_view')

    # Assert the call wraps the runtime error.
    with pytest.raises(TiferetError) as exc_info:
        view()

    # Assert the structured error carries the view key and the original cause.
    failure = exc_info.value
    assert failure.error_code == 'VIEW_RENDER_FAILED'
    assert failure.kwargs['view_key'] == 'failing_view'
    assert failure.__cause__ is error

# ** test: call_does_not_wrap_not_implemented
def test_call_does_not_wrap_not_implemented(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify the default render path still raises NotImplementedError.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a view that does not override render.
    class BareView(ViewContext):
        pass

    view = BareView(app=mock_app, key='bare_call')

    # Assert the call raises NotImplementedError, not a wrapped error.
    with pytest.raises(NotImplementedError) as exc_info:
        view()

    assert not isinstance(exc_info.value, TiferetError)

# ** test: multiple_renders_accumulate
def test_multiple_renders_accumulate(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify state accumulates across renders.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a rendering view.
    view = RenderingView(app=mock_app, key='counter')

    # Render multiple times.
    assert view.render() == 1
    assert view.render() == 2
    assert view.render() == 3

# *** tests: view_context session

# ** test: session_namespace_matches_key
def test_session_namespace_matches_key(sample_view: SampleView) -> None:
    '''
    Verify auto-created session uses view key as namespace.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Assert the session namespace matches the view key.
    assert sample_view.session.namespace == sample_view.key

# ** test: custom_session_is_used
def test_custom_session_is_used(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify custom session is preserved.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a custom session.
    custom_session = SessionCacheContext(namespace='custom_ns')

    # Create a view with the custom session.
    view = SampleView(app=mock_app, key='view_key', session=custom_session)

    # Assert the custom session is used.
    assert view.session is custom_session
    assert view.session.namespace == 'custom_ns'

# *** tests: view_component

# ** test: component_render
def test_component_render(sample_view: SampleView) -> None:
    '''
    Verify render executes with props.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Create a component and render with props.
    comp = SampleComponent(ctx=sample_view)
    result = comp.render(title='Hello', count=5)

    # Assert the props are returned.
    assert result == {'title': 'Hello', 'count': 5}

# ** test: component_callable
def test_component_callable(sample_view: SampleView) -> None:
    '''
    Verify comp() invokes render().

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Create a component and call it.
    comp = SampleComponent(ctx=sample_view)
    result = comp(name='world')

    # Assert it delegated to render.
    assert result == {'name': 'world'}

# ** test: component_default_props
def test_component_default_props(sample_view: SampleView) -> None:
    '''
    Verify default prop values work.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Create a component and render with no props.
    comp = SampleComponent(ctx=sample_view)
    result = comp.render()

    # Assert empty props are returned.
    assert result == {}

# ** test: component_accesses_parent_dispatch
def test_component_accesses_parent_dispatch(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify component can dispatch via parent context.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Create a component and dispatch via parent.
    comp = SampleComponent(ctx=sample_view)
    result = comp.ctx.dispatch('calc.add', a=1, b=2)

    # Assert the dispatch worked.
    assert result == 'mock_result'

# ** test: component_raises_not_implemented
def test_component_raises_not_implemented(sample_view: SampleView) -> None:
    '''
    Verify base render() raises NotImplementedError.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Create a base ViewComponent.
    comp = ViewComponent(ctx=sample_view)

    # Assert render raises NotImplementedError.
    with pytest.raises(NotImplementedError):
        comp.render()

# *** tests: widget binding

# ** test: bind_widget_seeds_default_and_writes_back
def test_bind_widget_seeds_default_and_writes_back(sample_view: SampleView) -> None:
    '''
    Verify a missing key uses default as the widget value and stores the result.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Confirm the key is missing.
    assert sample_view.session.get('name') is None

    # Bind a widget that records kwargs and returns a scripted value.
    calls = []
    result = sample_view.bind_widget(
        'name',
        recording_widget(calls, 'Ada'),
        default='',
        label='Name',
    )

    # Assert the default was passed as value and the result was stored.
    assert calls == [{'label': 'Name', 'value': ''}]
    assert result == 'Ada'
    assert sample_view.session.get('name') == 'Ada'

# ** test: bind_widget_keeps_false_and_zero
def test_bind_widget_keeps_false_and_zero(sample_view: SampleView) -> None:
    '''
    Verify stored False and 0 are passed through, not replaced by default.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Store falsy values that must not fall back to default.
    sample_view.session.set('flag', False)
    sample_view.session.set('count', 0)

    # Bind widgets that would replace those values if the default were used.
    flag_calls = []
    count_calls = []
    flag = sample_view.bind_widget(
        'flag',
        recording_widget(flag_calls, False),
        default=True,
    )
    count = sample_view.bind_widget(
        'count',
        recording_widget(count_calls, 0),
        default=1,
    )

    # Assert the stored falsy values were passed through and kept.
    assert flag_calls == [{'value': False}]
    assert count_calls == [{'value': 0}]
    assert flag is False
    assert count == 0
    assert sample_view.session.get('flag') is False
    assert sample_view.session.get('count') == 0

# ** test: bind_widget_dispatch_skips_when_unchanged
def test_bind_widget_dispatch_skips_when_unchanged(sample_view: SampleView) -> None:
    '''
    Verify an equal before and after value does not call dispatch.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Store the value the widget will return.
    sample_view.session.set('amount', 3)
    sample_view.dispatch = MagicMock()

    # Bind a widget that returns the same value.
    calls = []
    result = sample_view.bind_widget_dispatch(
        'amount',
        recording_widget(calls, 3),
        'calc.update',
        default=0,
    )

    # Assert the stored value was passed through and dispatch was skipped.
    assert calls == [{'value': 3}]
    assert result == 3
    assert sample_view.session.get('amount') == 3
    sample_view.dispatch.assert_not_called()

# ** test: bind_widget_dispatch_sends_key_payload
def test_bind_widget_dispatch_sends_key_payload(sample_view: SampleView) -> None:
    '''
    Verify a change with no dispatch_data calls dispatch with the key payload.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Store a value that the widget will change.
    sample_view.session.set('amount', 1)
    sample_view.dispatch = MagicMock()

    # Bind a widget that returns a new value and supplies no dispatch_data.
    result = sample_view.bind_widget_dispatch(
        'amount',
        recording_widget([], 5),
        'calc.update',
    )

    # Assert the new value was stored and dispatched as the key payload.
    assert result == 5
    assert sample_view.session.get('amount') == 5
    sample_view.dispatch.assert_called_once_with('calc.update', amount=5)

# ** test: bind_widget_dispatch_uses_dispatch_data
def test_bind_widget_dispatch_uses_dispatch_data(sample_view: SampleView) -> None:
    '''
    Verify dispatch_data(new_value) supplies the dispatch keyword arguments.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Store a value that the widget will change.
    sample_view.session.set('amount', 1)
    sample_view.dispatch = MagicMock()

    # Map the new value to an explicit payload.
    def to_payload(value):
        '''Return keyword arguments for the new value.'''
        return {'total': value, 'unit': 'kg'}

    # Bind a widget that returns a new value.
    result = sample_view.bind_widget_dispatch(
        'amount',
        recording_widget([], 5),
        'calc.update',
        dispatch_data=to_payload,
    )

    # Assert the mapper supplied the keyword arguments.
    assert result == 5
    sample_view.dispatch.assert_called_once_with(
        'calc.update',
        total=5,
        unit='kg',
    )

# ** test: bind_trigger_dispatches_only_when_truthy
def test_bind_trigger_dispatches_only_when_truthy(
        sample_view: SampleView,
        mock_session_state: dict,
    ) -> None:
    '''
    Verify a falsy widget does not dispatch and a truthy widget does.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Replace dispatch and snapshot session state before either call.
    sample_view.dispatch = MagicMock()
    before = dict(mock_session_state)

    # Bind a falsy widget with no dispatch_data.
    falsy = sample_view.bind_trigger(
        recording_widget([], False),
        'data.load',
        label='Load',
    )

    # Assert the falsy result did not dispatch or touch session state.
    assert falsy is False
    sample_view.dispatch.assert_not_called()
    assert mock_session_state == before

    # Bind a truthy widget with no dispatch_data.
    truthy = sample_view.bind_trigger(
        recording_widget([], True),
        'data.load',
        label='Load',
    )

    # Assert the truthy result dispatched with no extra keywords.
    assert truthy is True
    sample_view.dispatch.assert_called_once_with('data.load')
    assert mock_session_state == before

# ** test: view_component_bind_uses_parent_session_and_dispatch
def test_view_component_bind_uses_parent_session_and_dispatch(
        sample_view: SampleView,
        mock_session_state: dict,
    ) -> None:
    '''
    Verify a component call writes the parent session and calls parent dispatch.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Replace parent dispatch so the component call can be asserted.
    sample_view.dispatch = MagicMock()
    comp = SampleComponent(ctx=sample_view)

    # Bind a changed value through the component.
    calls = []
    result = comp.bind_widget_dispatch(
        'choice',
        recording_widget(calls, 'new'),
        'feat.pick',
        default='old',
    )

    # Assert the parent session was read and written, and parent dispatch ran.
    assert calls == [{'value': 'old'}]
    assert result == 'new'
    assert sample_view.session.get('choice') == 'new'
    sample_view.dispatch.assert_called_once_with('feat.pick', choice='new')

    # Value sync also writes the parent session.
    label = comp.bind_widget(
        'label',
        recording_widget([], 'kept'),
        default='x',
    )
    assert label == 'kept'
    assert sample_view.session.get('label') == 'kept'

    # A truthy trigger calls the parent dispatch without writing session state.
    before = dict(mock_session_state)
    triggered = comp.bind_trigger(
        recording_widget([], True),
        'feat.go',
    )

    # Assert the parent dispatch ran and session state was unchanged.
    assert triggered is True
    sample_view.dispatch.assert_any_call('feat.go')
    assert mock_session_state == before
