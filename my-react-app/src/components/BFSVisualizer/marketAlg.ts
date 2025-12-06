import { GraphData, MarketState } from "./types";

export function* marketDynamicsGenerator(
  graph: GraphData,
  initialScores: Record<string, number>
): Generator<MarketState> {
  const scores = { ...initialScores };
  const queue: string[] = [];
  const MAX_DEPTH = 50;
  const IMPACT_THRESHOLD = 1.0; // Próg reakcji (jak w Pythonie)
  const processCounts: Record<string, number> = {};

  // Mapa sąsiedztwa (Kto na kogo wpływa + waga)
  const adj: Record<string, Array<{ target: string; weight: number }>> = {};
  graph.nodes.forEach((n) => (adj[n.id] = []));
  graph.edges.forEach((e) => {
    adj[e.source].push({ target: e.target, weight: e.weight });
  });

  // 1. Inicjalizacja kolejki (szukamy węzłów wychylonych od równowagi 50)
  Object.keys(scores).forEach((id) => {
    if (Math.abs(scores[id] - 50) > IMPACT_THRESHOLD) {
      queue.push(id);
    }
  });

  yield {
    scores: { ...scores },
    activeNode: null,
    queue: [...queue],
    activeEdges: [],
  };

  while (queue.length > 0) {
    const u_id = queue.shift()!;

    // Zabezpieczenie przed pętlą nieskończoną
    processCounts[u_id] = (processCounts[u_id] || 0) + 1;
    if (processCounts[u_id] > MAX_DEPTH) continue;

    const currentScore = scores[u_id];
    const force = currentScore - 50.0;

    // Jeśli siła jest za mała, wygaszamy impuls
    if (Math.abs(force) < IMPACT_THRESHOLD) continue;

    const neighbors = adj[u_id] || [];
    const activeEdgesInStep: string[] = [];

    // KROK WIZUALIZACJI: Pobrano węzeł, będziemy sprawdzać sąsiadów
    yield {
      scores: { ...scores },
      activeNode: u_id,
      queue: [...queue],
      activeEdges: [],
    };

    let changesMade = false;

    for (const edge of neighbors) {
      // Wpływ = Siła wychylenia * Waga połączenia
      // (Można dodać współczynnik tłumienia np. * 0.8, żeby system był stabilniejszy)
      const impact = force * edge.weight * 0.8;

      const oldVal = scores[edge.target] || 50.0;
      let newVal = oldVal + impact;

      // Clamp 0-100
      newVal = Math.max(0, Math.min(100, newVal));

      if (Math.abs(newVal - oldVal) > 0.5) {
        scores[edge.target] = newVal;
        queue.push(edge.target);
        activeEdgesInStep.push(`${u_id}-${edge.target}`);
        changesMade = true;
      }
    }

    if (changesMade) {
      // KROK WIZUALIZACJI: Zaktualizowano sąsiadów
      yield {
        scores: { ...scores },
        activeNode: u_id,
        queue: [...queue],
        activeEdges: activeEdgesInStep,
      };
    }
  }

  // Stan końcowy
  yield { scores: { ...scores }, activeNode: null, queue: [], activeEdges: [] };
}
