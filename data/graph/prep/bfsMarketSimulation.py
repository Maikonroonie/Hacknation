from collections import deque

def bfs_market_dynamics(G, scores, max_depth=100, impact_threshold=1.0):
    """
    Symuluje rynek, gdzie 50 to punkt równowagi.
    G: Słownik z listami sąsiedztwa. Obsługuje format (Waga, ID) lub (ID, Waga).
    scores: Słownik {id: score (0-100)}
    """
    
    q = deque()
    process_counts = {id: 0 for id in scores}
    
    # Inicjalizacja kolejki (firmy odchylone od normy 50)
    for id, score in scores.items():
        if abs(score - 50) > impact_threshold:
            q.append(id)

    while q:
        u_id = q.popleft()
        
        # Zabezpieczenie przed nieskończoną pętlą dla jednego węzła
        if process_counts.get(u_id, 0) > max_depth:
            continue
        process_counts[u_id] = process_counts.get(u_id, 0) + 1
        
        # Pobranie aktualnego wyniku i obliczenie "siły"
        # Jeśli nie ma wyniku w scores, przyjmujemy 50 (neutralny)
        current_score = scores.get(u_id, 50.0)
        force = current_score - 50.0
        
        # Jeśli siła jest zbyt mała, nie przekazujemy jej dalej
        if abs(force) < impact_threshold:
            continue

        if u_id in G:
            # --- POPRAWKA GŁÓWNA ---
            # Iterujemy po liście. Sprawdzamy typy danych, żeby uniknąć błędu.
            for item in G[u_id]:
                # Rozpakowanie w zależności od tego, co jest pierwsze (liczba czy napis)
                if isinstance(item[0], (int, float)):
                    weight, v_id = item[0], item[1]  # Format (Waga, ID)
                else:
                    v_id, weight = item[0], item[1]  # Format (ID, Waga)

                # --- POPRAWKA MATEMATYCZNA ---
                # Twoje wagi są w procentach (np. 15.5 dla 15.5%). 
                # Musimy zamienić to na mnożnik (0.155), dzieląc przez 100.
                factor = weight / 100.0
                
                impact = force * factor
                
                # Aktualizacja sąsiada
                old_val = scores.get(v_id, 50.0)
                new_val = old_val + impact
                
                # Ograniczenie do zakresu 0-100
                new_val = max(0.0, min(100.0, new_val))
                
                # Jeśli zmiana jest istotna, aktualizujemy i dodajemy do kolejki
                if abs(new_val - old_val) > impact_threshold:
                    scores[v_id] = new_val
                    q.append(v_id)

    return scores