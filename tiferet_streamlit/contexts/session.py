'''Tiferet Streamlit – Session Cache Context'''

# *** imports

# ** core
from typing import Any

# ** infra
import streamlit as st
from tiferet.contexts.cache import CacheContext

# *** contexts

# ** context: session_cache_context
class SessionCacheContext(CacheContext):
    '''
    A cache context backed by Streamlit's st.session_state.
    Supports namespaced keys to prevent collisions between views
    in multi-page applications.
    '''

    # * attribute: namespace
    namespace: str

    # * init
    def __init__(self, namespace: str = ''):
        '''
        Initialize the session cache context.

        :param namespace: Optional namespace prefix for key isolation.
        :type namespace: str
        '''

        # Set the namespace for key isolation.
        self.namespace = namespace

    # * method: _key
    def _key(self, key: str) -> str:
        '''
        Build a namespaced key.

        :param key: The base key.
        :type key: str
        :return: The namespaced key, or the base key if no namespace is set.
        :rtype: str
        '''

        # Return the namespaced key if a namespace is set.
        if self.namespace:
            return f'{self.namespace}.{key}'

        # Otherwise return the key as-is.
        return key

    # * method: get
    def get(self, key: str) -> Any:
        '''
        Retrieve a value from session state.

        :param key: The key to retrieve.
        :type key: str
        :return: The stored value or None if not found.
        :rtype: Any
        '''

        # Return the value from session state.
        return st.session_state.get(self._key(key))

    # * method: set
    def set(self, key: str, value: Any):
        '''
        Store a value in session state.

        :param key: The key to store the value under.
        :type key: str
        :param value: The value to store.
        :type value: Any
        '''

        # Set the value in session state.
        st.session_state[self._key(key)] = value

    # * method: delete
    def delete(self, key: str):
        '''
        Remove a key from session state. No error if absent.

        :param key: The key to remove.
        :type key: str
        '''

        # Pop the key from session state.
        st.session_state.pop(self._key(key), None)

    # * method: clear
    def clear(self):
        '''
        Clear session state. If namespaced, removes only keys
        starting with the namespace prefix. Otherwise clears all.
        '''

        # If no namespace, clear all session state.
        if not self.namespace:
            st.session_state.clear()
            return

        # Remove only keys belonging to this namespace.
        prefix = f'{self.namespace}.'
        keys_to_remove = [
            k for k in list(st.session_state.keys())
            if k.startswith(prefix)
        ]
        for k in keys_to_remove:
            st.session_state.pop(k, None)
