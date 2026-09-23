'''Tiferet Streamlit – View Context Tests'''

# *** imports

# ** infra
import pytest
from unittest.mock import MagicMock
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
