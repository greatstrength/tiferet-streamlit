"""Tiferet Streamlit Session Context"""

# *** imports

# ** core
from typing import Any

# ** infra
import streamlit as st

# ** app
from tiferet.contexts.cache import CacheContext

# *** contexts

# ** context: session_cache_context
class SessionCacheContext(CacheContext):
    '''
    A cache context backed by Streamlit's session_state.

    Bridges st.session_state to Tiferet's CacheContext interface,
    enabling all Tiferet contexts (DI, Feature, Cache) to use
    Streamlit's persistence transparently.

    Supports namespaced keys to prevent collisions between views.
    '''

    # * attribute: namespace
    namespace: str

    # * init
    def __init__(self, namespace: str = ''):
        '''
        Initialize the session cache context.

        :param namespace: An optional namespace prefix for key isolation.
        :type namespace: str
        '''

        # Set the namespace for key isolation.
        self.namespace = namespace

    # * method: _key
    def _key(self, key: str) -> str:
        '''
        Build a namespaced key for session state.

        :param key: The base key.
        :type key: str
        :return: The namespaced key.
        :rtype: str
        '''

        # Prefix with namespace if set.
        return f'{self.namespace}.{key}' if self.namespace else key

    # * method: get
    def get(self, key: str) -> Any:
        '''
        Retrieve an item from session state.

        :param key: The key of the item to retrieve.
        :type key: str
        :return: The cached item or None if not found.
        :rtype: Any
        '''

        # Return the item from session state.
        return st.session_state.get(self._key(key))

    # * method: set
    def set(self, key: str, value: Any):
        '''
        Store an item in session state.

        :param key: The key to store the value under.
        :type key: str
        :param value: The value to store.
        :type value: Any
        '''

        # Store the value in session state.
        st.session_state[self._key(key)] = value

    # * method: delete
    def delete(self, key: str):
        '''
        Remove an item from session state.

        :param key: The key of the item to remove.
        :type key: str
        '''

        # Remove the item from session state.
        st.session_state.pop(self._key(key), None)

    # * method: clear
    def clear(self):
        '''
        Clear all items from this namespace in session state.
        If no namespace is set, clears all session state.
        '''

        # If no namespace, clear everything.
        if not self.namespace:
            st.session_state.clear()
            return

        # Clear only keys belonging to this namespace.
        prefix = f'{self.namespace}.'
        keys_to_remove = [
            k for k in st.session_state
            if k.startswith(prefix)
        ]
        for k in keys_to_remove:
            del st.session_state[k]
