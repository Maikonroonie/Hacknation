from collections import deque

def bfs_market_dynamics(G, scores, max_depth=100, impact_threshold=1.0):
    """
    Symuluje rynek, gdzie 50 to punkt równowagi.
    G: Słownik {Dostawca: [(Klient, Waga), ...]} -> Graf PUSH
    scores: Słownik {id: score (0-100)}
    """
    
    q = deque()
    
    process_counts = {id: 0 for id in scores}
    
    for id, score in scores.items():
        if abs(score - 50) > impact_threshold:
            q.append(id)

    while q:
        u_id = q.popleft()
        
        if process_counts.get(u_id, 0) > max_depth:
            continue
        process_counts[u_id] = process_counts.get(u_id, 0) + 1
        
        current_score = scores[u_id]
        

        force = current_score - 50.0
       
        if abs(force) < impact_threshold:
            continue


        if u_id in G:
            for v_id, weight in G[u_id]:
                
                impact = force * weight
                
                old_val = scores.get(v_id, 50.0)
                
                new_val = old_val + impact
                
                new_val = max(0.0, min(100.0, new_val))
                
                if abs(new_val - old_val) > impact_threshold:
                    scores[v_id] = new_val
                    q.append(v_id)

    return scores

# --- PRZYKŁAD UŻYCIA ---

# Graf zależności (Dostawca -> [(Klient, Waga)])
# Uwaga: Wagi powinny być mniejsze (np. 0.1, 0.2), bo inaczej system szybko "wybuchnie" do 100 lub 0.
test_graph = {
    'IT': [('Banki', 0.5)],       # IT mocno wpływa na Banki
    'Banki': [('Budowlanka', 0.3)] # Banki (kredyty) wpływają na Budowlankę
}

# Sytuacja rynkowa:
# IT ma boom (80), reszta jest neutralna (50)
market_scores = {
    'IT': 80, 
    'Banki': 50, 
    'Budowlanka': 50
}

print("--- Przed Symulacją ---")
print(market_scores)

final_scores = bfs_market_dynamics(test_graph, market_scores)

print("\n--- Po Symulacji (Efekt Wzrostu) ---")
# Oczekujemy: IT (80) -> pociągnie Banki w górę -> Banki pociągną Budowlankę
for k, v in final_scores.items():
    print(f"{k}: {v:.1f}")

