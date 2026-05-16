import os
import pandas as pd
import re

def natural_sort_key(s):
    """
    Key for natural sorting (e.g., 'sol2h' comes before 'sol10h').
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def make_dataset():
    base_path = "3-class"
    if not os.path.exists(base_path):
        print(f"Error: Base path '{base_path}' not found.")
        return
        
    classes = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    modes = ['horizontal', 'vertical']
    
    # Define trials and their logic
    # Trial 1: Train 1-15, Test 16-20
    # Trial 2: Train 1-10 & 16-20, Test 11-15
    trials = [
        {
            "name": "trail1",
            "train_indices": list(range(0, 15)),
            "test_indices": list(range(15, 20))
        },
        {
            "name": "trail2",
            "train_indices": list(range(0, 10)) + list(range(15, 20)),
            "test_indices": list(range(10, 15))
        },
        {
            "name": "trail3",
            "train_indices": list(range(0, 5)) + list(range(10, 20)),
            "test_indices": list(range(5, 10))
        },
        {
            "name": "trail4",
            "train_indices": list(range(5, 20)),
            "test_indices": list(range(0, 5))
        }
    ]

    for trial in trials:
        trial_name = trial["name"]
        print(f"\n--- Processing {trial_name} ---")
        
        for mode in modes:
            train_data = {}
            test_data = {}
            
            print(f"Processing {mode} mode for {trial_name}...")
            
            for cls in classes:
                folder = os.path.join(base_path, cls, mode)
                if not os.path.exists(folder):
                    continue
                    
                files = [f for f in os.listdir(folder) if f.endswith('.txt')]
                files.sort(key=natural_sort_key)
                
                # Check if we have enough files
                max_idx = max(max(trial["train_indices"]), max(trial["test_indices"]))
                if len(files) <= max_idx:
                    print(f"Warning: {folder} has only {len(files)} files. Some indices might be out of range.")
                
                # Select train files based on indices
                for i in trial["train_indices"]:
                    if i < len(files):
                        f = files[i]
                        file_path = os.path.join(folder, f)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                data = [line.strip() for line in file.readlines() if line.strip()]
                                data = pd.to_numeric(data, errors='coerce')
                                col_name = os.path.splitext(f)[0]
                                train_data[col_name] = pd.Series(data)
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")

                # Select test files based on indices
                for i in trial["test_indices"]:
                    if i < len(files):
                        f = files[i]
                        file_path = os.path.join(folder, f)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                data = [line.strip() for line in file.readlines() if line.strip()]
                                data = pd.to_numeric(data, errors='coerce')
                                col_name = os.path.splitext(f)[0]
                                test_data[col_name] = pd.Series(data)
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")
            
            # Save Train Excel
            if train_data:
                df_train = pd.DataFrame(train_data)
                train_filename = f"{trial_name}_{mode}_train.xlsx"
                df_train.to_excel(train_filename, index=False)
                print(f"Saved {train_filename} ({len(df_train.columns)} columns)")
            
            # Save Test Excel
            if test_data:
                df_test = pd.DataFrame(test_data)
                test_filename = f"{trial_name}_{mode}_test.xlsx"
                df_test.to_excel(test_filename, index=False)
                print(f"Saved {test_filename} ({len(df_test.columns)} columns)")

if __name__ == "__main__":
    make_dataset()
