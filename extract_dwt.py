import os
import pandas as pd
import numpy as np
import pywt
from pathlib import Path

def extract_a2_column(data):
    """
    Applies DWT (db4, level=2) and returns the a2 approximation coefficients.
    """
    sig = np.array(data, dtype=float)
    sig = sig[~np.isnan(sig)]
    
    if len(sig) == 0:
        return []

    # Perform DWT with db4, level 2
    coeffs = pywt.wavedec(sig, 'db4', level=2)
    
    # coeffs[0] is the approximation coefficient (a2)
    a2 = coeffs[0]
    return a2

def process_dwt():
    input_base = Path("A_ExcelSheets")
    output_base = Path("C_DWT_ExcelSheets")
    
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
                filename = f"{trial}_{mode}_{t_type}.xlsx"
                file_path = trial_input_dir / filename
                
                if not file_path.exists():
                    print(f"File {file_path} not found, skipping.")
                    continue
                
                print(f"Extracting DWT A2 for {file_path}...")
                try:
                    df = pd.read_excel(file_path)
                    
                    dwt_data = {}
                    for col in df.columns:
                        col_data = df[col].values
                        a2_col = extract_a2_column(col_data)
                        dwt_data[col] = pd.Series(a2_col)
                    
                    df_dwt = pd.DataFrame(dwt_data)
                    
                    # Define new filename for DWT
                    new_filename = f"dwt_a2_{trial}_{mode}_{t_type}.xlsx"
                    output_file_path = trial_output_dir / new_filename
                    
                    df_dwt.to_excel(output_file_path, index=False)
                    print(f"Successfully saved {output_file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    process_dwt()
