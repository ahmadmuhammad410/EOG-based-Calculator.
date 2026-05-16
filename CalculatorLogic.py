import streamlit as st

def btn_click(val):
    """Appends a number to the current display."""
    if st.session_state.get('new_input_starts_new_equation', False):
        st.session_state.display = str(val)
        st.session_state.new_input_starts_new_equation = False
    elif st.session_state.display == "0" or st.session_state.display == "Error":
        st.session_state.display = str(val)
    else:
        st.session_state.display += str(val)

def op_click(op):
    """Sets the operator and stores the previous value. Performs cumulative calculation if needed."""
    st.session_state.new_input_starts_new_equation = False
    if st.session_state.expression != "":
        # If there's already an expression, evaluate it first (cumulative behavior)
        try:
            full_expr = st.session_state.expression + st.session_state.display
            # Sanitize for eval
            expr_to_eval = full_expr.replace('×', '*').replace('÷', '/')
            result = eval(expr_to_eval)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            st.session_state.expression = str(result) + " " + op + " "
        except Exception:
            st.session_state.expression = st.session_state.display + " " + op + " "
    else:
        # First operator in the sequence
        st.session_state.expression = st.session_state.display + " " + op + " "
    
    st.session_state.display = "0"

def clear():
    """Resets the calculator state."""
    st.session_state.display = "0"
    st.session_state.expression = ""
    st.session_state.new_input_starts_new_equation = False

def calculate():
    """Evaluates the mathematical expression."""
    try:
        full_expr = st.session_state.expression + st.session_state.display
        # Replace display symbols with math operators
        expr_to_eval = full_expr.replace('×', '*').replace('÷', '/')
        result = eval(expr_to_eval)
        # Format result to avoid long decimals if needed
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        st.session_state.display = str(result)
        st.session_state.expression = ""
        st.session_state.new_input_starts_new_equation = True
    except Exception:
        st.session_state.display = "Error"
        st.session_state.new_input_starts_new_equation = True
