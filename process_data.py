
import pandas as pd
import json
import os
import numpy as np

# File paths
CONNECTIONS_PATH = 'connections.csv'
HARD_DATA_PATH = r'my-react-app\public\data\processed\hard_data_extnd.csv'
OUTPUT_PATH = r'my-react-app\src\components\BFSVisualizer\graph_data.json'

def create_mock_connections():
    print("Creating mock connections.csv since it was not found.")
    data = {
        'source': ['01', '01', '10', '10', '16', '23', '24', '29', '31', '35'],
        'target': ['10', '16', '23', '24', '29', '31', '35', '41', '46', '47'],
        'weight': [0.5, 0.3, 0.8, 0.2, 0.6, 0.7, 0.4, 0.9, 0.5, 0.6]
    }
    df = pd.DataFrame(data)
    df.to_csv(CONNECTIONS_PATH, index=False)
    return df

def process_data():
    # 1. Load Hard Data
    if not os.path.exists(HARD_DATA_PATH):
        print(f"Error: {HARD_DATA_PATH} not found.")
        return

    print(f"Loading {HARD_DATA_PATH}...")
    hard_data = pd.read_csv(HARD_DATA_PATH)
    
    # Filter for the latest year (2024-01-01) or use the most recent available per PKD
    # Assuming 'Date' column exists.
    if 'Date' in hard_data.columns:
        hard_data['Date'] = pd.to_datetime(hard_data['Date'])
        latest_date = hard_data['Date'].max()
        current_data = hard_data[hard_data['Date'] == latest_date].copy()
    else:
        current_data = hard_data.copy()

    # Normalize metrics to 0-100
    # We'll use a few key metrics to calculate a 'baseScore'
    # Metrics: Profit, Employment_Dynamics, Liquidity_Ratio
    # Handle NaN
    current_data = current_data.fillna(0)
    
    metrics_to_normalize = ['Profit', 'Revenue', 'Liquidity_Ratio']
    
    for metric in metrics_to_normalize:
        if metric in current_data.columns:
            min_val = current_data[metric].min()
            max_val = current_data[metric].max()
            if max_val != min_val:
                current_data[f'{metric}_norm'] = (current_data[metric] - min_val) / (max_val - min_val) * 100
            else:
                current_data[f'{metric}_norm'] = 50 # Default middle
        else:
            current_data[f'{metric}_norm'] = 50

    # Calculate baseScore (Simple average of normalized metrics for now)
    # Higher profit/revenue/liquidity -> Higher Score (Green)
    current_data['baseScore'] = current_data[[f'{m}_norm' for m in metrics_to_normalize]].mean(axis=1)

    # 2. Load Connections
    if not os.path.exists(CONNECTIONS_PATH):
        print(f"Warning: {CONNECTIONS_PATH} not found.")
        connections = create_mock_connections()
    else:
        connections = pd.read_csv(CONNECTIONS_PATH)
    
    # Ensure connections have string types for source/target
    connections['source'] = connections['source'].astype(str)
    connections['target'] = connections['target'].astype(str)
    # Ensure weight is float
    if 'weight' not in connections.columns:
         # If no weight, default to 1
         connections['weight'] = 1.0

    # 3. Build Graph Structure
    # Node Map: PKD_Code -> Node Data
    nodes = []
    # Get all unique PKDs from edges and hard_data
    all_pkd = set(connections['source']).union(set(connections['target']))
    
    # Create Node Objects
    for pkd in all_pkd:
        pkd_str = str(pkd)
        
        # Find matching hard data
        # Ensure PKD_Code in hard_data is string for matching
        current_data['PKD_Code'] = current_data['PKD_Code'].astype(str)
        
        record = current_data[current_data['PKD_Code'] == pkd_str]
        
        if not record.empty:
            base_score = float(record.iloc[0]['baseScore'])
            label = f"Branża {pkd_str}" # Could use a mapping if we had names
        else:
            base_score = 50.0 # Default
            label = f"Branża {pkd_str}"

        nodes.append({
            "id": pkd_str,
            "label": label,
            "baseScore": round(base_score, 2),
            "x": np.random.uniform(100, 700), # Random initial positions for vis
            "y": np.random.uniform(100, 500)
        })

    edges = []
    for _, row in connections.iterrows():
        edges.append({
            "source": str(row['source']),
            "target": str(row['target']),
            "weight": float(row['weight'])
        })

    output_data = {
        "nodes": nodes,
        "edges": edges
    }

    # 4. Save JSON
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Successfully generated {OUTPUT_PATH}")

if __name__ == "__main__":
    process_data()
