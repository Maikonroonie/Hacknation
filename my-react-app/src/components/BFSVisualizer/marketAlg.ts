import { GraphData, MarketState, AnimationStep } from './types';

export const generateBFSSteps = (
  graph: GraphData
): AnimationStep[] => {
  const steps: AnimationStep[] = [];
  
  // Constants
  const DAMPING = 0.9;
  const THRESHOLD = 0.0001; // Minimum deviation to trigger propagation
  const MAX_STEPS = 100;

  // Initialize Adjacency Map
  const adj: { [key: string]: { target: string, weight: number }[] } = {};
  graph.edges.forEach(edge => {
    if (!adj[edge.source]) adj[edge.source] = [];
    adj[edge.source].push({ target: edge.target, weight: edge.weight });
  });

  // State
  const totalImpacts: { [key: string]: number } = {};
  const baseScores: { [key: string]: number } = {};
  graph.nodes.forEach(n => {
    baseScores[n.id] = n.baseScore;
    totalImpacts[n.id] = 0;
  });

  const getCurrentScores = (): MarketState => {
    const state: MarketState = {};
    graph.nodes.forEach(n => {
      const val = baseScores[n.id] + (totalImpacts[n.id] || 0);
      state[n.id] = Math.max(0, Math.min(100, val));
    });
    return state;
  };

  // Step 0: Initial "Tension"
  // Nodes with score != 50 emit a wave.
  let waveFront: { [nodeId: string]: number } = {};
  
  graph.nodes.forEach(n => {
      const deviation = n.baseScore - 50;
      if (Math.abs(deviation) >= THRESHOLD) {
          waveFront[n.id] = deviation;
      }
  });

  steps.push({
    activeNodeIds: Object.keys(waveFront),
    activeEdgeIds: [],
    currentScores: getCurrentScores()
  });

  // BFS / Propagation Loop
  for (let step = 0; step < MAX_STEPS; step++) {
    const nextWaveFront: { [nodeId: string]: number } = {};
    const activeEdges: string[] = [];
    const activeNodesThisStep: string[] = [];

    const nodesToPropagate = Object.keys(waveFront);
    if (nodesToPropagate.length === 0) break;

    // For each node in the current wave
    nodesToPropagate.forEach(sourceId => {
      const delta = waveFront[sourceId];
      const neighbors = adj[sourceId] || [];

      neighbors.forEach(edge => {
        const passedDelta = delta * edge.weight * DAMPING;
        
        if (Math.abs(passedDelta) >= THRESHOLD) {
            // Add to next wave
            nextWaveFront[edge.target] = (nextWaveFront[edge.target] || 0) + passedDelta;
            
            // Mark edge as active
            activeEdges.push(`${sourceId}-${edge.target}`);
        }
      });
    });

    // Apply the next wave impacts to the TOTAL
    Object.keys(nextWaveFront).forEach(targetId => {
       totalImpacts[targetId] = (totalImpacts[targetId] || 0) + nextWaveFront[targetId];
       activeNodesThisStep.push(targetId);
    });

    if (activeNodesThisStep.length === 0 && activeEdges.length === 0) {
        break; // Die out
    }
    
    steps.push({
        activeNodeIds: activeNodesThisStep,
        activeEdgeIds: activeEdges,
        currentScores: getCurrentScores()
    });

    waveFront = nextWaveFront;
  }

  return steps;
};
