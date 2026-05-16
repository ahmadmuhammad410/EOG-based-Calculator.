import os
import pandas as pd
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
from statsmodels.tsa.ar_model import AutoReg
import pywt
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import streamlit as st

# --- Signal Processing Constants ---
FS = 176
LOWCUT = 0.5
HIGHCUT = 20.0
FILTER_ORDER = 4

def butter_bandpass_filter(data, lowcut=LOWCUT, highcut=HIGHCUT, fs=FS, order=FILTER_ORDER):
    nyq = 0.5 * fs
    low, high = lowcut / nyq, highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)

def preprocess(signal_data):
    sig = np.array(signal_data, dtype=float)

    bpf_full = butter_bandpass_filter(sig, fs=FS)
    if len(sig) > 50:
        bpf_down = signal.resample(bpf_full, 50)
    else:
        bpf_down = bpf_full
    return bpf_full, bpf_down

def feature_extraction(signal_data_bpf):
    # 1. DWT (A2 Approximation Coefficients)
    coeffs = pywt.wavedec(signal_data_bpf, 'db4', level=2)
    signal_data_a2 = coeffs[0]

    # 2. AR Coefficients
    try:
        ar_mod = AutoReg(signal_data_bpf, lags=3).fit()
        ar_coeffs = ar_mod.params.tolist()
    except:
        ar_coeffs = [0.0] * 4

    
    return ar_coeffs, signal_data_a2

# --- Machine Learning Models ---
class_to_label = {'yukari': 0, 'asagi': 1, 'sag': 2, 'sol': 3, 'krip': 4, 'kirp': 4}

def load_merged_data(filepath):
    if not os.path.exists(filepath):
        return None, None
    df = pd.read_excel(filepath)
    X, y = [], []
    columns = list(df.columns)
    for i in range(0, len(columns), 2):
        h_col = columns[i]
        v_col = columns[i+1]
        h_data = df[h_col].dropna().values
        v_data = df[v_col].dropna().values
        feature_vector = np.concatenate([h_data, v_data])
        X.append(feature_vector)
        label_str = "".join([c for c in h_col if c.isalpha()]).lower()
        if label_str.endswith('h'):
            label_str = label_str[:-1]
        y.append(class_to_label.get(label_str, -1))
    return np.array(X), np.array(y)

def evaluate_models(progress_callback=None):
    categories = ['Raw', 'DWT', 'AR']
    trials = ['trail1', 'trail2', 'trail3', 'trail4']
    results = []
    
    for idx, category in enumerate(categories):
        svm_accs = []
        rf_accs = []
        
        folder_name = category
        if category == 'Raw':
            folder_name = 'Preprocessing'
            
        for trial in trials:
            train_file = f"Merged/{folder_name}/{trial}/{trial}_train_{category}.xlsx"
            test_file = f"Merged/{folder_name}/{trial}/{trial}_test_{category}.xlsx"
            
            X_train, y_train = load_merged_data(train_file)
            X_test, y_test = load_merged_data(test_file)
            
            if X_train is not None and X_test is not None:
                train_mask = y_train != -1
                test_mask = y_test != -1
                X_train, y_train = X_train[train_mask], y_train[train_mask]
                X_test, y_test = X_test[test_mask], y_test[test_mask]
                
                if len(X_train) == 0 or len(X_test) == 0:
                    continue
                    
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # SVM model
                svm_model = OneVsRestClassifier(SVC())
                svm_model.fit(X_train_scaled, y_train)
                svm_preds = svm_model.predict(X_test_scaled)
                svm_accs.append(accuracy_score(y_test, svm_preds))
                
                # Random Forest model
                rf_model = RandomForestClassifier(random_state=42, n_estimators=100)
                rf_model.fit(X_train_scaled, y_train)
                rf_preds = rf_model.predict(X_test_scaled)
                rf_accs.append(accuracy_score(y_test, rf_preds))
                
                if category == 'AR' and trial == 'trail1':
                    st.session_state.svm_model = svm_model
                    st.session_state.scaler = scaler
                    st.session_state.is_merged_model = True
                    st.session_state.merged_category = 'AR'
        
        if svm_accs and rf_accs:
            avg_svm_acc = np.mean(svm_accs) * 100
            avg_rf_acc = np.mean(rf_accs) * 100
            results.append({
                "Feature Category": category, 
                "SVM Accuracy": f"{avg_svm_acc:.2f}%",
                "Random Forest Accuracy": f"{avg_rf_acc:.2f}%"
            })
        else:
            results.append({
                "Feature Category": category, 
                "SVM Accuracy": "N/A",
                "Random Forest Accuracy": "N/A"
            })
        
        if progress_callback:
            progress_callback((idx + 1) / len(categories))
            
    return pd.DataFrame(results)

def classify_eog_movement(signal_data, model, scaler):
    if model is None or scaler is None:
        return "MODEL NOT TRAINED", None
    
    bpf_full, bpf_down = preprocess(signal_data)
    AR_coefficients, a2_signal = feature_extraction(bpf_down)
    features_scaled = scaler.transform(np.array(AR_coefficients).reshape(1, -1))
    
    prediction = model.predict(features_scaled)[0]
    
    mapping = {0: "UP", 1: "DOWN", 2: "RIGHT", 3: "LEFT", 4: "BLINK"}
    movement = mapping.get(prediction, "UNKNOWN")
    
    return movement, {"bpf_full": bpf_full, "bpf_down": bpf_down, "dwt_a2": a2_signal}

def classify_merged_movement(h_signal, v_signal, category, model, scaler):
    if model is None or scaler is None:
        return "MODEL NOT TRAINED", None
        
    h_bpf_full, h_bpf = preprocess(h_signal)
    v_bpf_full, v_bpf = preprocess(v_signal)
    
    from extract_dwt import extract_a2_column
    from extract_ar import extract_ar_fitted
    
    h_dwt = extract_a2_column(h_bpf)
    v_dwt = extract_a2_column(v_bpf)
    
    h_ar = extract_ar_fitted(h_bpf, lags=3)
    v_ar = extract_ar_fitted(v_bpf, lags=3)
    
    if category == 'AR':
        h_feats = h_ar
        v_feats = v_ar
    elif category == 'DWT':
        h_feats = h_dwt
        v_feats = v_dwt
    else: # Raw
        h_feats = h_bpf
        v_feats = v_bpf
        
    feature_vector = np.concatenate([h_feats, v_feats])
    scaled_feats = scaler.transform([feature_vector])
    
    pred_idx = model.predict(scaled_feats)[0]
    
    mapping = {0: "UP", 1: "DOWN", 2: "RIGHT", 3: "LEFT", 4: "BLINK"}
    movement = mapping.get(pred_idx, "UNKNOWN")
    
    return movement, {
        "h_bpf_full": h_bpf_full, "h_bpf_down": h_bpf, "h_dwt": h_dwt, "h_ar": h_ar,
        "v_bpf_full": v_bpf_full, "v_bpf_down": v_bpf, "v_dwt": v_dwt, "v_ar": v_ar
    }
