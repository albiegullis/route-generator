import kagglehub
import pandas as pd
import os

print("Downloading CIC-IDS2017 dataset...")
dataset_path = kagglehub.dataset_download("dhoogla/cicids2017")

files = os.listdir(dataset_path)

# Look for parquet files instead of csv
parquet_files = [f for f in files if f.endswith('.parquet')]

if parquet_files:
    # Target the DoS attack logs directly
    target_file = "DoS-Wednesday-no-metadata.parquet"
    file_path = os.path.join(dataset_path, target_file)
    
    print(f"\nLoading {target_file} into Pandas...")
    
    # Read the parquet file
    df = pd.read_parquet(file_path) 
    
    # Print the first 5 rows and the total row count
    print(df.head())
    print(f"\nTotal rows loaded: {len(df)}")