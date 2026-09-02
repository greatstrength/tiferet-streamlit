'''Tiferet Streamlit – View Context Tests'''

# *** imports

# ** infra
import pytest
from unittest.mock import MagicMock

# ** app
from tiferet import TiferetError
from tiferet_streamlit.assets.constants import VIEW_RENDER_FAILED_ID
from tiferet_streamlit.contexts.session import SessionCacheContext
from tiferet_streamlit.contexts.view import ViewContext, ViewComponent
from tiferet_streamlit.domain.audit import DispatchAuditRecord

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

# ** helper: failing_view
class FailingView(ViewContext):
    '''
    Concrete ViewContext whose render() always raises.
    '''

    # * method: render
    def render(self):
        '''Raise an arbitrary exception to simulate a render failure.'''
        raise ValueError('boom')

# ** helper: sample_component
class SampleComponent(ViewComponent):
    '''
    Concrete ViewComponent for testing.
    '''

    # * method: render
    def render(self, **props):
        '''Render the component with props.'''
        return props

# *** fixtures

# ** fixture: mock_app
@pytest.fixture
def mock_app() -> MagicMock:
    '''
    MagicMock with run returning 'mock_result'.

    :return: A mocked AppInterfaceContext.
    :rtype: MagicMock
    '''

    # Create a mock app context.
    app = MagicMock()
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

# *** tests: view_context dispatch audit log

# ** test: dispatch_success_is_logged
def test_dispatch_success_is_logged(sample_view: SampleView) -> None:
    '''
    Verify a successful dispatch appends a success record to the audit log.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Dispatch a feature.
    result = sample_view.dispatch('calc.add', a=1, b=2)

    # Assert the audit log contains the success record.
    log = sample_view.audit_log
    assert len(log) == 1
    assert isinstance(log[0], DispatchAuditRecord)
    assert log[0].feature_id == 'calc.add'
    assert log[0].arguments == {'a': 1, 'b': 2}
    assert log[0].outcome == 'success'
    assert log[0].result == result

# ** test: dispatch_failure_is_logged_and_raised
def test_dispatch_failure_is_logged_and_raised(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify a failed dispatch appends an error record and re-raises unchanged.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Configure the app to raise on run.
    mock_app.run.side_effect = ValueError('boom')

    # Assert the original exception propagates unchanged.
    with pytest.raises(ValueError, match='boom'):
        sample_view.dispatch('calc.add', a=1, b=2)

    # Assert the audit log contains the error record.
    log = sample_view.audit_log
    assert len(log) == 1
    assert log[0].feature_id == 'calc.add'
    assert log[0].arguments == {'a': 1, 'b': 2}
    assert log[0].outcome == 'error'

# ** test: audit_log_is_namespaced_per_view
def test_audit_log_is_namespaced_per_view(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify the audit log is isolated per view namespace.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create two distinct views and dispatch on one of them.
    view_a = SampleView(app=mock_app, key='view_a')
    view_b = SampleView(app=mock_app, key='view_b')
    view_a.dispatch('calc.add', a=1, b=2)

    # Assert only the dispatching view's log is populated.
    assert len(view_a.audit_log) == 1
    assert len(view_b.audit_log) == 0

# *** tests: view_context bind_widget

# ** test: bind_widget_seeds_default_on_first_render
def test_bind_widget_seeds_default_on_first_render(sample_view: SampleView) -> None:
    '''
    Verify bind_widget seeds the widget with the default when unset.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Stand in for a native Streamlit widget.
    widget = MagicMock(return_value='typed')

    # Bind the widget with a default.
    result = sample_view.bind_widget('name', widget, default='guest')

    # Assert the widget was seeded with the default value.
    widget.assert_called_once_with(value='guest')

    # Assert the return value was written back and returned.
    assert result == 'typed'
    assert sample_view.session.get('name') == 'typed'

# ** test: bind_widget_seeds_stored_value_on_rerun
def test_bind_widget_seeds_stored_value_on_rerun(sample_view: SampleView) -> None:
    '''
    Verify bind_widget seeds the widget with the previously stored value.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Pre-seed the stored value from a prior rerun.
    sample_view.session.set('name', 'stored')

    # Stand in for a native Streamlit widget.
    widget = MagicMock(return_value='stored')

    # Bind the widget.
    sample_view.bind_widget('name', widget, default='guest')

    # Assert the widget was seeded with the stored value, not the default.
    widget.assert_called_once_with(value='stored')

# ** test: bind_widget_forwards_kwargs_untouched
def test_bind_widget_forwards_kwargs_untouched(sample_view: SampleView) -> None:
    '''
    Verify widget-specific keyword arguments are forwarded untouched.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Stand in for a native Streamlit widget.
    widget = MagicMock(return_value=5)

    # Bind the widget with extra widget-specific kwargs.
    sample_view.bind_widget('count', widget, default=0, min_value=0, max_value=10)

    # Assert the extra kwargs were forwarded alongside the injected value.
    widget.assert_called_once_with(value=0, min_value=0, max_value=10)

# ** test: bind_widget_respects_custom_value_param
def test_bind_widget_respects_custom_value_param(sample_view: SampleView) -> None:
    '''
    Verify a custom value_param name is used to seed the widget.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Stand in for a native Streamlit widget that uses 'index' instead of 'value'.
    widget = MagicMock(return_value='b')

    # Bind the widget with a custom value_param.
    sample_view.bind_widget('choice', widget, value_param='index', default='a')

    # Assert the widget was seeded via the custom kwarg name.
    widget.assert_called_once_with(index='a')

# *** tests: view_context bind_widget_dispatch

# ** test: bind_widget_dispatch_dispatches_on_change
def test_bind_widget_dispatch_dispatches_on_change(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify dispatch is called with the default {key: value} payload on change.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Simulate a user typing a new value.
    widget = MagicMock(return_value='new value')

    # Bind with dispatch.
    result = sample_view.bind_widget_dispatch('name', widget, 'greet.user')

    # Assert the feature was dispatched with the default payload shape.
    mock_app.run.assert_called_once_with(
        feature_id='greet.user',
        headers={},
        data={'name': 'new value'},
    )
    assert result == 'new value'

# ** test: bind_widget_dispatch_skips_dispatch_when_unchanged
def test_bind_widget_dispatch_skips_dispatch_when_unchanged(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify dispatch is not called when the value is unchanged across a rerun.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Pre-seed the stored value to simulate a prior rerun.
    sample_view.session.set('name', 'same')

    # Simulate the widget returning the same value on rerun.
    widget = MagicMock(return_value='same')

    # Bind with dispatch.
    sample_view.bind_widget_dispatch('name', widget, 'greet.user')

    # Assert no dispatch occurred.
    mock_app.run.assert_not_called()

# ** test: bind_widget_dispatch_uses_custom_dispatch_data
def test_bind_widget_dispatch_uses_custom_dispatch_data(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify a custom dispatch_data callable overrides the default payload shape.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Simulate a user typing a new value.
    widget = MagicMock(return_value='new value')

    # Bind with a custom dispatch_data mapping.
    sample_view.bind_widget_dispatch(
        'name',
        widget,
        'greet.user',
        dispatch_data=lambda value: {'entered_name': value, 'source': 'form'},
    )

    # Assert the custom payload shape was used.
    mock_app.run.assert_called_once_with(
        feature_id='greet.user',
        headers={},
        data={'entered_name': 'new value', 'source': 'form'},
    )

# ** test: bind_widget_dispatch_is_audited
def test_bind_widget_dispatch_is_audited(sample_view: SampleView) -> None:
    '''
    Verify a dispatch triggered by bind_widget_dispatch is recorded in the audit log.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Simulate a user typing a new value.
    widget = MagicMock(return_value='new value')
    sample_view.bind_widget_dispatch('name', widget, 'greet.user')

    # Assert the dispatch was recorded, since bind_widget_dispatch calls self.dispatch().
    assert len(sample_view.audit_log) == 1
    assert sample_view.audit_log[0].feature_id == 'greet.user'

# *** tests: view_context bind_trigger

# ** test: bind_trigger_dispatches_on_truthy_return
def test_bind_trigger_dispatches_on_truthy_return(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify a trigger widget dispatches unconditionally on a truthy return.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Simulate a clicked button.
    widget = MagicMock(return_value=True)

    # Bind the trigger.
    result = sample_view.bind_trigger(widget, 'calc.reset')

    # Assert the feature was dispatched with an empty default payload.
    mock_app.run.assert_called_once_with(
        feature_id='calc.reset',
        headers={},
        data={},
    )
    assert result is True

# ** test: bind_trigger_skips_dispatch_on_falsy_return
def test_bind_trigger_skips_dispatch_on_falsy_return(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify a trigger widget does not dispatch when its return is falsy.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Simulate a button that was not clicked this rerun.
    widget = MagicMock(return_value=False)

    # Bind the trigger.
    result = sample_view.bind_trigger(widget, 'calc.reset')

    # Assert no dispatch occurred.
    mock_app.run.assert_not_called()
    assert result is False

# ** test: bind_trigger_uses_custom_dispatch_data
def test_bind_trigger_uses_custom_dispatch_data(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify a custom dispatch_data callable supplies the dispatch payload.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Simulate a clicked submit button.
    widget = MagicMock(return_value=True)

    # Bind the trigger with a custom payload.
    sample_view.bind_trigger(widget, 'form.submit', dispatch_data=lambda: {'confirmed': True})

    # Assert the custom payload was dispatched.
    mock_app.run.assert_called_once_with(
        feature_id='form.submit',
        headers={},
        data={'confirmed': True},
    )

# ** test: bind_trigger_has_no_stored_previous_value
def test_bind_trigger_has_no_stored_previous_value(sample_view: SampleView, mock_session_state: dict) -> None:
    '''
    Verify bind_trigger writes nothing to the session cache.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Snapshot the namespace's keys before the trigger.
    before_keys = {k for k in mock_session_state if k.startswith('test_view.')}

    # Simulate a clicked button.
    widget = MagicMock(return_value=True)
    sample_view.bind_trigger(widget, 'calc.reset')

    # Assert bind_trigger itself wrote no widget-value key; the only new key
    # is the audit log entry, which is dispatch()'s own side effect (RFP-002),
    # not something bind_trigger writes.
    after_keys = {k for k in mock_session_state if k.startswith('test_view.')}
    assert after_keys - before_keys <= {'test_view._audit_log'}

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

# *** tests: view_context render failure hardening

# ** test: callable_wraps_render_failure
def test_callable_wraps_render_failure(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify __call__() wraps a concrete render() failure into a structured
    TiferetError carrying VIEW_RENDER_FAILED_ID.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a view whose render() always raises.
    view = FailingView(app=mock_app, key='failing_view')

    # Assert calling the view raises a structured TiferetError.
    with pytest.raises(TiferetError) as exc_info:
        view()

    # Assert the structured error carries VIEW_RENDER_FAILED_ID.
    assert exc_info.value.error_code == VIEW_RENDER_FAILED_ID

# ** test: callable_wraps_render_failure_preserves_chain
def test_callable_wraps_render_failure_preserves_chain(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify the original exception is preserved via exception chaining.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a view whose render() always raises.
    view = FailingView(app=mock_app, key='failing_view')

    # Assert the original exception is chained as the cause.
    with pytest.raises(TiferetError) as exc_info:
        view()

    assert isinstance(exc_info.value.__cause__, ValueError)
    assert str(exc_info.value.__cause__) == 'boom'

# ** test: callable_does_not_wrap_default_not_implemented
def test_callable_does_not_wrap_default_not_implemented(mock_app: MagicMock, mock_session_state: dict) -> None:
    '''
    Verify the default, unoverridden render()'s NotImplementedError
    propagates through __call__() unwrapped.

    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a base ViewContext (render not overridden).
    class BareView(ViewContext):
        pass

    view = BareView(app=mock_app, key='bare_call')

    # Assert calling the view raises the raw NotImplementedError, not a
    # wrapped TiferetError.
    with pytest.raises(NotImplementedError):
        view()

# *** tests: view_component bind delegation

# ** test: component_bind_widget_delegates_to_ctx
def test_component_bind_widget_delegates_to_ctx(sample_view: SampleView) -> None:
    '''
    Verify ViewComponent.bind_widget delegates to the parent ctx and shares state.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    '''

    # Stand in for a native Streamlit widget.
    widget = MagicMock(return_value='typed')

    # Bind the widget through the component.
    comp = ViewComponent(ctx=sample_view)
    result = comp.bind_widget('name', widget, default='guest')

    # Assert the result and stored value are visible through the parent view.
    assert result == 'typed'
    assert sample_view.session.get('name') == 'typed'

# ** test: component_bind_widget_dispatch_delegates_to_ctx
def test_component_bind_widget_dispatch_delegates_to_ctx(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify ViewComponent.bind_widget_dispatch delegates to the parent ctx.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Simulate a user typing a new value.
    widget = MagicMock(return_value='new value')

    # Bind with dispatch through the component.
    comp = ViewComponent(ctx=sample_view)
    comp.bind_widget_dispatch('name', widget, 'greet.user')

    # Assert the feature was dispatched via the parent ctx.
    mock_app.run.assert_called_once_with(
        feature_id='greet.user',
        headers={},
        data={'name': 'new value'},
    )

# ** test: component_bind_trigger_delegates_to_ctx
def test_component_bind_trigger_delegates_to_ctx(sample_view: SampleView, mock_app: MagicMock) -> None:
    '''
    Verify ViewComponent.bind_trigger delegates to the parent ctx.

    :param sample_view: The sample view instance.
    :type sample_view: SampleView
    :param mock_app: The mocked app context.
    :type mock_app: MagicMock
    '''

    # Simulate a clicked button.
    widget = MagicMock(return_value=True)

    # Bind the trigger through the component.
    comp = ViewComponent(ctx=sample_view)
    result = comp.bind_trigger(widget, 'calc.reset')

    # Assert the feature was dispatched and the result was returned.
    mock_app.run.assert_called_once_with(
        feature_id='calc.reset',
        headers={},
        data={},
    )
    assert result is True
