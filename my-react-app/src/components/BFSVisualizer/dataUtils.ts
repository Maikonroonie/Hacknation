import { GraphData } from "./types";

// Funkcja, która dodaje współrzędne X, Y do surowych danych
export const layoutNodesInCircle = (
  nodesList: string[],
  edgesList: { source: string; target: string }[]
): GraphData => {
  const width = 600;
  const height = 400;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 2 - 40;

  const nodes = nodesList.map((id, index) => {
    const angle = (index / nodesList.length) * 2 * Math.PI;
    return {
      id,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  return { nodes, edges: edgesList };
};
