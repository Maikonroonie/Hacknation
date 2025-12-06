export interface Node {
  id: string;
  x: number;
  y: number;
}

export interface Edge {
  source: string;
  target: string;
  weight: number; // Waga wpływu (0.0 - 1.0)
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

// Stan symulacji rynku
export interface MarketState {
  scores: Record<string, number>; // Wynik dla każdego węzła (0-100, start 50)
  activeNode: string | null; // Węzeł aktualnie przetwarzany
  queue: string[]; // Kolejka do przetworzenia
  activeEdges: string[]; // Krawędzie, którymi płynie "impuls" w tym kroku
}
