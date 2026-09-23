'''Tiferet Streamlit – Audit Domain Objects'''

# *** imports

# ** core
from typing import Any, Dict, Literal

# ** infra
from pydantic import Field

# ** app
from tiferet.domain.core import DomainObject

# *** models

# ** model: dispatch_audit_record
class DispatchAuditRecord(DomainObject):
    '''
    Records the outcome of a single ``ViewContext.dispatch()`` call so that
    history can be observed after the fact. It does not replay the call.
    '''

    # * attribute: feature_id
    feature_id: str = Field(
        ...,
        description='The identifier of the dispatched feature.',
    )

    # * attribute: arguments
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description='The keyword arguments passed to the dispatched feature.',
    )

    # * attribute: outcome
    outcome: Literal['success', 'error'] = Field(
        ...,
        description='Whether the dispatch succeeded or raised an exception.',
    )

    # * attribute: result
    result: Any = Field(
        default=None,
        description='The feature result on success, or an error summary on failure.',
    )
