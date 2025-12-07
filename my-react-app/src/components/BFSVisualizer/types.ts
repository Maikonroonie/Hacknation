
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
  [nodeId: string]: number; 
}

export interface AnimationStep {
  activeNodeIds: string[];  // Nodes processing in this step
  activeEdgeIds: string[];  // Edges transmitting in this step (formatted "source-target")
  currentScores: MarketState; // Snapshot of scores at this step
}
