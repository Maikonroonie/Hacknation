import csv
import os  # <--- 1. Dodano bibliotekę os

# List of industries to keep (Exact match required)
KEY_INDUSTRIES = [
    '01', '10', '16', '23', '24', '29', '31', '35', 
    '41', '68', '46', '47', '49', '55', '62'
]

def parse_csv_data(file_path):
    dependency_dict = {}
    
    # Helper to clean "( 01 )" -> "01"
    clean = lambda x: x.replace('(', '').replace(')', '').strip()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            
            # 1. Parse Headers (Columns = Buyers)
            headers = []
            target_indices = [] # Stores (index, pkd_code) for columns we want to keep
            
            while not headers:
                try:
                    row = next(reader)
                except StopIteration: return {}
                
                # Get all headers first
                raw_headers = [clean(x) for x in row if x.strip()]
                
                # Filter: Identify which columns match KEY_INDUSTRIES
                for idx, pkd in enumerate(raw_headers):
                    if pkd in KEY_INDUSTRIES:
                        target_indices.append((idx, pkd))
                        dependency_dict[pkd] = [] # Initialize list for this industry
                
                if raw_headers: headers = raw_headers

            # 2. Parse Rows (Rows = Suppliers)
            for row in reader:
                if not row: continue
                
                supplier_pkd = clean(row[0])
                
                # Filter: Skip rows that are NOT in our key list
                if supplier_pkd not in KEY_INDUSTRIES:
                    continue
                
                values = row[1:]
                
                # Only extract data for columns we care about
                for col_idx, buyer_pkd in target_indices:
                    if col_idx < len(values):
                        try:
                            weight = float(values[col_idx].replace(',', '.').strip())
                            if weight > 0:
                                # Raw extraction: (Weight, Supplier) - temporary used for sorting
                                dependency_dict[buyer_pkd].append((weight, supplier_pkd))
                        except ValueError: pass

        # 3. Sort by weight descending (pre-normalization)
        for pkd in dependency_dict:
            dependency_dict[pkd].sort(key=lambda x: x[0], reverse=True)

        return dependency_dict

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return {}

# --- GLÓWNA CZĘŚĆ KODU ---

# 2. Naprawa ścieżki do pliku (zawsze szuka obok skryptu)
script_dir = os.path.dirname(os.path.abspath(__file__))
file_name = os.path.join(script_dir, 'connections.csv')

graph = parse_csv_data(file_name)

if graph:
    for industry in graph:
        # industry to teraz DOSTAWCA
        total_weight = sum(weight for weight, _ in graph[industry])
        
        if total_weight > 0:
            normalized_list = []
            for weight, client in graph[industry]: # client zamiast supplier
                percentage = (weight / total_weight) * 100
                
                # Pamiętaj o kolejności dla BFS: (NAZWA, WAGA) lub (WAGA, NAZWA)
                # Skoro naprawiliśmy BFS, trzymajmy się (NAZWA, WAGA/PROCENT)
                normalized_list.append((client, percentage)) 
            
            graph[industry] = normalized_list

    # Print Example
    first_key = '35' # Sprawdźmy Energetykę
    if first_key in graph:
        print(f"--- Kogo zasila branża {first_key}? (Impact Downstream) ---")
        for client, pct in graph[first_key]:
            print(f"Impacts Client {client}: {pct:.2f}%")