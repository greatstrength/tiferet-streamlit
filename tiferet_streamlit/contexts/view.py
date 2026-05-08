"""Tiferet Streamlit View Context"""

# *** imports

# ** core
from typing import Any, Dict

# ** app
from tiferet.contexts.app import AppInterfaceContext
from .session import SessionCacheContext

# *** contexts

# ** context: view_context
class ViewContext(object):
    '''
    The code-behind for a Streamlit view, analogous to a React class component.

    Manages state (via SessionCacheContext), exposes actions (via Tiferet
    feature dispatch), and defines rendering (Streamlit widgets) through
    a subclass-overridable render() method.

    Lifecycle:
    - init_state() runs once on first render (persisted via session).
    - render() runs on every Streamlit rerun.
    '''

    # * attribute: app
    app: AppInterfaceContext

    # * attribute: key
    key: str

    # * attribute: session
    session: SessionCacheContext

    # * init
    def __init__(self,
            app: AppInterfaceContext,
            key: str,
            session: SessionCacheContext = None):
        '''
        Initialize the view context.

        :param app: The Tiferet application interface context for feature dispatch.
        :type app: AppInterfaceContext
        :param key: A unique key identifying this view instance (used for state namespacing).
        :type key: str
        :param session: An optional session cache context. If not provided, one is created
            with the view key as namespace.
        :type session: SessionCacheContext
        '''

        # Assign the app interface context.
        self.app = app

        # Assign the view key.
        self.key = key

        # Assign or create the session cache context with the view key as namespace.
        self.session = session or SessionCacheContext(namespace=key)

        # Run init_state once (on first render) and mark as initialized.
        if not self.session.get('_initialized'):
            self.init_state()
            self.session.set('_initialized', True)

    # * method: init_state
    def init_state(self):
        '''
        Initialize the view's state. Called once on first render.

        Override this method to set initial state values via self.session.set(...).
        '''

        # No-op by default; subclasses override.
        pass

    # * method: dispatch
    def dispatch(self, feature_id: str, headers: Dict[str, str] = None, **data) -> Any:
        '''
        Execute a Tiferet feature and return the result.

        :param feature_id: The feature identifier to execute.
        :type feature_id: str
        :param headers: Optional request headers.
        :type headers: Dict[str, str]
        :param data: The data to pass to the feature.
        :type data: dict
        :return: The feature execution result.
        :rtype: Any
        '''

        # Execute the feature via the app interface context.
        return self.app.run(
            feature_id=feature_id,
            headers=headers or {},
            data=data,
        )

    # * method: render
    def render(self):
        '''
        Define the Streamlit widgets for this view.

        Override this method to compose the view's UI using Streamlit calls
        and self.session for state, self.dispatch() for actions.
        '''

        # Not implemented; subclasses must override.
        raise NotImplementedError()

    # * method: __call__
    def __call__(self):
        '''
        Render the view. Makes ViewContext callable for Streamlit composition
        (e.g., passing to st.Page or embedding in another view).
        '''

        # Delegate to render.
        self.render()


# ** context: view_component
class ViewComponent(object):
    '''
    A composable, prop-driven sub-component for Streamlit views.

    Lighter-weight than ViewContext: receives props, accesses a parent
    ViewContext for state and actions, and renders Streamlit widgets.
    Analogous to a React functional component.
    '''

    # * attribute: ctx
    ctx: ViewContext

    # * init
    def __init__(self, ctx: ViewContext):
        '''
        Initialize the view component.

        :param ctx: The parent view context providing state and action access.
        :type ctx: ViewContext
        '''

        # Assign the parent view context.
        self.ctx = ctx

    # * method: render
    def render(self, **props):
        '''
        Define the Streamlit widgets for this component.

        Override this method to compose the component's UI using Streamlit calls,
        self.ctx.session for state, and self.ctx.dispatch() for actions.

        :param props: Properties passed to the component for rendering.
        :type props: dict
        '''

        # Not implemented; subclasses must override.
        raise NotImplementedError()

    # * method: __call__
    def __call__(self, **props):
        '''
        Render the component with the given props.

        :param props: Properties passed to the component for rendering.
        :type props: dict
        '''

        # Delegate to render.
        self.render(**props)
