import csv
import json
import os

# --- KONFIGURACJA ---
INPUT_FILE = 'connections.csv'
OUTPUT_FILE = 'graph_data.json'
# Filtrowanie: Pomiń zależności mniejsze niż 2% (dla czytelności wykresu)
MIN_PERCENTAGE_THRESHOLD = 2.0 

KEY_INDUSTRIES = [
    '01', '10', '16', '23', '24', '29', '31', '35', 
    '41', '68', '46', '47', '49', '55', '62'
]

def parse_and_export():
    dependency_dict = {}
    clean = lambda x: x.replace('(', '').replace(')', '').strip()

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            
            # 1. Nagłówki (Kupujący)
            headers = []
            target_indices = []
            
            while not headers:
                try:
                    row = next(reader)
                except StopIteration: return
                
                raw_headers = [clean(x) for x in row if x.strip()]
                
                for idx, pkd in enumerate(raw_headers):
                    if pkd in KEY_INDUSTRIES:
                        target_indices.append((idx, pkd))
                        dependency_dict[pkd] = []
                
                if raw_headers: headers = raw_headers

            # 2. Wiersze (Dostawcy)
            for row in reader:
                if not row: continue
                supplier_pkd = clean(row[0])
                
                if supplier_pkd not in KEY_INDUSTRIES:
                    continue
                
                values = row[1:]
                for col_idx, buyer_pkd in target_indices:
                    if col_idx < len(values):
                        try:
                            val_str = values[col_idx].replace(',', '.').strip()
                            if not val_str: continue
                            weight = float(val_str)
                            if weight > 0:
                                dependency_dict[buyer_pkd].append({'weight': weight, 'supplier': supplier_pkd})
                        except ValueError: pass

        # 3. Normalizacja i Budowa Struktury JSON
        nodes = []
        edges = []
        
        # Tworzymy listę węzłów
        for ind in KEY_INDUSTRIES:
            nodes.append({"id": ind})

        # Tworzymy krawędzie
        for industry in dependency_dict:
            total_weight = sum(item['weight'] for item in dependency_dict[industry])
            
            if total_weight > 0:
                for item in dependency_dict[industry]:
                    percentage = (item['weight'] / total_weight) * 100
                    
                    # Zapisujemy tylko znaczące połączenia
                    if percentage >= MIN_PERCENTAGE_THRESHOLD:
                        # UWAGA: W Twoim modelu:
                        # Dostawca WPLYWA na Klienta.
                        # source = supplier, target = buyer (industry)
                        edges.append({
                            "source": item['supplier'],
                            "target": industry,
                            "weight": round(percentage / 100, 4) # Skala 0.0 - 1.0 dla algorytmu
                        })

        output_data = {
            "nodes": nodes,
            "edges": edges
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
            
        print(f"Sukces! Dane zapisano do {OUTPUT_FILE}")
        print(f"Znaleziono {len(nodes)} węzłów i {len(edges)} krawędzi.")

    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {INPUT_FILE}")

if __name__ == '__main__':
    parse_and_export()