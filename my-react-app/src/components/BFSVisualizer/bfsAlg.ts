import { GraphData, BFSState } from "./types";

export function* bfsGenerator(
  graph: GraphData,
  startNodeId: string
): Generator<BFSState> {
  const queue: string[] = [startNodeId];
  const visited = new Set<string>([startNodeId]);
  const parentMap: Record<string, string> = {}; // Do śledzenia skąd przyszliśmy

  // Tworzymy mapę sąsiedztwa dla łatwiejszego dostępu
  const adj: Record<string, string[]> = {};
  graph.nodes.forEach((n) => (adj[n.id] = []));
  graph.edges.forEach((e) => {
    adj[e.source].push(e.target);
    // Odkomentuj linię niżej, jeśli graf jest nieskierowany (działa w obie strony)
    // adj[e.target].push(e.source);
  });

  // Stan początkowy
  yield {
    currentNode: null,
    queue: [...queue],
    visited: [...visited],
    path: [],
  };

  while (queue.length > 0) {
    const current = queue.shift()!;

    // KROK 1: Pobranie z kolejki i przetwarzanie
    yield {
      currentNode: current,
      queue: [...queue],
      visited: Array.from(visited),
      path: buildPath(parentMap),
    };

    const neighbors = adj[current] || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        parentMap[neighbor] = current; // Zapisujemy rodzica
        queue.push(neighbor);

        // KROK 2: Dodanie sąsiada do kolejki
        yield {
          currentNode: current,
          queue: [...queue],
          visited: Array.from(visited),
          path: buildPath(parentMap),
        };
      }
    }
  }

  // Stan końcowy
  yield {
    currentNode: null,
    queue: [],
    visited: Array.from(visited),
    path: buildPath(parentMap),
  };
}

// Pomocnicza funkcja do budowania listy krawędzi, które zostały wykorzystane
function buildPath(parents: Record<string, string>): string[] {
  const edges: string[] = [];
  Object.entries(parents).forEach(([child, parent]) => {
    edges.push(`${parent}-${child}`);
    edges.push(`${child}-${parent}`); // dla pewności przy nieskierowanych
  });
  return edges;
}
