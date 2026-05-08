"""Tiferet Streamlit View Context Tests"""

# *** imports

# ** core
from unittest import mock
from typing import Any, Dict

# ** infra
import pytest

# ** app
from ..session import SessionCacheContext
from ..view import ViewContext, ViewComponent

# *** helpers

# ** helper: concrete_view_context
class SampleView(ViewContext):
    '''
    A concrete ViewContext subclass for testing.
    '''

    # * method: init_state
    def init_state(self):
        self.session.set('counter', 0)

    # * method: render
    def render(self):
        pass


# ** helper: rendering_view_context
class RenderingView(ViewContext):
    '''
    A ViewContext that tracks render calls.
    '''

    # * method: init_state
    def init_state(self):
        self.session.set('render_count', 0)

    # * method: render
    def render(self):
        count = self.session.get('render_count') or 0
        self.session.set('render_count', count + 1)


# ** helper: sample_component
class SampleComponent(ViewComponent):
    '''
    A concrete ViewComponent subclass for testing.
    '''

    # * method: render
    def render(self, label: str = 'default', **props):
        self.ctx.session.set(f'component_{label}', True)


# *** fixtures

# ** fixture: mock_app
@pytest.fixture
def mock_app():
    '''
    A mock AppInterfaceContext for testing dispatch.
    '''
    app = mock.MagicMock()
    app.run.return_value = 'mock_result'
    return app


# ** fixture: sample_view
@pytest.fixture
def sample_view(mock_app) -> SampleView:
    '''
    A SampleView instance with mocked app.
    '''
    return SampleView(app=mock_app, key='test_view')


# *** tests — ViewContext lifecycle

# ** test: init_state_called_once
def test_init_state_called_once(mock_app, mock_session_state: dict) -> None:
    '''
    Test that init_state() is called exactly once on first construction.
    '''

    view = SampleView(app=mock_app, key='test')

    assert view.session.get('counter') == 0
    assert view.session.get('_initialized') is True


# ** test: init_state_not_called_again
def test_init_state_not_called_again(mock_app, mock_session_state: dict) -> None:
    '''
    Test that constructing a second ViewContext with the same key
    does not re-run init_state().
    '''

    view1 = SampleView(app=mock_app, key='test')
    view1.session.set('counter', 99)

    # Second construction with the same key should not reset counter.
    view2 = SampleView(app=mock_app, key='test')

    assert view2.session.get('counter') == 99


# ** test: default_init_state_is_noop
def test_default_init_state_is_noop(mock_app, mock_session_state: dict) -> None:
    '''
    Test that the base ViewContext.init_state() is a no-op.
    '''

    # Use base ViewContext directly (render will raise, but init should not).
    class MinimalView(ViewContext):
        def render(self):
            pass

    view = MinimalView(app=mock_app, key='minimal')

    # Only _initialized should be set.
    assert view.session.get('_initialized') is True


# *** tests — ViewContext dispatch

# ** test: dispatch_calls_app_run
def test_dispatch_calls_app_run(sample_view: SampleView, mock_app) -> None:
    '''
    Test that dispatch() delegates to app.run with correct arguments.
    '''

    result = sample_view.dispatch('calc.add', a=1, b=2)

    mock_app.run.assert_called_once_with(
        feature_id='calc.add',
        headers={},
        data={'a': 1, 'b': 2},
    )
    assert result == 'mock_result'


# ** test: dispatch_with_headers
def test_dispatch_with_headers(sample_view: SampleView, mock_app) -> None:
    '''
    Test that dispatch() passes custom headers to app.run.
    '''

    sample_view.dispatch('calc.add', headers={'lang': 'en_US'}, a=1, b=2)

    mock_app.run.assert_called_once_with(
        feature_id='calc.add',
        headers={'lang': 'en_US'},
        data={'a': 1, 'b': 2},
    )


# *** tests — ViewContext render

# ** test: render_raises_not_implemented
def test_render_raises_not_implemented(mock_app, mock_session_state: dict) -> None:
    '''
    Test that the base ViewContext.render() raises NotImplementedError.
    '''

    class UnimplementedView(ViewContext):
        pass

    view = UnimplementedView(app=mock_app, key='unimpl')

    with pytest.raises(NotImplementedError):
        view.render()


# ** test: callable_delegates_to_render
def test_callable_delegates_to_render(mock_app, mock_session_state: dict) -> None:
    '''
    Test that calling a ViewContext invokes render().
    '''

    view = RenderingView(app=mock_app, key='renderable')
    view()

    assert view.session.get('render_count') == 1


# ** test: multiple_renders_accumulate
def test_multiple_renders_accumulate(mock_app, mock_session_state: dict) -> None:
    '''
    Test that multiple render() calls accumulate state.
    '''

    view = RenderingView(app=mock_app, key='renderable')
    view()
    view()
    view()

    assert view.session.get('render_count') == 3


# *** tests — ViewContext session namespace

# ** test: session_namespace_matches_key
def test_session_namespace_matches_key(mock_app, mock_session_state: dict) -> None:
    '''
    Test that auto-created session uses the view key as namespace.
    '''

    view = SampleView(app=mock_app, key='my_view')

    assert view.session.namespace == 'my_view'


# ** test: custom_session_is_used
def test_custom_session_is_used(mock_app, mock_session_state: dict) -> None:
    '''
    Test that a custom session passed to ViewContext is used instead of auto-creating one.
    '''

    custom = SessionCacheContext(namespace='custom_ns')
    view = SampleView(app=mock_app, key='view', session=custom)

    assert view.session is custom
    assert view.session.namespace == 'custom_ns'


# *** tests — ViewComponent

# ** test: component_render
def test_component_render(sample_view: SampleView) -> None:
    '''
    Test that ViewComponent.render() executes with props.
    '''

    comp = SampleComponent(sample_view)
    comp.render(label='btn')

    assert sample_view.session.get('component_btn') is True


# ** test: component_callable
def test_component_callable(sample_view: SampleView) -> None:
    '''
    Test that calling a ViewComponent invokes render() with props.
    '''

    comp = SampleComponent(sample_view)
    comp(label='input')

    assert sample_view.session.get('component_input') is True


# ** test: component_default_props
def test_component_default_props(sample_view: SampleView) -> None:
    '''
    Test that ViewComponent uses default prop values.
    '''

    comp = SampleComponent(sample_view)
    comp()

    assert sample_view.session.get('component_default') is True


# ** test: component_accesses_parent_dispatch
def test_component_accesses_parent_dispatch(sample_view: SampleView, mock_app) -> None:
    '''
    Test that a ViewComponent can access dispatch via its parent context.
    '''

    class DispatchingComponent(ViewComponent):
        def render(self, feature_id: str = 'test.feature', **props):
            result = self.ctx.dispatch(feature_id)
            self.ctx.session.set('dispatch_result', result)

    comp = DispatchingComponent(sample_view)
    comp(feature_id='calc.add')

    assert sample_view.session.get('dispatch_result') == 'mock_result'
    mock_app.run.assert_called_once()


# ** test: component_raises_not_implemented
def test_component_raises_not_implemented(sample_view: SampleView) -> None:
    '''
    Test that the base ViewComponent.render() raises NotImplementedError.
    '''

    comp = ViewComponent(sample_view)

    with pytest.raises(NotImplementedError):
        comp.render()
