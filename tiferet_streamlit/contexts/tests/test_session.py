'''Tiferet Streamlit – Session Cache Context Tests'''

# *** imports

# ** infra
import pytest

# ** app
from tiferet_streamlit.contexts.session import SessionCacheContext

# *** tests: no-namespace

# ** test: get_returns_none_for_missing_key
def test_get_returns_none_for_missing_key(mock_session_state: dict) -> None:
    '''
    Verify get returns None when the key does not exist.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a context without namespace.
    ctx = SessionCacheContext()

    # Assert get returns None for a missing key.
    assert ctx.get('missing') is None


# ** test: set_and_get_value
def test_set_and_get_value(mock_session_state: dict) -> None:
    '''
    Verify set stores a value and get retrieves it. Also verifies the key
    exists in the mock state.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a context and set a value.
    ctx = SessionCacheContext()
    ctx.set('foo', 42)

    # Assert the value is retrievable.
    assert ctx.get('foo') == 42

    # Assert the key exists in the underlying state.
    assert 'foo' in mock_session_state


# ** test: set_overwrites_existing
def test_set_overwrites_existing(mock_session_state: dict) -> None:
    '''
    Verify set overwrites an existing value.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a context and set then overwrite a value.
    ctx = SessionCacheContext()
    ctx.set('key', 'first')
    ctx.set('key', 'second')

    # Assert the overwritten value is returned.
    assert ctx.get('key') == 'second'


# ** test: delete_removes_key
def test_delete_removes_key(mock_session_state: dict) -> None:
    '''
    Verify delete removes a key from session state.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a context, set a value, then delete it.
    ctx = SessionCacheContext()
    ctx.set('key', 'value')
    ctx.delete('key')

    # Assert the key is removed.
    assert ctx.get('key') is None
    assert 'key' not in mock_session_state


# ** test: delete_nonexistent_key_is_safe
def test_delete_nonexistent_key_is_safe(mock_session_state: dict) -> None:
    '''
    Verify delete does not raise for a nonexistent key.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a context and delete a nonexistent key.
    ctx = SessionCacheContext()
    ctx.delete('nonexistent')


# ** test: clear_removes_all_keys
def test_clear_removes_all_keys(mock_session_state: dict) -> None:
    '''
    Verify clear removes all keys from session state.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a context and set multiple values.
    ctx = SessionCacheContext()
    ctx.set('a', 1)
    ctx.set('b', 2)

    # Clear all keys.
    ctx.clear()

    # Assert the state is empty.
    assert len(mock_session_state) == 0


# *** tests: namespaced

# ** test: namespace_key_isolation
def test_namespace_key_isolation(mock_session_state: dict) -> None:
    '''
    Verify two contexts with different namespaces store independently.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create two contexts with different namespaces.
    ctx_a = SessionCacheContext(namespace='ns_a')
    ctx_b = SessionCacheContext(namespace='ns_b')

    # Set the same key in both contexts.
    ctx_a.set('key', 'value_a')
    ctx_b.set('key', 'value_b')

    # Assert each context retrieves its own value.
    assert ctx_a.get('key') == 'value_a'
    assert ctx_b.get('key') == 'value_b'


# ** test: namespace_get_returns_none_for_other_namespace
def test_namespace_get_returns_none_for_other_namespace(mock_session_state: dict) -> None:
    '''
    Verify get returns None when querying a key from another namespace.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create two contexts with different namespaces.
    ctx_a = SessionCacheContext(namespace='ns_a')
    ctx_b = SessionCacheContext(namespace='ns_b')

    # Set a key in one namespace.
    ctx_a.set('key', 'value')

    # Assert the other namespace does not see it.
    assert ctx_b.get('key') is None


# ** test: namespace_delete
def test_namespace_delete(mock_session_state: dict) -> None:
    '''
    Verify delete only removes from own namespace.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create two contexts with different namespaces.
    ctx_a = SessionCacheContext(namespace='ns_a')
    ctx_b = SessionCacheContext(namespace='ns_b')

    # Set the same key in both namespaces.
    ctx_a.set('key', 'value_a')
    ctx_b.set('key', 'value_b')

    # Delete from one namespace.
    ctx_a.delete('key')

    # Assert the other namespace still has its value.
    assert ctx_a.get('key') is None
    assert ctx_b.get('key') == 'value_b'


# ** test: namespace_clear_only_clears_own_keys
def test_namespace_clear_only_clears_own_keys(mock_session_state: dict) -> None:
    '''
    Verify clear only removes keys from own namespace.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create two contexts with different namespaces.
    ctx_a = SessionCacheContext(namespace='ns_a')
    ctx_b = SessionCacheContext(namespace='ns_b')

    # Set keys in both namespaces.
    ctx_a.set('x', 1)
    ctx_a.set('y', 2)
    ctx_b.set('x', 3)

    # Clear only namespace A.
    ctx_a.clear()

    # Assert namespace A keys are removed.
    assert ctx_a.get('x') is None
    assert ctx_a.get('y') is None

    # Assert namespace B key is preserved.
    assert ctx_b.get('x') == 3


# ** test: set_complex_value
def test_set_complex_value(mock_session_state: dict) -> None:
    '''
    Verify storing and retrieving dicts and lists.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a context and set complex values.
    ctx = SessionCacheContext(namespace='ns')
    ctx.set('data', {'nested': [1, 2, 3]})

    # Assert the complex value is retrievable.
    assert ctx.get('data') == {'nested': [1, 2, 3]}


# ** test: empty_namespace_behaves_like_no_namespace
def test_empty_namespace_behaves_like_no_namespace(mock_session_state: dict) -> None:
    '''
    Verify empty string namespace behaves identically to no namespace.

    :param mock_session_state: The mocked session state dict.
    :type mock_session_state: dict
    '''

    # Create a context with empty namespace.
    ctx = SessionCacheContext(namespace='')

    # Set and get a value.
    ctx.set('key', 'value')

    # Assert the key is stored without prefix.
    assert 'key' in mock_session_state
    assert ctx.get('key') == 'value'
