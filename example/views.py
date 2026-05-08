'''Calculator Example – Views'''

# *** imports

# ** infra
import streamlit as st
from tiferet import TiferetError

# ** app
from tiferet_streamlit import ViewContext, ViewComponent

# *** components

# ** component: number_input
class NumberInput(ViewComponent):
    '''
    A reusable number input component.
    '''

    # * method: render
    def render(self, label: str = 'Number', default: float = 0.0, key_suffix: str = 'num'):
        '''
        Render a number input widget.

        :param label: The input label.
        :type label: str
        :param default: The default value.
        :type default: float
        :param key_suffix: Suffix for the widget key.
        :type key_suffix: str
        '''

        # Render the number input with a scoped widget key.
        widget_key = f'{self.ctx.key}_{key_suffix}'
        st.number_input(label, value=default, key=widget_key, step=1.0)

    # * method: get_widget_value (static)
    @staticmethod
    def get_widget_value(view_key: str, key_suffix: str) -> float:
        '''
        Read a number input value from session state.

        :param view_key: The parent view key.
        :type view_key: str
        :param key_suffix: The widget key suffix.
        :type key_suffix: str
        :return: The current widget value.
        :rtype: float
        '''

        # Return the value from session state.
        return st.session_state.get(f'{view_key}_{key_suffix}', 0.0)


# ** component: result_display
class ResultDisplay(ViewComponent):
    '''
    A component to display calculation results or errors.
    '''

    # * method: render
    def render(self):
        '''
        Display the result or error from the parent session.
        '''

        # Check for error first.
        error = self.ctx.session.get('error')
        if error:
            st.error(f'Error: {error}')
            return

        # Display result if available.
        result = self.ctx.session.get('result')
        if result is not None:
            st.success(f'Result: {result}')


# *** views

# ** view: calculator_view
class CalculatorView(ViewContext):
    '''
    Main calculator page with arithmetic operations.
    '''

    # * method: init_state
    def init_state(self):
        '''Initialize calculator state.'''

        # Set default values.
        self.session.set('result', None)
        self.session.set('error', None)

    # * method: run_operation
    def run_operation(self, feature_id: str, **data):
        '''
        Dispatch a calculator feature and store result or error.

        :param feature_id: The feature to dispatch.
        :type feature_id: str
        :param data: The feature data.
        :type data: dict
        '''

        # Clear previous results.
        self.session.set('result', None)
        self.session.set('error', None)

        # Dispatch the feature.
        try:
            result = self.dispatch(feature_id, **data)
            self.session.set('result', result)
        except TiferetError as e:
            self.session.set('error', e.message)

    # * method: render
    def render(self):
        '''Render the calculator UI.'''

        # Page title.
        st.title('🧮 Calculator')

        # Number inputs.
        num_input = NumberInput(ctx=self)
        num_input(label='First Number (a)', default=0.0, key_suffix='a')
        num_input(label='Second Number (b)', default=0.0, key_suffix='b')

        # Read current values.
        a = NumberInput.get_widget_value(self.key, 'a')
        b = NumberInput.get_widget_value(self.key, 'b')

        # Operation buttons in columns.
        st.subheader('Operations')
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button('➕ Add'):
                self.run_operation('calc.add', a=a, b=b)
            if st.button('➖ Subtract'):
                self.run_operation('calc.subtract', a=a, b=b)

        with col2:
            if st.button('✖️ Multiply'):
                self.run_operation('calc.multiply', a=a, b=b)
            if st.button('➗ Divide'):
                self.run_operation('calc.divide', a=a, b=b)

        with col3:
            if st.button('⬆️ Power'):
                self.run_operation('calc.exp', a=a, b=b)
            if st.button('√ Square Root'):
                self.run_operation('calc.sqrt', a=a)

        # Result display.
        st.divider()
        result_display = ResultDisplay(ctx=self)
        result_display()


# ** view: about_view
class AboutView(ViewContext):
    '''
    Static about page describing the app architecture.
    '''

    # * method: render
    def render(self):
        '''Render the about page.'''

        st.title('ℹ️ About')
        st.markdown('''
This calculator application demonstrates the **tiferet-streamlit** package:

- **Domain Events** — Arithmetic operations (`AddNumber`, `SubtractNumber`, etc.) are Tiferet domain events with input validation.
- **ViewContext** — `CalculatorView` manages calculator state and dispatches features.
- **ViewComponent** — `NumberInput` and `ResultDisplay` are reusable, prop-driven components.
- **Multi-Page Navigation** — `PageContext` manages routing between Calculator and About pages.
- **Feature Dispatch** — Operations are executed via `self.dispatch()`, which delegates to Tiferet's feature engine.
- **Error Handling** — Division by zero and invalid inputs produce structured `TiferetError` messages.

Built with [Tiferet](https://github.com/greatstrength/tiferet) and [Streamlit](https://streamlit.io).
        ''')
