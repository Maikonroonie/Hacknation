
import { GraphData, MarketState } from './types';

export const calculateMarketState = (
  graph: GraphData,
  userDeltas: MarketState // Map of user-applied deltas (e.g., node '01' -> +10)
): MarketState => {
  // Initialize current deltas with user deltas
  const currentDeltas: { [key: string]: number } = { ...userDeltas };
  const finalScores: { [key: string]: number } = {};

  // Initialize BFS queue with nodes that have user input
  const queue: string[] = Object.keys(userDeltas);
  
  // Track visited or processed to prevent cycles/infinite loops? 
  // For continuous propagation in a cyclic graph, we usually iterate until convergence or fixed steps.
  // BFS suggests "ripples". Let's do a Ripple with depth limit or threshold.
  
  // Let's use a simple iterative approach for propagation to allow multiple sources to mix.
  // Using a "push" model. 
  
  // Create an adjacency list for easier lookup
  const adj: { [key: string]: { target: string, weight: number }[] } = {};
  graph.edges.forEach(edge => {
    if (!adj[edge.source]) adj[edge.source] = [];
    adj[edge.source].push({ target: edge.target, weight: edge.weight });
    
    // Assuming undirected or bidirectional influence? 
    // Usually supply chain is directional, but shocks might travel both ways.
    // The visualizer implies "BFS", so standard directed traversal usually.
    // If user wants undirected, we'd add the reverse edge. Let's assume directed as per CSV source->target.
  });

  // We need to calculate the TOTAL impact on each node.
  // Impact = UserDelta + Sum(IncomingImpact * Weight)
  
  // To avoid cycles exploding, we can use a damping factor `alpha`.
  const DAMPING = 0.9;
  const MIN_DELTA = 0.1; // Stop propagating if change is negligible

  // State to hold accumulated delta for each node from propagation
  const propagatedDeltas: { [key: string]: number } = {};
  
  // Initialize propagatedDeltas with userDeltas
  Object.keys(currentDeltas).forEach(k => {
    propagatedDeltas[k] = currentDeltas[k];
  });

  // Processing Queue: [NodeID, IncomingDelta]
  // We actually need to process 'pulses'.
  type Signal = { nodeId: string; delta: number };
  let signalQueue: Signal[] = Object.entries(userDeltas).map(([k, v]) => ({ nodeId: k, delta: v }));
  
  // To prevent infinite loops in cyclic graphs, we can limit the number of hops or track total updates.
  // Or better, for a "Visualizer", a simplified 1-pass or 2-pass expansion is often enough.
  // Let's do a robust BFS with visited set per source? No, effects stack.
  
  // Simple BFS with Threshold:
  // If a node receives a delta, add it to its total. If that delta > MIN_DELTA, propagate to neighbors (weighted).
  // Be careful with cycles (A->B->A). 
  // We can track 'active' nodes.
  
  // Refined Logic:
  // We handle specific "events".
  // Only propagate the *new* delta.
  
  // Since we are re-calculating from scratch each frame/change:
  // 1. Start with Nodes X, Y... having Delta D_x, D_y...
  // 2. Propagate these to neighbors.
  // 3. Repeat. 
  
  // To stop cycles: Limit hops (e.g., 5 levels).
  
  const MAX_HOPS = 5;
  
  // queue: { nodeId, val, depth }
  const bfsQueue: { nodeId: string; val: number; depth: number }[] = 
    Object.entries(userDeltas).map(([k, v]) => ({ nodeId: k, val: v, depth: 0 }));
    
  // We accumulate the 'effect' on each node.
  const nodeEffects: { [key: string]: number } = {};
  
  while (bfsQueue.length > 0) {
    const { nodeId, val, depth } = bfsQueue.shift()!;
    
    // Accumulate effect
    nodeEffects[nodeId] = (nodeEffects[nodeId] || 0) + val;
    
    if (depth >= MAX_HOPS) continue;
    if (Math.abs(val) < MIN_DELTA) continue;
    
    const neighbors = adj[nodeId] || [];
    for (const neighbor of neighbors) {
      const transmittedVal = val * neighbor.weight * DAMPING;
      bfsQueue.push({
        nodeId: neighbor.target,
        val: transmittedVal,
        depth: depth + 1
      });
    }
  }

  // Now calculate Final Score = BaseScore + NodeEffects.
  // We need baseScores from graph.
  // But this function returns "MarketState". 
  // Let's assume MarketState is just the *Values* (0-100) or just the *Deltas*?
  // The types says MarketState is [id: string]: number. 
  // Let's return the FINAL CALCULATED SCORES.
  
  // Map graph nodes to a lookup
  const nodeBaseScores: {[key: string]: number} = {};
  graph.nodes.forEach(n => nodeBaseScores[n.id] = n.baseScore);
  
  const result: MarketState = {};
  graph.nodes.forEach(n => {
    const effect = nodeEffects[n.id] || 0;
    let score = n.baseScore + effect;
    // Clamp 0-100
    score = Math.max(0, Math.min(100, score));
    result[n.id] = score;
  });

  return result;
};
