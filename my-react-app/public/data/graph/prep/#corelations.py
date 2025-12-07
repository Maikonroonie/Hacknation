import csv

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
            
            headers = []
            target_indices = [] 
            
            while not headers:
                try:
                    row = next(reader)
                except StopIteration: return {}
                
                raw_headers = [clean(x) for x in row if x.strip()]
                
                for idx, pkd in enumerate(raw_headers):
                    if pkd in KEY_INDUSTRIES:
                        target_indices.append((idx, pkd))
                        # dependency_dict[pkd] = []  <--- USUNIĘTE: Nie inicjalizujemy tutaj po kluczach-Kupujących
                
                if raw_headers: headers = raw_headers

            # Inicjalizacja słownika dla wszystkich branż (żeby każdy mógł być nadawcą)
            for pkd in KEY_INDUSTRIES:
                if pkd not in dependency_dict:
                    dependency_dict[pkd] = []

            for row in reader:
                if not row: continue
                
                supplier_pkd = clean(row[0])
                
                if supplier_pkd not in KEY_INDUSTRIES:
                    continue
                
                # Upewnij się, że dostawca jest w słowniku
                if supplier_pkd not in dependency_dict:
                    dependency_dict[supplier_pkd] = []

                values = row[1:]
                
                for col_idx, buyer_pkd in target_indices:
                    if col_idx < len(values):
                        try:
                            weight = float(values[col_idx].replace(',', '.').strip())
                            if weight > 0:
                                # --- ODWRÓCENIE KRAWĘDZI ---
                                # Było: dependency_dict[buyer_pkd].append((weight, supplier_pkd))
                                # Jest: Dostawca wpływa na Kupującego
                                dependency_dict[supplier_pkd].append((weight, buyer_pkd)) 
                        except ValueError: pass

        # Sortowanie
        for pkd in dependency_dict:
            dependency_dict[pkd].sort(key=lambda x: x[0], reverse=True)

        return dependency_dict

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return {}