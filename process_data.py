
import pandas as pd
import json
import os
import numpy as np

# File paths
CONNECTIONS_PATH = r'my-react-app\public\data\processed\connections.csv'
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

def load_connections_matrix(path):
    print(f"Loading matrix from {path}...")
    # Read CSV with ; separator and , as decimal
    # header=0 implies the first row is columns. 
    # index_col=0 implies the first column is the index (source).
    df = pd.read_csv(path, sep=';', decimal=',', index_col=0)
    
    # Clean up column names and index (remove parens)
    # The file has a trailing empty column sometimes due to trailing ;
    df = df.dropna(axis=1, how='all')
    
    def clean_label(label):
        if isinstance(label, str):
            val = label.replace('(', '').replace(')', '').strip()
            # Handle headers like '( 01 )' -> '01'
            return val
        return str(label)

    df.columns = [clean_label(c) for c in df.columns]
    df.index = [clean_label(i) for i in df.index]

    edges = []
    # Identify non-zero connections
    # Iterate over matrix
    for source in df.index:
        for target in df.columns:
            try:
                weight = float(df.loc[source, target])
                if weight > 0.0001: # Threshold to filter weak links
                    edges.append({
                        'source': source,
                        'target': target,
                        'weight': weight
                    })
            except Exception as e:
                continue
                
    return pd.DataFrame(edges)

def process_data():
    # 1. Load Hard Data
    if not os.path.exists(HARD_DATA_PATH):
        print(f"Error: {HARD_DATA_PATH} not found.")
        return

    print(f"Loading {HARD_DATA_PATH}...")
    hard_data = pd.read_csv(HARD_DATA_PATH)
    
    # Filter for the latest year (2024-01-01) or use the most recent available per PKD
    if 'Date' in hard_data.columns:
        hard_data['Date'] = pd.to_datetime(hard_data['Date'])
        latest_date = hard_data['Date'].max()
        current_data = hard_data[hard_data['Date'] == latest_date].copy()
    else:
        current_data = hard_data.copy()

    # Normalize metrics to 0-100
    current_data = current_data.fillna(0)
    metrics_to_normalize = ['Profit', 'Revenue', 'Liquidity_Ratio']
    
    for metric in metrics_to_normalize:
        if metric in current_data.columns:
            min_val = current_data[metric].min()
            max_val = current_data[metric].max()
            if max_val != min_val:
                current_data[f'{metric}_norm'] = (current_data[metric] - min_val) / (max_val - min_val) * 100
            else:
                current_data[f'{metric}_norm'] = 50
        else:
            current_data[f'{metric}_norm'] = 50

    current_data['baseScore'] = current_data[[f'{m}_norm' for m in metrics_to_normalize]].mean(axis=1)

    # 2. Load Connections (Matrix)
    if not os.path.exists(CONNECTIONS_PATH):
        print(f"Warning: {CONNECTIONS_PATH} not found. Creating mock.")
        connections = create_mock_connections()
    else:
        connections = load_connections_matrix(CONNECTIONS_PATH)
    
    connections['source'] = connections['source'].astype(str)
    connections['target'] = connections['target'].astype(str)
    
    # 3. Build Graph Structure
    KEY_SECTORS = ['01', '10', '16', '23', '24', '29', '31', '35', '41', '68', '46', '47', '49', '55', '62']
    
    PKD_NAMES = {
        '01': 'Rolnictwo (01)',
        '10': 'Spożywczy (10)',
        '16': 'Drewno (16)',
        '23': 'Ceramika/Bud (23)',
        '24': 'Metale (24)',
        '29': 'Automotive (29)',
        '31': 'Meble (31)',
        '35': 'Energetyka (35)',
        '41': 'Budownictwo (41)',
        '68': 'Nieruchomości (68)',
        '46': 'Hurt (46)',
        '47': 'Detal (47)',
        '49': 'Transport (49)',
        '55': 'Hotele (55)',
        '62': 'IT (62)'
    }

    nodes = []
    # Only use keys present in our whitelist
    all_pkd = set(connections['source']).union(set(connections['target']))
    filtered_pkd = [pkd for pkd in all_pkd if str(pkd) in KEY_SECTORS]
    
    # Ensure PKD_Code in hard_data is string
    current_data['PKD_Code'] = current_data['PKD_Code'].astype(str)
    
    for pkd in filtered_pkd:
        pkd_str = str(pkd)
        record = current_data[current_data['PKD_Code'] == pkd_str]
        
        if not record.empty:
            base_score = float(record.iloc[0]['baseScore'])
        else:
            base_score = 50.0 
            
        label = PKD_NAMES.get(pkd_str, f"Branża {pkd_str}")

        nodes.append({
            "id": pkd_str,
            "label": label,
            "baseScore": round(base_score, 2),
            "x": np.random.uniform(100, 700),
            "y": np.random.uniform(100, 500)
        })

    edges = []
    valid_ids = set(n['id'] for n in nodes)
    
    for _, row in connections.iterrows():
        s = str(row['source'])
        t = str(row['target'])
        if s in valid_ids and t in valid_ids:
            edges.append({
                "source": s,
                "target": t,
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
