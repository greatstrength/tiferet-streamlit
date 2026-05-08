"""Calculator Views — Streamlit UI powered by Tiferet"""

# *** imports

# ** infra
import streamlit as st

# ** app
from tiferet_streamlit import ViewContext, ViewComponent
from tiferet import TiferetError

# *** components

# ** component: number_input
class NumberInput(ViewComponent):
    '''
    A reusable numeric input component.

    The widget owns its state via the Streamlit key. Use
    get_widget_value() to read the current value from session_state.
    '''

    def render(self, label: str, state_key: str, default: float = 0.0):
        widget_key = f'{self.ctx.key}.{state_key}'
        st.number_input(
            label,
            value=default,
            step=1.0,
            key=widget_key,
        )

    @staticmethod
    def get_widget_value(ctx, state_key: str):
        '''Read the current widget value from session state.'''
        widget_key = f'{ctx.key}.{state_key}'
        return st.session_state.get(widget_key, 0.0)


# ** component: result_display
class ResultDisplay(ViewComponent):
    '''
    A reusable component that shows the last computation result.
    '''

    def render(self, **props):
        result = self.ctx.session.get('result')
        error = self.ctx.session.get('error')

        if error:
            st.error(error)
        elif result is not None:
            st.success(f'Result: {result}')


# *** views

# ** view: calculator_view
class CalculatorView(ViewContext):
    '''
    The main calculator page. Dispatches Tiferet features for arithmetic.
    '''

    def init_state(self):
        self.session.set('result', None)
        self.session.set('error', None)

    def render(self):
        st.header('Calculator')

        # Number inputs.
        NumberInput(self)(label='A', state_key='a')
        NumberInput(self)(label='B', state_key='b')

        # Operation buttons in columns.
        col1, col2, col3, col4 = st.columns(4)

        operations = [
            (col1, 'Add', 'calc.add'),
            (col2, 'Subtract', 'calc.subtract'),
            (col3, 'Multiply', 'calc.multiply'),
            (col4, 'Divide', 'calc.divide'),
        ]

        for col, label, feature_id in operations:
            with col:
                if st.button(label, key=f'{self.key}.{label.lower()}', use_container_width=True):
                    self.run_operation(feature_id)

        # Advanced operations.
        col_exp, col_sqrt = st.columns(2)

        with col_exp:
            if st.button('Power (A^B)', key=f'{self.key}.exp', use_container_width=True):
                self.run_operation('calc.exp')

        with col_sqrt:
            if st.button('Square Root (A)', key=f'{self.key}.sqrt', use_container_width=True):
                self.run_operation('calc.sqrt', a=NumberInput.get_widget_value(self, 'a'))

        # Display result.
        st.divider()
        ResultDisplay(self)()

    # * method: run_operation
    def run_operation(self, feature_id: str, **override_data):
        '''
        Execute an operation, storing the result or error in session.
        '''

        data = {
            'a': NumberInput.get_widget_value(self, 'a'),
            'b': NumberInput.get_widget_value(self, 'b'),
            **override_data,
        }

        try:
            result = self.dispatch(feature_id, **data)
            self.session.set('result', result)
            self.session.set('error', None)
        except TiferetError as e:
            self.session.set('result', None)
            self.session.set('error', str(e.message) if hasattr(e, 'message') else str(e))
        except Exception as e:
            self.session.set('result', None)
            self.session.set('error', str(e))


# ** view: about_view
class AboutView(ViewContext):
    '''
    An about page demonstrating a simple static view.
    '''

    def render(self):
        st.header('About')
        st.write(
            'This is a sample calculator application built with '
            '**tiferet-streamlit**, demonstrating how Tiferet\'s '
            'domain-driven design integrates with Streamlit\'s UI framework.'
        )
        st.subheader('Architecture')
        st.write(
            '- **Domain Events** in `app/events/calc.py` handle arithmetic logic\n'
            '- **Features** in `config.yml` wire events into callable workflows\n'
            '- **ViewContexts** in `views.py` serve as the code-behind for each page\n'
            '- **ViewComponents** provide reusable, composable UI pieces'
        )
