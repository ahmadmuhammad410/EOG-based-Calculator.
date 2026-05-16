import streamlit as st
import numpy as np
import pandas as pd
import CalculatorLogic as logic
import Models as models

# --- Page Config & Styling ---
st.set_page_config(page_title="EOG Compass Calculator", layout="wide")

# Custom CSS for the Sketch-accurate Layout
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: #0f172a;
        color: #f8fafc;
    }

    /* Calculator Buttons */
    .stButton > button {
        width: 80px !important;
        height: 60px !important;
        background: #1e293b !important;
        border: 2px solid #334155 !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
        font-weight: 700 !important;
        font-size: 1.4rem !important;
        transition: all 0.2s !important;
    }

    .stButton > button:hover {
        background: #334155 !important;
        border-color: #38bdf8 !important;
        transform: translateY(-2px);
    }

    /* Center Node Styling */
    .node-center {
        width: 80px;
        height: 60px;
        background: #1e293b;
        color: white;
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        border: 2px solid #334155;
        transition: all 0.3s;
    }

    @keyframes pulse-glow {
        0% { box-shadow: 0 0 10px rgba(245, 158, 11, 0.4); transform: scale(1.05); }
        50% { box-shadow: 0 0 30px rgba(245, 158, 11, 0.8); transform: scale(1.15); }
        100% { box-shadow: 0 0 10px rgba(245, 158, 11, 0.4); transform: scale(1.05); }
    }

    .node-active {
        background: #f59e0b !important;
        border: 2px solid #fbbf24 !important;
        animation: pulse-glow 2s infinite ease-in-out;
        z-index: 10;
    }

    @keyframes selection-pulse {
        0% { filter: brightness(1); transform: scale(1); }
        50% { filter: brightness(1.3); transform: scale(1.08); }
        100% { filter: brightness(1); transform: scale(1); }
    }

    button[kind="primary"] {
        animation: selection-pulse 1.5s infinite ease-in-out !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5) !important;
    }

    /* Connection Lines (Visual Simulation) */
    .connection-h { height: 2px; background: #334155; width: 100%; margin: auto; }
    .connection-v { width: 2px; background: #334155; height: 100%; margin: auto; }

    /* Display Area */
    .display-box {
        background: #1e293b;
        border-radius: 12px;
        padding: 20px;
        text-align: right;
        border: 2px solid #334155;
        margin-bottom: 30px;
        width: 100%;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
    }
    .curr-val { font-size: 3rem; font-weight: 800; color: #38bdf8; }
    .prev-val { font-size: 1rem; color: #94a3b8; }
    </style>
""", unsafe_allow_html=True)

# --- Session State ---
if 'display' not in st.session_state:
    st.session_state.display = "0"
if 'expression' not in st.session_state:
    st.session_state.expression = ""
if 'svm_model' not in st.session_state:
    st.session_state.svm_model = None
if 'scaler' not in st.session_state:
    st.session_state.scaler = None
if 'current_state' not in st.session_state:
    st.session_state.current_state = "MAIN_CENTER"

# --- Interaction Logic ---
def execute_movement(move):
    """Handles the 3-step 'Point and Blink' logic."""
    
    # 1. BLINK: The ONLY way to choose/click the pointed button
    if move == "BLINK":
        if st.session_state.get('pointed_at_key'):
            key = st.session_state.pointed_at_key
            # Extract the actual value from the key (e.g., 'g1_0' -> '0')
            # Group 1/2/3 use btn_click, Group 4 uses op_click
            val = key.split('_')[1]
            
            if 'g3_e' in key: logic.calculate()
            elif 'g3_c' in key: logic.clear()
            elif 'g4' in key:
                ops = {"mi": "-", "sl": "/", "pl": "+", "x": "×"}
                logic.op_click(ops.get(val, val))
            else:
                # Convert logic.btn_click value mappings if needed
                logic.btn_click(val)
                
            st.session_state.last_clicked_key = key # For historical highlight
            st.toast(f"Selected: {key}")
        
        # Always return to center on blink
        st.session_state.current_state = "MAIN_CENTER"
        st.session_state.pointed_at_key = None
        return

    if move == "CENTER":
        return

    # STEP 1: At Main Center -> Move to Group Center & Point at primary button
    if st.session_state.current_state == "MAIN_CENTER":
        if move == "UP": 
            st.session_state.current_state = "GROUP_1_CENTER"
            st.session_state.pointed_at_key = "g1_0" # Point at 0
        elif move == "RIGHT": 
            st.session_state.current_state = "GROUP_2_CENTER"
            st.session_state.pointed_at_key = "g2_4" # Point at 4
        elif move == "DOWN": 
            st.session_state.current_state = "GROUP_3_CENTER"
            st.session_state.pointed_at_key = "g3_8" # Point at 8
        elif move == "LEFT": 
            st.session_state.current_state = "GROUP_4_CENTER"
            st.session_state.pointed_at_key = "g4_pl" # Point at +
        st.toast(f"Focused {st.session_state.current_state}")
        
    # STEP 2: At Group Center -> Move the 'Point' Focus
    else:
        state = st.session_state.current_state
        if state == "GROUP_1_CENTER":
            if move == "UP": st.session_state.pointed_at_key = "g1_2"
            elif move == "DOWN": st.session_state.pointed_at_key = "g1_0"
            elif move == "RIGHT": st.session_state.pointed_at_key = "g1_1"
            elif move == "LEFT": st.session_state.pointed_at_key = "g1_3"
            
        elif state == "GROUP_2_CENTER":
            if move == "UP": st.session_state.pointed_at_key = "g2_7"
            elif move == "DOWN": st.session_state.pointed_at_key = "g2_5"
            elif move == "RIGHT": st.session_state.pointed_at_key = "g2_6"
            elif move == "LEFT": st.session_state.pointed_at_key = "g2_4"
            
        elif state == "GROUP_3_CENTER":
            if move == "UP": st.session_state.pointed_at_key = "g3_8"
            elif move == "DOWN": st.session_state.pointed_at_key = "g3_e"
            elif move == "RIGHT": st.session_state.pointed_at_key = "g3_c"
            elif move == "LEFT": st.session_state.pointed_at_key = "g3_9"
            
        elif state == "GROUP_4_CENTER":
            if move == "UP": st.session_state.pointed_at_key = "g4_mi"
            elif move == "DOWN": st.session_state.pointed_at_key = "g4_x"
            elif move == "LEFT": st.session_state.pointed_at_key = "g4_sl"
            elif move == "RIGHT": st.session_state.pointed_at_key = "g4_pl"
        
        st.toast(f"Pointing at: {st.session_state.pointed_at_key}")


# --- Sidebar for Signals ---
st.sidebar.title("📡 EOG Interface")

# 3. Merged Feature Evaluation
with st.sidebar.expander("🚀 Evaluate Merged Features (1vAll)"):
    st.write("Train and evaluate SVM using One-Vs-Rest across all 4 trials for each feature category.")
    
    if st.button("Run Merged Evaluation"):
        progress_bar = st.progress(0)
        df_results = models.evaluate_models(progress_callback=progress_bar.progress)
        st.success("Evaluation Complete!")
        st.table(df_results)

st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ Live Classification")
st.sidebar.code("Yukari=UP, Asagi=DOWN, Sag=RIGHT, Sol=LEFT, Kirp=BLINK")

is_merged = st.session_state.get('is_merged_model', False)

if not is_merged:
    st.sidebar.write("Using Single-File Hybrid Model")
    uploaded_file = st.sidebar.file_uploader("Upload EOG Data for Prediction", type=["csv", "txt"])
    
    if uploaded_file:
        try:
            sig = pd.read_csv(uploaded_file).iloc[:, 0].values if uploaded_file.name.endswith('.csv') else np.loadtxt(uploaded_file)
            movement, processed = models.classify_eog_movement(np.array(sig).flatten(), st.session_state.svm_model, st.session_state.scaler)
            
            st.sidebar.markdown(f"### Detected Movement: <span style='color:#f59e0b'>{movement}</span>", unsafe_allow_html=True)
            if st.sidebar.button("Execute Predicted Move"):
                execute_movement(movement)
                st.rerun()
                
            if processed:
                with st.expander("📈 View Signal Stages", expanded=True):
                    st.line_chart(processed['bpf'], height=150)
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
else:
    cat = st.session_state.get('merged_category', 'AR')
    st.sidebar.write(f"Using **Merged Model** ({cat} features)")
    st.sidebar.write("Requires both Horizontal and Vertical signals.")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        h_file = st.file_uploader("Horizontal File", type=["csv", "txt"])
    with col2:
        v_file = st.file_uploader("Vertical File", type=["csv", "txt"])
        
    if h_file and v_file:
        try:
            h_sig = pd.read_csv(h_file).iloc[:, 0].values if h_file.name.endswith('.csv') else np.loadtxt(h_file)
            v_sig = pd.read_csv(v_file).iloc[:, 0].values if v_file.name.endswith('.csv') else np.loadtxt(v_file)
            
            # Create a unique hash for these two files using Streamlit's file_id
            # This ensures that re-uploading the exact same file is treated as a NEW action!
            file_hash = f"{getattr(h_file, 'file_id', 'h')}_{getattr(v_file, 'file_id', 'v')}"
            
            # Predict using the new dual-channel function
            model = st.session_state.svm_model
            scaler = st.session_state.scaler
            
            movement, processed = models.classify_merged_movement(
                np.array(h_sig).flatten(), 
                np.array(v_sig).flatten(), 
                cat, 
                model, 
                scaler
            )
            
            st.sidebar.markdown(f"### Detected Movement: <span style='color:#f59e0b'>{movement}</span>", unsafe_allow_html=True)
            
            if 'last_processed_hash' not in st.session_state:
                st.session_state.last_processed_hash = None
                
            # Execute automatically exactly once per unique file combination
            if file_hash != st.session_state.last_processed_hash:
                st.session_state.last_processed_hash = file_hash
                execute_movement(movement)
                
            if processed:
                with st.expander("📈 View Signal Stages", expanded=True):
                    # Pad arrays to the same length so Streamlit can plot them together
                    def pad_dict(h_arr, v_arr):
                        max_len = max(len(h_arr), len(v_arr))
                        h_pad = np.pad(h_arr, (0, max_len - len(h_arr)))
                        v_pad = np.pad(v_arr, (0, max_len - len(v_arr)))
                        return pd.DataFrame({'Horizontal': h_pad, 'Vertical': v_pad})
                        
                    st.write("**1. Bandpass Filter (Full)**")
                    st.line_chart(pad_dict(processed['h_bpf_full'], processed['v_bpf_full']), height=150)
                    
                    st.write("**2. Downsampled (50 samples)**")
                    st.line_chart(pad_dict(processed['h_bpf_down'], processed['v_bpf_down']), height=150)
                    
                    st.write("**3. DWT (A2 Coefficients)**")
                    st.line_chart(pad_dict(processed['h_dwt'], processed['v_dwt']), height=150)
                    
                    st.write("**4. AR Coefficients**")
                    st.bar_chart(pad_dict(processed['h_ar'], processed['v_ar']), height=150)
                
        except Exception as e:
            st.sidebar.error(f"Error during Merged Prediction: {e}")
    else:
        # If files are removed, clear the cache so they can be reused easily
        st.session_state.last_processed_hash = None

# --- UI Components ---

def draw_group_top():
    is_active = st.session_state.current_state == "GROUP_1_CENTER"
    active_class = "node-active" if is_active else ""
    last_k = st.session_state.get('last_clicked_key')
    pointed_k = st.session_state.get('pointed_at_key')
    
    # Helper to check highlight
    def is_h(k): return "primary" if (k == last_k or k == pointed_k) else "secondary"
    
    # Row 1: [ ] [2] [ ]
    c1, c2, c3 = st.columns(3)
    with c2: st.button("2", key="g1_2", on_click=logic.btn_click, args=("2",), type=is_h("g1_2"))
    
    # Row 2: [3] [0] [1]
    c1, c2, c3 = st.columns(3)
    with c1: st.button("3", key="g1_3", on_click=logic.btn_click, args=("3",), type=is_h("g1_3"))
    with c2: 
        if is_active:
            st.markdown(f'<div class="node-center {active_class}" style="position:absolute; width:100%; height:100%; z-index:-1; opacity:0.5;"></div>', unsafe_allow_html=True)
        st.button("0", key="g1_0", on_click=logic.btn_click, args=("0",), type=is_h("g1_0"))
    with c3: st.button("1", key="g1_1", on_click=logic.btn_click, args=("1",), type=is_h("g1_1"))

def draw_group_bottom():
    is_active = st.session_state.current_state == "GROUP_3_CENTER"
    active_class = "node-active" if is_active else ""
    last_k = st.session_state.get('last_clicked_key')
    pointed_k = st.session_state.get('pointed_at_key')
    def is_h(k): return "primary" if (k == last_k or k == pointed_k) else "secondary"
    
    # Row 1: [9] [8] [C]
    c1, c2, c3 = st.columns(3)
    with c1: st.button("9", key="g3_9", on_click=logic.btn_click, args=("9",), type=is_h("g3_9"))
    with c2: st.button("8", key="g3_8", on_click=logic.btn_click, args=("8",), type=is_h("g3_8"))
    with c3: st.button("C", key="g3_c", on_click=logic.clear, type=is_h("g3_c"))
    
    # Row 2: [ ] [=] [ ]
    c1, c2, c3 = st.columns(3)
    with c2: 
        if is_active:
             st.markdown(f'<div class="node-center {active_class}" style="position:absolute; width:100%; height:100%; z-index:-1; opacity:0.5;"></div>', unsafe_allow_html=True)
        st.button("=", key="g3_e", on_click=logic.calculate, type=is_h("g3_e"))

def draw_group_left():
    is_active = st.session_state.current_state == "GROUP_4_CENTER"
    active_class = "node-active" if is_active else ""
    last_k = st.session_state.get('last_clicked_key')
    pointed_k = st.session_state.get('pointed_at_key')
    def is_h(k): return "primary" if (k == last_k or k == pointed_k) else "secondary"
    
    # Using 3 columns to bring '/' closer to '+'
    # Row 1: [ ] [-] [ ]
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2: st.button("-", key="g4_mi", on_click=logic.op_click, args=("-",), type=is_h("g4_mi"))
    
    # Row 2: [/] [+] [ ]
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: st.button("/", key="g4_sl", on_click=logic.op_click, args=("/",), type=is_h("g4_sl"))
    with c2: 
        if is_active:
             st.markdown(f'<div class="node-center {active_class}" style="position:absolute; width:100%; height:100%; z-index:-1; opacity:0.5;"></div>', unsafe_allow_html=True)
        st.button("+", key="g4_pl", on_click=logic.op_click, args=("+",), type=is_h("g4_pl"))
    
    # Row 3: [ ] [*] [ ]
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2: st.button("×", key="g4_x", on_click=logic.op_click, args=("×",), type=is_h("g4_x"))

def draw_group_right():
    is_active = st.session_state.current_state == "GROUP_2_CENTER"
    active_class = "node-active" if is_active else ""
    last_k = st.session_state.get('last_clicked_key')
    pointed_k = st.session_state.get('pointed_at_key')
    def is_h(k): return "primary" if (k == last_k or k == pointed_k) else "secondary"
    
    # Using 3 columns to bring '6' closer to '4'
    # Row 1: [7] [ ] [ ]
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: st.button("7", key="g2_7", on_click=logic.btn_click, args=("7",), type=is_h("g2_7"))
    
    # Row 2: [4] [6] [ ]
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: 
        if is_active:
             st.markdown(f'<div class="node-center {active_class}" style="position:absolute; width:100%; height:100%; z-index:-1; opacity:0.5;"></div>', unsafe_allow_html=True)
        st.button("4", key="g2_4", on_click=logic.btn_click, args=("4",), type=is_h("g2_4"))
    with c2: st.button("6", key="g2_6", on_click=logic.btn_click, args=("6",), type=is_h("g2_6"))
    
    # Row 3: [5] [ ] [ ]
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: st.button("5", key="g2_5", on_click=logic.btn_click, args=("5",), type=is_h("g2_5"))

# --- Layout ---

# Display at top
st.markdown(f"""
    <div class="display-box">
        <div class="prev-val">{st.session_state.expression}</div>
        <div class="curr-val">{st.session_state.display}</div>
    </div>
""", unsafe_allow_html=True)

# ROW 1: TOP GROUP
r1_c1, r1_c2, r1_c3 = st.columns([1, 1, 1])
with r1_c2:
    draw_group_top()

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ROW 2: LEFT GROUP | MAIN CENTER | RIGHT GROUP
r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])

with r2_c1: # --- GROUP 4 (LEFT) ---
    draw_group_left()

with r2_c2: # --- MAIN CENTER ---
    is_main_active = "node-active" if st.session_state.current_state == "MAIN_CENTER" else ""
    st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="node-center {is_main_active}" style="margin:auto; width:120px; height:80px;">Main Center</div>', unsafe_allow_html=True)

with r2_c3: # --- GROUP 2 (RIGHT) ---
    draw_group_right()

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ROW 3: BOTTOM GROUP
r3_c1, r3_c2, r3_c3 = st.columns([1, 1, 1])
with r3_c2:
    draw_group_bottom()
