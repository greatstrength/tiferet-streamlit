"""Tiferet Streamlit Session Context Tests"""

# *** imports

# ** infra
import pytest

# ** app
from ..session import SessionCacheContext

# *** tests — no namespace

# ** test: get_returns_none_for_missing_key
def test_get_returns_none_for_missing_key(mock_session_state: dict) -> None:
    '''
    Test that get() returns None when the key does not exist.
    '''

    ctx = SessionCacheContext()

    assert ctx.get('missing') is None


# ** test: set_and_get_value
def test_set_and_get_value(mock_session_state: dict) -> None:
    '''
    Test that set() stores a value and get() retrieves it.
    '''

    ctx = SessionCacheContext()
    ctx.set('count', 42)

    assert ctx.get('count') == 42
    assert mock_session_state['count'] == 42


# ** test: set_overwrites_existing
def test_set_overwrites_existing(mock_session_state: dict) -> None:
    '''
    Test that set() overwrites an existing value.
    '''

    ctx = SessionCacheContext()
    ctx.set('count', 1)
    ctx.set('count', 2)

    assert ctx.get('count') == 2


# ** test: delete_removes_key
def test_delete_removes_key(mock_session_state: dict) -> None:
    '''
    Test that delete() removes the key from session state.
    '''

    ctx = SessionCacheContext()
    ctx.set('temp', 'value')
    ctx.delete('temp')

    assert ctx.get('temp') is None
    assert 'temp' not in mock_session_state


# ** test: delete_nonexistent_key_is_safe
def test_delete_nonexistent_key_is_safe(mock_session_state: dict) -> None:
    '''
    Test that deleting a nonexistent key does not raise.
    '''

    ctx = SessionCacheContext()
    ctx.delete('nonexistent')  # must not raise


# ** test: clear_removes_all_keys
def test_clear_removes_all_keys(mock_session_state: dict) -> None:
    '''
    Test that clear() without a namespace removes all session state.
    '''

    ctx = SessionCacheContext()
    ctx.set('a', 1)
    ctx.set('b', 2)
    ctx.clear()

    assert len(mock_session_state) == 0


# *** tests — with namespace

# ** test: namespace_key_isolation
def test_namespace_key_isolation(mock_session_state: dict) -> None:
    '''
    Test that namespaced keys are isolated from each other.
    '''

    ctx_a = SessionCacheContext(namespace='view_a')
    ctx_b = SessionCacheContext(namespace='view_b')

    ctx_a.set('count', 10)
    ctx_b.set('count', 20)

    assert ctx_a.get('count') == 10
    assert ctx_b.get('count') == 20
    assert mock_session_state['view_a.count'] == 10
    assert mock_session_state['view_b.count'] == 20


# ** test: namespace_get_returns_none_for_other_namespace
def test_namespace_get_returns_none_for_other_namespace(mock_session_state: dict) -> None:
    '''
    Test that get() with namespace does not see keys from another namespace.
    '''

    ctx_a = SessionCacheContext(namespace='view_a')
    ctx_b = SessionCacheContext(namespace='view_b')

    ctx_a.set('value', 'hello')

    assert ctx_b.get('value') is None


# ** test: namespace_delete
def test_namespace_delete(mock_session_state: dict) -> None:
    '''
    Test that delete() only removes the namespaced key.
    '''

    ctx_a = SessionCacheContext(namespace='view_a')
    ctx_b = SessionCacheContext(namespace='view_b')

    ctx_a.set('x', 1)
    ctx_b.set('x', 2)
    ctx_a.delete('x')

    assert ctx_a.get('x') is None
    assert ctx_b.get('x') == 2


# ** test: namespace_clear_only_clears_own_keys
def test_namespace_clear_only_clears_own_keys(mock_session_state: dict) -> None:
    '''
    Test that clear() only removes keys from the current namespace.
    '''

    ctx_a = SessionCacheContext(namespace='view_a')
    ctx_b = SessionCacheContext(namespace='view_b')

    ctx_a.set('x', 1)
    ctx_a.set('y', 2)
    ctx_b.set('z', 3)

    ctx_a.clear()

    assert ctx_a.get('x') is None
    assert ctx_a.get('y') is None
    assert ctx_b.get('z') == 3
    assert 'view_b.z' in mock_session_state


# ** test: set_complex_value
def test_set_complex_value(mock_session_state: dict) -> None:
    '''
    Test that session cache can store complex types (dicts, lists).
    '''

    ctx = SessionCacheContext(namespace='test')
    ctx.set('data', {'items': [1, 2, 3], 'nested': {'a': True}})

    result = ctx.get('data')

    assert result == {'items': [1, 2, 3], 'nested': {'a': True}}


# ** test: empty_namespace_behaves_like_no_namespace
def test_empty_namespace_behaves_like_no_namespace(mock_session_state: dict) -> None:
    '''
    Test that an empty string namespace stores keys without a prefix.
    '''

    ctx = SessionCacheContext(namespace='')
    ctx.set('key', 'value')

    assert mock_session_state.get('key') == 'value'
