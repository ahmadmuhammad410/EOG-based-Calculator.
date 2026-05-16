import os
import pandas as pd
import numpy as np
from scipy import signal
from pathlib import Path


FS = 176
LOWCUT = 0.5
HIGHCUT = 20.0
FILTER_ORDER = 4

def butter_bandpass_filter(data, lowcut=LOWCUT, highcut=HIGHCUT, fs=FS, order=FILTER_ORDER):
    nyq = 0.5 * fs
    low, high = lowcut / nyq, highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)

def preprocess_column(data):
    """
    Applies BPF + Downsampling to a single column (signal).
    Follows the logic from EOG_Logic.py
    """
    sig = np.array(data, dtype=float)
    if len(sig) == 0:
        return []

    # 2. Bandpass Filter
    # Note: Using FS=176 as defined in EOG_Logic.py
    bpf_full = butter_bandpass_filter(sig)

    # # 3. Downsampling to exactly 50 samples
    if len(bpf_full) > 50:
        bpf_down = signal.resample(bpf_full, 50)
    else:
        bpf_down = bpf_full
        
    return bpf_down

def process_all_files():
    trials = ['trail1', 'trail2', 'trail3', 'trail4']
    modes = ['horizontal', 'vertical']
    types = ['train', 'test']
    
    # Define possible base directories
    search_dirs = [Path("A_ExcelSheets"), Path(".")]
    output_base_dir = Path("B_preprocessed_ExcelSheets")
    
    # Create the base output directory if it doesn't exist
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    for trial in trials:
        # Create trial-specific output directory
        trial_output_dir = output_base_dir / trial
        trial_output_dir.mkdir(parents=True, exist_ok=True)
        
        for mode in modes:
            for t_type in types:
                filename = f"{trial}_{mode}_{t_type}.xlsx"
                
                # Find the file in either the root or ExcelSheets/trial/
                file_path = None
                for search_dir in search_dirs:
                    # Check nested path first
                    nested_path = search_dir / trial / filename
                    if nested_path.exists():
                        file_path = nested_path
                        break
                    
                    # Check direct path
                    direct_path = search_dir / filename
                    if direct_path.exists():
                        file_path = direct_path
                        break
                
                if file_path is None:
                    print(f"File {filename} not found anywhere, skipping.")
                    continue
                
                print(f"Preprocessing {file_path}...")
                try:
                    df = pd.read_excel(file_path)
                    
                    preprocessed_data = {}
                    for col in df.columns:
                        col_data = df[col].values
                        processed_col = preprocess_column(col_data)
                        preprocessed_data[col] = pd.Series(processed_col)
                    
                    df_new = pd.DataFrame(preprocessed_data)
                    
                    # Define new filename and path
                    new_filename = f"preprocessed_{filename}"
                    output_file_path = trial_output_dir / new_filename
                    
                    df_new.to_excel(output_file_path, index=False)
                    print(f"Successfully saved {output_file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    process_all_files()
