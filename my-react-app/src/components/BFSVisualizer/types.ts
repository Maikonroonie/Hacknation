export interface Node {
  id: string;
  x: number; // Współrzędna X (do rysowania)
  y: number; // Współrzędna Y
}

export interface Edge {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

// Stan pojedynczego kroku animacji
export interface BFSState {
  currentNode: string | null; // Węzeł aktualnie przetwarzany
  queue: string[]; // Węzły czekające w kolejce
  visited: string[]; // Węzły już odwiedzone
  path: string[]; // Krawędzie tworzące drzewo BFS (do podświetlenia)
}
