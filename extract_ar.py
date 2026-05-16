import os
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.tsa.ar_model import AutoReg
import warnings

# Suppress statsmodels warnings about missing frequency
warnings.filterwarnings('ignore', 'No frequency information was')

def extract_ar_fitted(data, lags=3):
    """
    Applies AutoRegressive model and returns the fitted values (filtered signal).
    Using lags=4 on a 50-sample signal results in exactly 46 values.
    """
    sig = np.array(data, dtype=float)
    sig = sig[~np.isnan(sig)]
    
    if len(sig) <= lags:
        # If signal is too short, return empty or zeros
        return [0.0] * (50 - lags)

    try:
        ar_mod = AutoReg(sig, lags=lags).fit()
        # Return the fitted values (predicted signal)
        return ar_mod.params.tolist()
    except Exception as e:
        # Fallback if AR fails
        return [0.0] * (len(sig) - lags)

def process_ar():
    input_base = Path("B_preprocessed_ExcelSheets")
    output_base = Path("E_AR_ExcelSheets")
    
    if not input_base.exists():
        print(f"Error: Directory '{input_base}' not found.")
        return
        
    output_base.mkdir(parents=True, exist_ok=True)
    
    trials = ['trail1', 'trail2', 'trail3', 'trail4']
    modes = ['horizontal', 'vertical']
    types = ['train', 'test']
    
    for trial in trials:
        trial_input_dir = input_base / trial
        trial_output_dir = output_base / trial
        
        if not trial_input_dir.exists():
            print(f"Warning: Directory '{trial_input_dir}' not found.")
            continue
            
        trial_output_dir.mkdir(parents=True, exist_ok=True)
        
        for mode in modes:
            for t_type in types:
                filename = f"preprocessed_{trial}_{mode}_{t_type}.xlsx"
                file_path = trial_input_dir / filename
                
                if not file_path.exists():
                    print(f"File {file_path} not found, skipping.")
                    continue
                
                print(f"Extracting AR fitted values for {file_path}...")
                try:
                    df = pd.read_excel(file_path)
                    
                    ar_data = {}
                    for col in df.columns:
                        col_data = df[col].values
                        ar_fitted = extract_ar_fitted(col_data, lags=3)
                        ar_data[col] = pd.Series(ar_fitted)
                    
                    df_ar = pd.DataFrame(ar_data)
                    
                    # Define new filename for AR
                    new_filename = f"ar_fitted_{trial}_{mode}_{t_type}.xlsx"
                    output_file_path = trial_output_dir / new_filename
                    
                    df_ar.to_excel(output_file_path, index=False)
                    print(f"Successfully saved {output_file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    process_ar()
