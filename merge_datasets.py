import pandas as pd
import os
from pathlib import Path

def merge_datasets():
    trials = ['trail1', 'trail2', 'trail3', 'trail4']
    splits = ['train', 'test']
    
    # Mapping of "k" (feature type) to its input folder and file prefix
    features = {
        'Raw': ('B_preprocessed_ExcelSheets', 'preprocessed_'),
        'DWT': ('C_DWT_ExcelSheets', 'dwt_a2_'),
        'AR': ('E_AR_ExcelSheets', 'ar_fitted_')
    }
    
    output_base = Path("Merged")
    output_base.mkdir(parents=True, exist_ok=True)
    
    for trial in trials:
        for split in splits:
            for feature_name, (input_folder, prefix) in features.items():
                # Construct input file paths
                h_file = Path(input_folder) / trial / f"{prefix}{trial}_horizontal_{split}.xlsx"
                v_file = Path(input_folder) / trial / f"{prefix}{trial}_vertical_{split}.xlsx"
                
                if not h_file.exists() or not v_file.exists():
                    print(f"Missing files for {trial} {split} {feature_name}. Checked:\n{h_file}\n{v_file}")
                    continue
                
                print(f"Merging {trial} | {split} | {feature_name}...")
                df_h = pd.read_excel(h_file)
                df_v = pd.read_excel(v_file)
                
                # Verify column count matches
                if len(df_h.columns) != len(df_v.columns):
                    print(f"Warning: Column count mismatch for {trial} {split} {feature_name}. Skipping.")
                    continue
                    
                merged_data = {}
                for i in range(len(df_h.columns)):
                    col_h = df_h.columns[i]
                    col_v = df_v.columns[i]
                    
                    # Add horizontal and vertical columns side-by-side
                    merged_data[col_h] = df_h.iloc[:, i]
                    merged_data[col_v] = df_v.iloc[:, i]
                
                df_merged = pd.DataFrame(merged_data)
                
                # Naming convention: "traili_j_k" -> e.g., trail1_train_DWT.xlsx
                out_filename = f"{trial}_{split}_{feature_name}.xlsx"
                out_filepath = output_base / out_filename
                
                df_merged.to_excel(out_filepath, index=False)
                print(f"Successfully saved: {out_filepath}")

if __name__ == "__main__":
    merge_datasets()
