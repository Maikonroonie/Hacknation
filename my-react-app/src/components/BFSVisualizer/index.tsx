
import React, { useState, useEffect, useRef } from 'react';
import graphDataRaw from './graph_data.json';
import { GraphData, AnimationStep } from './types';
import { generateBFSSteps } from './marketAlg';

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
    width: '320px',
    padding: '20px',
    backgroundColor: '#252525',
    borderRight: '1px solid #333',
    overflowY: 'auto' as const,
    boxShadow: '2px 0 5px rgba(0,0,0,0.3)',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '15px'
  },
  main: {
    flex: 1,
    position: 'relative' as const,
    overflow: 'hidden'
  },
  controlGroup: {
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
  },
  buttonRow: {
    display: 'flex',
    gap: '10px',
    marginBottom: '10px'
  },
  button: {
    flex: 1,
    padding: '8px',
    backgroundColor: '#4a4a4a',
    border: 'none',
    borderRadius: '4px',
    color: 'white',
    cursor: 'pointer',
    fontWeight: 'bold' as const
  },
  activeButton: {
    backgroundColor: '#007bff'
  }
};

const MarketVisualizer: React.FC = () => {
  // Graph Data
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  
  // Simulation State
  const [animationSteps, setAnimationSteps] = useState<AnimationStep[]>([]);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(500); // ms per step
  
  // Viewport State (Zoom/Pan)
  const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 1 });
  const [isPanning, setIsPanning] = useState(false);
  const [lastPanPoint, setLastPanPoint] = useState({ x: 0, y: 0 });

  // Dragging state
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Initialize Data
  useEffect(() => {
    const data = graphDataRaw as unknown as GraphData;
    setGraphData(data);
    
    // Calculate steps based on Graph Data inherent attributes
    const steps = generateBFSSteps(data);
    setAnimationSteps(steps);
  }, []);

  // Animation Loop
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentStep(prev => {
          if (prev < animationSteps.length - 1) {
            return prev + 1;
          } else {
            setIsPlaying(false); // Stop at end
            return prev;
          }
        });
      }, speed);
    }
    return () => clearInterval(interval);
  }, [isPlaying, animationSteps, speed]);

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
  };

  const handleStep = (direction: 'next' | 'prev') => {
      setIsPlaying(false);
      setCurrentStep(prev => {
          if (direction === 'next') return Math.min(animationSteps.length - 1, prev + 1);
          return Math.max(0, prev - 1);
      });
  };

  const getColor = (score: number) => {
    const clamped = Math.max(0, Math.min(100, score));
    if (clamped < 50) {
      const g = Math.round((clamped / 50) * 255);
      return `rgb(255, ${g}, 0)`;
    } else {
      const r = Math.round(255 - ((clamped - 50) / 50) * 255);
      return `rgb(${r}, 255, 0)`;
    }
  };

  // Interaction Logic
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault(); // Stop page scroll
    const scaleFactor = 1.05;
    const direction = e.deltaY > 0 ? -1 : 1;
    const newZoom = direction > 0 ? viewport.zoom * scaleFactor : viewport.zoom / scaleFactor;
    
    // Clamp zoom
    if (newZoom < 0.1 || newZoom > 5) return;

    setViewport(prev => ({ ...prev, zoom: newZoom }));
  };

  const handleMouseDown = (e: React.MouseEvent, nodeId?: string) => {
    e.preventDefault();
    if (nodeId) {
       setDraggingNodeId(nodeId);
    } else {
       setIsPanning(true);
       setLastPanPoint({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
        const dx = e.clientX - lastPanPoint.x;
        const dy = e.clientY - lastPanPoint.y;
        setViewport(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
        setLastPanPoint({ x: e.clientX, y: e.clientY });
        return;
    }

    if (!draggingNodeId || !svgRef.current) return;

    // Convert screen coordinates to SVG coordinates, accounting for zoom/pan
    const svgRect = svgRef.current.getBoundingClientRect();
    const x = (e.clientX - svgRect.left - viewport.x) / viewport.zoom;
    const y = (e.clientY - svgRect.top - viewport.y) / viewport.zoom;

    setGraphData(prev => ({
      ...prev,
      nodes: prev.nodes.map(n => n.id === draggingNodeId ? { ...n, x, y } : n)
    }));
  };
  const handleMouseUp = () => {
    setDraggingNodeId(null);
    setIsPanning(false);
  };
  
  // Derived State for Render
  const activeStepData = animationSteps[currentStep] || { 
     activeNodeIds: [], 
     activeEdgeIds: [], 
     currentScores: {} 
  };
  
  const scores = activeStepData.currentScores;

  return (
    <div style={styles.container}>
      {/* Sidebar - Graphite Style */}
      <div style={{...styles.sidebar, backgroundColor: '#1e1e1e', borderRight: '1px solid #000'}}>
        <div style={{ borderBottom: '1px solid #333', paddingBottom: '10px' }}>
          <p style={{ fontSize: '0.9rem', color: '#fff', fontWeight: 'bold', margin: 0 }}>
             Market Visualizer
          </p>
          <p style={{ fontSize: '0.75rem', color: '#888', margin: '5px 0' }}>
            Systemic Risk • {graphData.nodes.length} Nodes • {graphData.edges.length} Edges
          </p>
        </div>

        <div style={{...styles.controlGroup, backgroundColor: '#2a2a2a'}}>
           <div style={styles.buttonRow}>
             <button 
               style={{...styles.button, backgroundColor: isPlaying ? '#ff5555' : '#00adb5'}}
               onClick={() => setIsPlaying(!isPlaying)}
             >
               {isPlaying ? 'PAUSE' : 'PLAY'}
             </button>
             <button style={{...styles.button, backgroundColor: '#444'}} onClick={handleReset}>
               RESET
             </button>
           </div>

           <div style={{display: 'flex', gap: '5px', marginBottom: '10px'}}>
             <button style={{...styles.button, fontSize: '0.8rem'}} onClick={() => handleStep('prev')}>{'< Step'}</button>
             <button style={{...styles.button, fontSize: '0.8rem'}} onClick={() => handleStep('next')}>{'Step >'}</button>
           </div>
           
           <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#fff', marginBottom: '5px'}}>
             <span>Timeline: {currentStep}</span>
             <span>Speed: {speed}ms</span>
           </div>
           
           <input 
             type="range" 
             min="0" 
             max={Math.max(0, animationSteps.length - 1)} 
             value={currentStep}
             onChange={(e) => {
               setIsPlaying(false);
               setCurrentStep(parseInt(e.target.value));
             }}
             style={{width: '100%', accentColor: '#00adb5'}}
           />
           
           <div style={{marginTop: '10px', display: 'flex', alignItems: 'center', gap: '10px'}}>
               <span style={{fontSize: '0.7rem'}}>Speed:</span>
               <input 
                 type="range" 
                 min="50" 
                 max="1000" 
                 step="50"
                 value={1050 - speed} 
                 onChange={(e) => setSpeed(1050 - parseInt(e.target.value))}
                 style={{flex: 1, height: '4px'}}
               />
           </div>
        </div>
        
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {graphData.nodes.map(node => {
              const currentScore = scores[node.id] ?? node.baseScore;
              const isActive = activeStepData.activeNodeIds.includes(node.id);
              
              return (
                <div key={node.id} style={{
                    padding: '8px', 
                    marginBottom: '5px', 
                    backgroundColor: isActive ? '#333' : 'transparent',
                    borderLeft: isActive ? '3px solid #00adb5' : '3px solid transparent',
                    borderRadius: '2px',
                    transition: 'background 0.3s'
                }}>
                  <div style={styles.label}>
                    <span style={{ fontWeight: 'bold', fontSize: '0.85rem' }}>{node.label}</span>
                    <span style={{ color: getColor(currentScore), fontWeight: 'bold', fontSize: '0.85rem' }}>
                       {currentScore.toFixed(1)}
                    </span>
                  </div>
                  {/* Mini Bar */}
                  <div style={{height: '3px', backgroundColor: '#333', borderRadius: '1px', marginTop: '3px'}}>
                      <div style={{
                          width: `${Math.min(100, Math.max(0, currentScore))}%`, 
                          height: '100%', 
                          backgroundColor: getColor(currentScore),
                          transition: 'width 0.3s'
                      }} />
                  </div>
                </div>
              );
          })}
        </div>
      </div>

      {/* Main Graph Area */}
      <div 
        style={{...styles.main, backgroundColor: '#0f0f0f', overflow: 'hidden'}}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onMouseDown={(e) => handleMouseDown(e)} // Background pan
        onWheel={handleWheel}
      >
        <svg 
            ref={svgRef}
            width="100%" 
            height="100%" 
            style={{ cursor: isPanning ? 'grabbing' : (draggingNodeId ? 'grabbing' : 'default') }}
        >
          <defs>
            {/* Subtle Arrowhead */}
            <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="22" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6" fill="#444" />
            </marker>
            {/* Active Arrowhead */}
            <marker id="arrowhead-active" markerWidth="6" markerHeight="6" refX="22" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6" fill="#00adb5" />
            </marker>
          </defs>
            
          {/* Zoom/Pan Group */}
          <g transform={`translate(${viewport.x}, ${viewport.y}) scale(${viewport.zoom})`}>

          {/* Grid Background Pattern */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#222" strokeWidth="1"/>
          </pattern>
          <rect x="-5000" y="-5000" width="10000" height="10000" fill="url(#grid)" />

          {/* Edges */}
          {graphData.edges.map((edge, idx) => {
            const sourceNode = graphData.nodes.find(n => n.id === edge.source);
            const targetNode = graphData.nodes.find(n => n.id === edge.target);
            
            if (!sourceNode || !targetNode) return null;
            
            const edgeKey = `${edge.source}-${edge.target}`;
            const isActive = activeStepData.activeEdgeIds.includes(edgeKey);

            const x1 = sourceNode.x || 0; 
            const y1 = sourceNode.y || 0;
            const x2 = targetNode.x || 0;
            const y2 = targetNode.y || 0;

            const strokeWidth = isActive ? 2 : 1;
            const strokeColor = isActive ? '#00adb5' : '#333'; 
            const opacity = isActive ? 1 : 0.6;
            const marker = isActive ? "url(#arrowhead-active)" : "url(#arrowhead)";
            
            // Midpoint for text
            const midX = (x1 + x2) / 2;
            const midY = (y1 + y2) / 2;

            return (
              <g key={`${edgeKey}-${idx}`}>
                <line 
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  markerEnd={marker}
                  opacity={opacity}
                  style={{ transition: 'stroke 0.3s, stroke-width 0.3s' }}
                />
                
                {/* Edge Weight Label */}
                {edge.weight > 0.01 && (
                    <g transform={`translate(${midX}, ${midY})`}>
                       <rect x="-10" y="-7" width="20" height="14" fill="#0f0f0f" opacity="0.9" rx="2" />
                       <text 
                         textAnchor="middle" 
                         dy="3" 
                         fill="#555" 
                         fontSize="8"
                         fontFamily="monospace"
                         pointerEvents="none"
                       >
                         {edge.weight.toFixed(2)}
                       </text>
                    </g>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {graphData.nodes.map(node => {
            const score = scores[node.id] ?? node.baseScore;
            // Use score color for STROKE
            const color = getColor(score);
            const x = node.x || 50;
            const y = node.y || 50;
            
            const isActive = activeStepData.activeNodeIds.includes(node.id);
            
            return (
              <g 
                key={node.id} 
                transform={`translate(${x}, ${y})`}
                onMouseDown={(e) => { e.stopPropagation(); handleMouseDown(e, node.id); }}
                style={{ cursor: 'grab', transition: 'transform 0.1s' }}
              >
                {/* Halo for active nodes */}
                {isActive && (
                   <circle r="25" fill="none" stroke="#00adb5" strokeWidth="1" opacity="0.6">
                     <animate attributeName="r" from="18" to="30" dur="1.5s" repeatCount="indefinite" />
                     <animate attributeName="opacity" from="0.6" to="0" dur="1.5s" repeatCount="indefinite" />
                   </circle>
                )}
                
                {/* Node Body */}
                <circle 
                  r="18" 
                  fill="#1a1a1a"
                  stroke={color} 
                  strokeWidth="3"
                />
                
                {/* Score in center */}
                <text 
                  dy="4"
                  fill={color} 
                  textAnchor="middle" 
                  fontSize="10" 
                  fontWeight="bold"
                  fontFamily="monospace"
                  style={{ pointerEvents: 'none' }}
                >
                  {Math.round(score)}
                </text>

                {/* Label below */}
                <text 
                  y="30" 
                  fill="#aaa" 
                  textAnchor="middle" 
                  fontSize="10"
                  fontFamily="sans-serif"
                  style={{ pointerEvents: 'none', textShadow: '0 2px 2px #000' }}
                >
                  {node.label}
                </text>
              </g>
            );
          })}
          
          </g>
        </svg>
      </div>
    </div>
  );
};

export default MarketVisualizer;
