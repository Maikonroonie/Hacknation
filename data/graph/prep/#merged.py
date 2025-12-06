import os
import matplotlib.pyplot as plt
from corelations import parse_csv_data
from justScores import getScores
from bfsMarketSimulation import bfs_market_dynamics

# 1. Ustal katalog i ścieżki
script_dir = os.path.dirname(os.path.abspath(__file__))
connections_path = os.path.join(script_dir, 'connections.csv')

print(f"--- START ---")
print(f"Wczytuję graf z: {connections_path}")

# 2. Wczytaj dane
G = parse_csv_data(connections_path)
scores = getScores()

# Sprawdzenie
if not G or not scores:
    print("Błąd: Brak danych (graf lub wyniki są puste).")
    exit()

print(f"Liczba węzłów w grafie G: {len(G)}")

# 3. Zrób KOPIĘ wyników przed symulacją (Kluczowe!)
# Musimy to zrobić, bo funkcja bfs modyfikuje słownik, na którym pracuje.
initial_scores = scores.copy()

print("\n--- Symulacja ---")
# 4. Uruchomienie symulacji na oryginalnym słowniku 'scores'
final_scores = bfs_market_dynamics(G, scores, impact_threshold=0.01)

# 5. Przygotowanie danych do wykresu
# Sortujemy klucze, aby oś X była uporządkowana
pkd_codes = sorted(initial_scores.keys())

y_before = [initial_scores.get(pkd, 50) for pkd in pkd_codes]
y_after = [final_scores.get(pkd, 50) for pkd in pkd_codes]

# 6. Rysowanie wykresu
plt.figure(figsize=(12, 6))

# Rysujemy punkty "Przed" (Niebieskie)
plt.scatter(pkd_codes, y_before, color='blue', label='Przed symulacją', alpha=0.6, s=80)

# Rysujemy punkty "Po" (Czerwone)
plt.scatter(pkd_codes, y_after, color='red', label='Po symulacji', alpha=0.8, s=80)

# Rysujemy linie łączące, żeby pokazać zmianę (strzałki/linie)
for i in range(len(pkd_codes)):
    if y_before[i] != y_after[i]: # Rysuj linię tylko jeśli była zmiana
        plt.plot([pkd_codes[i], pkd_codes[i]], [y_before[i], y_after[i]], color='gray', linestyle='--', alpha=0.5)

plt.title('Symulacja wpływu rynku na PKO Score (PKD)')
plt.xlabel('Kody PKD')
plt.ylabel('PKO Score')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)

# Wyświetl wykres
plt.show()