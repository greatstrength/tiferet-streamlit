'''Tiferet Streamlit – View Contexts'''

# *** imports

# ** core
from typing import Any, Dict

# ** infra
from tiferet.contexts.app import AppInterfaceContext

# ** app
from .session import SessionCacheContext

# *** contexts

# ** context: view_context
class ViewContext(object):
    '''
    The code-behind for a Streamlit page. Manages state via
    SessionCacheContext, dispatches Tiferet features via
    AppInterfaceContext, and defines Streamlit widgets through
    an overridable render() method.
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
            session: SessionCacheContext = None,
        ):
        '''
        Initialize the view context.

        :param app: Tiferet interface context for feature dispatch.
        :type app: AppInterfaceContext
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

        # Append the record to this view's namespaced audit log.
        log = self.session.get('_audit_log') or []
        log.append({
            'feature_id': feature_id,
            'arguments': data,
            'outcome': outcome,
            'result': result,
        })
        self.session.set('_audit_log', log)

    # * method: audit_log
    def audit_log(self) -> list:
        '''
        Return this view's dispatch audit log.

        :return: The list of recorded dispatch outcomes, oldest first.
        :rtype: list
        '''

        # Return the namespaced audit log, defaulting to an empty list.
        return self.session.get('_audit_log') or []

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
        Delegates to render().
        '''

        # Delegate to render.
        return self.render()


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
