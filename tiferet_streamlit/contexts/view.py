'''Tiferet Streamlit – View Contexts'''

# *** imports

# ** core
from typing import Any, Dict, List

# ** infra
from tiferet.contexts.app import AppSessionContext

# ** app
from ..domain import DispatchAuditRecord
from .session import SessionCacheContext

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
