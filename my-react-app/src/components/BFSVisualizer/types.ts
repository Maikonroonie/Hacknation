
export interface Node {
  id: string;
  label: string;
  baseScore: number;
  x?: number;
  y?: number;
}

export interface Edge {
  source: string;
  target: string;
  weight: number;
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

export interface MarketState {
  [nodeId: string]: number; // Current delta/score for each node
}
