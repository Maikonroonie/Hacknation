
import React, { useState, useEffect, useMemo, useRef } from 'react';
import graphDataRaw from './graph_data.json';
import { GraphData, Node, MarketState } from './types';
import { calculateMarketState } from './marketAlg';

// Styles for the container and layout
const styles = {
  container: {
    display: 'flex',
    height: '100vh',
    width: '100%',
    fontFamily: 'sans-serif',
    overflow: 'hidden',
    backgroundColor: '#1a1a1a',
    color: '#eee'
  },
  sidebar: {
    width: '300px',
    padding: '20px',
    backgroundColor: '#252525',
    borderRight: '1px solid #333',
    overflowY: 'auto' as const,
    boxShadow: '2px 0 5px rgba(0,0,0,0.3)'
  },
  main: {
    flex: 1,
    position: 'relative' as const,
    overflow: 'hidden'
  },
  controlGroup: {
    marginBottom: '15px',
    padding: '10px',
    backgroundColor: '#333',
    borderRadius: '8px'
  },
  label: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '5px',
    fontSize: '0.9rem'
  },
  slider: {
    width: '100%',
    cursor: 'pointer'
  }
};

const MarketVisualizer: React.FC = () => {
  // State
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [userDeltas, setUserDeltas] = useState<MarketState>({});
  const [calculatedState, setCalculatedState] = useState<MarketState>({});
  
  // Dragging state
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Initialize Data
  useEffect(() => {
    // Load initial data
    // Cast strict type if needed, or rely on inference
    const data = graphDataRaw as unknown as GraphData;
    setGraphData(data);
    
    // Initial calculation (deltas 0)
    const initialState = calculateMarketState(data, {});
    setCalculatedState(initialState);
  }, []);

  // Update calculation when deltas change
  useEffect(() => {
    const newState = calculateMarketState(graphData, userDeltas);
    setCalculatedState(newState);
  }, [userDeltas, graphData]);

  // Handlers
  const handleSliderChange = (nodeId: string, val: string) => {
    const delta = parseFloat(val);
    setUserDeltas(prev => ({
      ...prev,
      [nodeId]: delta
    }));
  };

  const getColor = (score: number) => {
    // 0 -> Red (255, 0, 0)
    // 50 -> Yellow (255, 255, 0)
    // 100 -> Green (0, 255, 0)
    const clamped = Math.max(0, Math.min(100, score));
    if (clamped < 50) {
      // Red to Yellow
      const r = 255;
      const g = Math.round((clamped / 50) * 255);
      return `rgb(${r}, ${g}, 0)`;
    } else {
      // Yellow to Green
      const r = Math.round(255 - ((clamped - 50) / 50) * 255);
      const g = 255;
      return `rgb(${r}, ${g}, 0)`;
    }
  };

  // Drag Logic
  const handleMouseDown = (e: React.MouseEvent, nodeId: string) => {
    e.preventDefault();
    setDraggingNodeId(nodeId);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggingNodeId) return;
    if (!svgRef.current) return;

    const CTM = svgRef.current.getScreenCTM();
    if (!CTM) return;

    // Calculate SVG coordinates
    const x = (e.clientX - CTM.e) / CTM.a;
    const y = (e.clientY - CTM.f) / CTM.d;

    setGraphData(prev => ({
      ...prev,
      nodes: prev.nodes.map(n => n.id === draggingNodeId ? { ...n, x, y } : n)
    }));
  };

  const handleMouseUp = () => {
    setDraggingNodeId(null);
  };

  // Render
  return (
    <div style={styles.container}>
      {/* Sidebar */}
      <div style={styles.sidebar}>
        <h3>Market Simulator</h3>
        <p style={{ fontSize: '0.8rem', color: '#aaa' }}>Adjust sliders to add shocks (+/-)</p>
        
        {graphData.nodes.map(node => {
            const currentDelta = userDeltas[node.id] || 0;
            const currentScore = calculatedState[node.id] ?? node.baseScore;
            
            return (
              <div key={node.id} style={styles.controlGroup}>
                <div style={styles.label}>
                  <span style={{ fontWeight: 'bold' }}>{node.label}</span>
                  <span style={{ color: getColor(currentScore) }}>
                    {currentScore.toFixed(1)}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.8rem' }}>
                  <span>Shock:</span>
                  <input
                    type="range"
                    min="-50"
                    max="50"
                    value={currentDelta}
                    onChange={(e) => handleSliderChange(node.id, e.target.value)}
                    style={styles.slider}
                  />
                  <span>{currentDelta > 0 ? '+' : ''}{currentDelta}</span>
                </div>
              </div>
            );
        })}
      </div>

      {/* Main Graph Area */}
      <div 
        style={styles.main} 
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg 
            ref={svgRef}
            width="100%" 
            height="100%" 
            style={{ backgroundColor: '#111', cursor: draggingNodeId ? 'grabbing' : 'default' }}
        >
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#555" />
            </marker>
          </defs>

          {/* Edges */}
          {graphData.edges.map((edge, idx) => {
            const sourceNode = graphData.nodes.find(n => n.id === edge.source);
            const targetNode = graphData.nodes.find(n => n.id === edge.target);
            
            if (!sourceNode || !targetNode) return null;
            
            // Safety check for coords
            const x1 = sourceNode.x || 0; 
            const y1 = sourceNode.y || 0;
            const x2 = targetNode.x || 0;
            const y2 = targetNode.y || 0;

            const strokeWidth = 1 + edge.weight * 5; // Thickness based on weight

            return (
              <line 
                key={`${edge.source}-${edge.target}-${idx}`}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#555"
                strokeWidth={strokeWidth}
                markerEnd="url(#arrowhead)"
                opacity={0.6}
              />
            );
          })}

          {/* Nodes */}
          {graphData.nodes.map(node => {
            const score = calculatedState[node.id] ?? node.baseScore;
            const fill = getColor(score);
            const x = node.x || 50;
            const y = node.y || 50;
            
            return (
              <g 
                key={node.id} 
                transform={`translate(${x}, ${y})`}
                onMouseDown={(e) => handleMouseDown(e, node.id)}
                style={{ cursor: 'grab' }}
              >
                <circle 
                  r="20" 
                  fill={fill} 
                  stroke="#fff" 
                  strokeWidth="2" 
                />
                <text 
                  y="-30" 
                  fill="#fff" 
                  textAnchor="middle" 
                  fontSize="12"
                  style={{ pointerEvents: 'none', textShadow: '0 1px 2px #000' }}
                >
                  {node.label}
                </text>
                <text 
                  y="5" 
                  fill="#000" 
                  textAnchor="middle" 
                  fontSize="10" 
                  fontWeight="bold"
                  style={{ pointerEvents: 'none' }}
                >
                  {Math.round(score)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

export default MarketVisualizer;
