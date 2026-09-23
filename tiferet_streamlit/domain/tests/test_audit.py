'''Tiferet Streamlit – Dispatch Audit Record Tests'''

# *** imports

# ** infra
import pytest
from pydantic import ValidationError

# ** app
from tiferet_streamlit import DispatchAuditRecord as PackageDispatchAuditRecord
from tiferet_streamlit.domain import DispatchAuditRecord

# *** tests

# ** test: dispatch_audit_record_requires_feature_id_and_outcome
def test_dispatch_audit_record_requires_feature_id_and_outcome() -> None:
    '''
    Verify constructing without feature_id or without outcome is rejected.
    '''

    # Omit the feature identifier.
    with pytest.raises(ValidationError):
        DispatchAuditRecord(outcome='success')

    # Omit the outcome.
    with pytest.raises(ValidationError):
        DispatchAuditRecord(feature_id='group.feature')


# ** test: dispatch_audit_record_rejects_unknown_outcome
def test_dispatch_audit_record_rejects_unknown_outcome() -> None:
    '''
    Verify an outcome outside success and error is rejected.
    '''

    # Attempt an outcome the literal does not allow.
    with pytest.raises(ValidationError):
        DispatchAuditRecord(
            feature_id='group.feature',
            outcome='failed',
        )


# ** test: dispatch_audit_record_defaults_arguments_and_result
def test_dispatch_audit_record_defaults_arguments_and_result() -> None:
    '''
    Verify omitted arguments default to an empty dict and omitted result to None.
    '''

    # Construct with only the required fields.
    record = DispatchAuditRecord(
        feature_id='group.feature',
        outcome='success',
    )

    # Assert the documented defaults.
    assert record.arguments == {}
    assert record.result is None

    # Assert the model is the public export.
    assert PackageDispatchAuditRecord is DispatchAuditRecord


# ** test: dispatch_audit_record_round_trip
def test_dispatch_audit_record_round_trip() -> None:
    '''
    Verify model_dump reconstructs the original field values.
    '''

    # Record one failed dispatch with arguments and an error summary.
    record = DispatchAuditRecord(
        feature_id='group.feature',
        arguments={'left': 1, 'right': 2},
        outcome='error',
        result={'code': 'FEATURE_NOT_FOUND'},
    )

    # Reconstruct from the dumped fields.
    restored = DispatchAuditRecord(**record.model_dump())

    # Assert each field matches the original.
    assert restored.feature_id == record.feature_id
    assert restored.arguments == record.arguments
    assert restored.outcome == record.outcome
    assert restored.result == record.result
