import os
import kagglehub
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    # ==========================================
    # PHASE 1: DATA ACQUISITION
    # ==========================================
    print("Fetching dataset from cache...")
    dataset_path = kagglehub.dataset_download("dhoogla/cicids2017")
    target_file = "DoS-Wednesday-no-metadata.parquet"
    file_path = os.path.join(dataset_path, target_file)
    
    print(f"Loading {target_file} into Pandas...")
    df = pd.read_parquet(file_path)
    
    # ==========================================
    # PHASE 2: DATA CLEANING & PREPROCESSING
    # ==========================================
    print("Cleaning messy network logs...")
    
    df.columns = df.columns.str.strip()
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed')
        df.sort_values('Timestamp', inplace=True)
        df.set_index('Timestamp', inplace=True)
    else:
        print("Timestamp column not found, using sequential index.")
        
    # ==========================================
    # PHASE 3: FEATURE SELECTION & ANOMALY DETECTION
    # ==========================================
    print("Applying statistical anomaly detection...")
    
    # UPDATED: The exact column name from the Parquet file
    feature = 'Fwd Packets Length Total' 
    
    if feature not in df.columns:
         print(f"Columns available: {df.columns.tolist()}")
         return
    
    window_size = 1000
    df['Rolling_Mean'] = df[feature].rolling(window=window_size).mean()
    df['Rolling_Std'] = df[feature].rolling(window=window_size).std()
    
    df['Z_Score'] = (df[feature] - df['Rolling_Mean']) / df['Rolling_Std']
    
    threshold = 3
    df['Anomaly'] = df['Z_Score'] > threshold
    
    anomalies = df[df['Anomaly']]
    
    # ==========================================
    # PHASE 4: VISUALIZATION 
    # ==========================================
    print(f"Found {len(anomalies)} anomalous traffic spikes. Generating plot...")
    
    plt.figure(figsize=(14, 7))
    
    plt.plot(df.index, df[feature], label="Raw Network Traffic", color='#1f77b4', alpha=0.5)
    plt.plot(df.index, df['Rolling_Mean'], label="Rolling Baseline (Normal)", color='black', linewidth=2)
    plt.scatter(anomalies.index, anomalies[feature], color='red', label="Detected Anomaly (DoS Flood)", s=10)
    
    plt.title("5G Network Traffic Prediction: DoS Anomaly Detection", fontsize=16, fontweight='bold')
    plt.xlabel("Network Flow Progression (Chronological)", fontsize=12)
    plt.ylabel("Total Forward Packet Length (Bytes)", fontsize=12)
    plt.legend(loc="upper left")
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()