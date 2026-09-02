'''Tiferet Streamlit – Audit Domain Object Tests'''

# *** imports

# ** infra
import pytest
from pydantic import ValidationError

# ** app
from tiferet_streamlit.domain.audit import DispatchAuditRecord

# *** fixtures

# ** fixture: sample_record_data
@pytest.fixture
def sample_record_data() -> dict:
    '''
    Dict with minimal valid DispatchAuditRecord fields.

    :return: A dictionary of sample audit record data.
    :rtype: dict
    '''

    return dict(
        feature_id='calc.add',
        arguments={'a': 1, 'b': 2},
        outcome='success',
        result=3,
    )

# ** fixture: sample_record
@pytest.fixture
def sample_record(sample_record_data: dict) -> DispatchAuditRecord:
    '''
    DispatchAuditRecord instance constructed from sample_record_data.

    :param sample_record_data: The sample audit record data dictionary.
    :type sample_record_data: dict
    :return: A DispatchAuditRecord instance.
    :rtype: DispatchAuditRecord
    '''

    return DispatchAuditRecord(**sample_record_data)

# *** tests

# ** test: record_required_fields
def test_record_required_fields(sample_record: DispatchAuditRecord, sample_record_data: dict) -> None:
    '''
    Verify required fields are stored correctly.

    :param sample_record: The sample DispatchAuditRecord instance.
    :type sample_record: DispatchAuditRecord
    :param sample_record_data: The sample audit record data dictionary.
    :type sample_record_data: dict
    '''

    # Assert each field matches the input data.
    assert sample_record.feature_id == sample_record_data['feature_id']
    assert sample_record.arguments == sample_record_data['arguments']
    assert sample_record.outcome == sample_record_data['outcome']
    assert sample_record.result == sample_record_data['result']

# ** test: record_default_arguments_empty
def test_record_default_arguments_empty() -> None:
    '''
    Verify arguments defaults to an empty dict.
    '''

    # Create a record without explicit arguments.
    record = DispatchAuditRecord(feature_id='calc.add', outcome='success')

    # Assert the default arguments value.
    assert record.arguments == {}

# ** test: record_default_result_none
def test_record_default_result_none() -> None:
    '''
    Verify result defaults to None.
    '''

    # Create a record without an explicit result.
    record = DispatchAuditRecord(feature_id='calc.add', outcome='error')

    # Assert the default result value.
    assert record.result is None

# ** test: record_rejects_invalid_outcome
def test_record_rejects_invalid_outcome(sample_record_data: dict) -> None:
    '''
    Verify an outcome outside the success/error literal is rejected.

    :param sample_record_data: The sample audit record data dictionary.
    :type sample_record_data: dict
    '''

    # Attempt to create a record with an invalid outcome.
    with pytest.raises(ValidationError):
        DispatchAuditRecord(**{**sample_record_data, 'outcome': 'pending'})

# ** test: record_rejects_extra_fields
def test_record_rejects_extra_fields(sample_record_data: dict) -> None:
    '''
    Verify DomainObject(extra='forbid') rejects unknown fields.

    :param sample_record_data: The sample audit record data dictionary.
    :type sample_record_data: dict
    '''

    # Attempt to create a record with an extra field.
    with pytest.raises(ValidationError):
        DispatchAuditRecord(**{**sample_record_data, 'unknown_field': 'value'})

# ** test: record_round_trips_through_model_dump
def test_record_round_trips_through_model_dump(sample_record: DispatchAuditRecord) -> None:
    '''
    Verify a record serialized via model_dump() reconstructs identically.

    :param sample_record: The sample DispatchAuditRecord instance.
    :type sample_record: DispatchAuditRecord
    '''

    # Serialize then reconstruct the record.
    primitive = sample_record.model_dump()
    rebuilt = DispatchAuditRecord(**primitive)

    # Assert the reconstructed record matches the original.
    assert rebuilt == sample_record
