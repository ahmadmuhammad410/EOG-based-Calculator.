import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.tsa.ar_model import AutoReg
from sklearn.svm import SVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import warnings

warnings.filterwarnings('ignore', 'No frequency information was')

def extract_ar_fitted(data, lags):
    sig = np.array(data, dtype=float)
    sig = sig[~np.isnan(sig)]
    
    if len(sig) <= lags:
        return [0.0] * (50 - lags)

    try:
        ar_mod = AutoReg(sig, lags=lags).fit()
        return ar_mod.params.tolist()
    except Exception as e:
        return [0.0] * (len(sig) - lags)

class_to_label = {'yukari': 0, 'asagi': 1, 'sag': 2, 'sol': 3, 'krip': 4, 'kirp': 4}

def load_and_extract_ar(trial, split, lags):
    input_base = Path("B_preprocessed_ExcelSheets")
    
    h_file = input_base / trial / f"preprocessed_{trial}_horizontal_{split}.xlsx"
    v_file = input_base / trial / f"preprocessed_{trial}_vertical_{split}.xlsx"
    
    if not h_file.exists() or not v_file.exists():
        return None, None
        
    df_h = pd.read_excel(h_file)
    df_v = pd.read_excel(v_file)
    
    X, y = [], []
    
    for i in range(len(df_h.columns)):
        col_h = df_h.columns[i]
        
        h_data = df_h.iloc[:, i].dropna().values
        v_data = df_v.iloc[:, i].dropna().values
        
        h_ar = extract_ar_fitted(h_data, lags=lags)
        v_ar = extract_ar_fitted(v_data, lags=lags)
        
        feature_vector = np.concatenate([h_ar, v_ar])
        X.append(feature_vector)
        
        label_str = "".join([c for c in col_h if c.isalpha()]).lower()
        if label_str.endswith('h'):
            label_str = label_str[:-1]
            
        y.append(class_to_label.get(label_str, -1))
        
    return np.array(X), np.array(y)

def evaluate():
    trials = ['trail1', 'trail2', 'trail3', 'trail4']
    print(f"{'nlags':<10} | {'Avg Accuracy':<15}")
    print("-" * 30)
    
    results = {}
    
    for lags in range(1, 21):
        trial_accs = []
        for trial in trials:
            X_train, y_train = load_and_extract_ar(trial, 'train', lags)
            X_test, y_test = load_and_extract_ar(trial, 'test', lags)
            
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
                
                model = OneVsRestClassifier(SVC(random_state=42))
                model.fit(X_train_scaled, y_train)
                
                preds = model.predict(X_test_scaled)
                acc = accuracy_score(y_test, preds)
                trial_accs.append(acc)
                
        if trial_accs:
            avg_acc = np.mean(trial_accs) * 100
            print(f"{lags:<10} | {avg_acc:.2f}%")
            results[lags] = avg_acc
        else:
            print(f"{lags:<10} | N/A")
            
if __name__ == '__main__':
    evaluate()
