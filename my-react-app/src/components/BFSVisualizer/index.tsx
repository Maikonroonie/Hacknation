import React, { useState, useEffect, useRef } from "react";
import { marketDynamicsGenerator } from "./marketAlg";
import { GraphData, MarketState } from "./types";
import rawData from "./graph_data.json"; // Zaimportuj wygenerowany plik JSON

const MarketVisualizer = () => {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [state, setState] = useState<MarketState | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const generatorRef = useRef<Generator<MarketState> | null>(null);
  const timerRef = useRef<any>(null);

  // Funkcja układająca węzły na okręgu
  const prepareGraph = (data: any): GraphData => {
    const nodesRaw = data.nodes;
    const width = 600;
    const height = 500;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 200;

    const nodes = nodesRaw.map((n: any, i: number) => {
      const angle = (i / nodesRaw.length) * 2 * Math.PI;
      return {
        id: n.id,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    return { nodes, edges: data.edges };
  };

  useEffect(() => {
    setGraph(prepareGraph(rawData));
  }, []);

  const startSimulation = (scenario: "boom" | "crash") => {
    if (!graph) return;
    if (timerRef.current) clearInterval(timerRef.current);

    // 1. Ustawienie stanu początkowego (wszyscy 50, jeden ma zmianę)
    const initialScores: Record<string, number> = {};
    graph.nodes.forEach((n) => (initialScores[n.id] = 50));

    // SCENARIUSZ: Budownictwo (41) ma Boom lub Krach
    const triggerNode = "41";
    initialScores[triggerNode] = scenario === "boom" ? 100 : 0;

    // 2. Start generatora
    generatorRef.current = marketDynamicsGenerator(graph, initialScores);
    setIsRunning(true);

    // 3. Pętla animacji
    timerRef.current = setInterval(() => {
      const next = generatorRef.current?.next();
      if (next && !next.done) {
        setState(next.value);
      } else {
        clearInterval(timerRef.current);
        setIsRunning(false);
      }
    }, 400); // Szybkość animacji (ms)
  };

  // Helper do koloru węzła (Czerwony < 50 < Zielony)
  const getNodeColor = (score: number) => {
    if (score === 50) return "#e5e7eb"; // Szary (równowaga)
    if (score > 50) {
      // Gradient do zielonego
      const intensity = (score - 50) / 50;
      return `rgba(34, 197, 94, ${0.3 + intensity * 0.7})`;
    } else {
      // Gradient do czerwonego
      const intensity = (50 - score) / 50;
      return `rgba(239, 68, 68, ${0.3 + intensity * 0.7})`;
    }
  };

  if (!graph) return <div>Ładowanie...</div>;

  return (
    <div className="p-4 bg-gray-50 min-h-screen flex flex-col items-center">
      <h1 className="text-2xl font-bold mb-4">
        Symulacja Rynku (BFS Market Dynamics)
      </h1>

      <div className="flex gap-4 mb-6">
        <button
          onClick={() => startSimulation("boom")}
          className="px-6 py-2 bg-green-600 text-white rounded shadow hover:bg-green-700"
        >
          Symuluj Hossę (Budownictwo)
        </button>
        <button
          onClick={() => startSimulation("crash")}
          className="px-6 py-2 bg-red-600 text-white rounded shadow hover:bg-red-700"
        >
          Symuluj Krach (Budownictwo)
        </button>
        <button
          onClick={() => {
            if (timerRef.current) clearInterval(timerRef.current);
            setIsRunning(false);
          }}
          className="px-4 py-2 bg-gray-400 text-white rounded hover:bg-gray-500"
        >
          Stop
        </button>
      </div>

      <div className="flex gap-8">
        {/* Wizualizacja SVG */}
        <div className="border bg-white rounded-xl shadow-lg p-4">
          <svg width="600" height="500">
            <defs>
              <marker
                id="arrow"
                markerWidth="10"
                markerHeight="10"
                refX="28"
                refY="3"
                orient="auto"
              >
                <path d="M0,0 L0,6 L9,3 z" fill="#9ca3af" />
              </marker>
            </defs>

            {/* Krawędzie */}
            {graph.edges.map((edge, i) => {
              const s = graph.nodes.find((n) => n.id === edge.source)!;
              const t = graph.nodes.find((n) => n.id === edge.target)!;
              const isActive = state?.activeEdges.includes(
                `${edge.source}-${edge.target}`
              );

              return (
                <line
                  key={i}
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke={isActive ? "#fbbf24" : "#e5e7eb"}
                  strokeWidth={isActive ? 3 : 1}
                  markerEnd="url(#arrow)"
                />
              );
            })}

            {/* Węzły */}
            {graph.nodes.map((node) => {
              const score = state?.scores[node.id] ?? 50;
              const isActive = state?.activeNode === node.id;

              return (
                <g key={node.id} className="transition-all duration-300">
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={24}
                    fill={getNodeColor(score)}
                    stroke={isActive ? "black" : "#6b7280"}
                    strokeWidth={isActive ? 3 : 1}
                  />
                  <text
                    x={node.x}
                    y={node.y}
                    dy="-5"
                    textAnchor="middle"
                    className="text-xs font-bold pointer-events-none"
                    fill="#1f2937"
                  >
                    {node.id}
                  </text>
                  <text
                    x={node.x}
                    y={node.y}
                    dy="12"
                    textAnchor="middle"
                    className="text-[10px] pointer-events-none"
                    fill="#374151"
                  >
                    {score.toFixed(0)}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Panel Boczny - Kolejka */}
        <div className="w-64">
          <h3 className="font-bold mb-2">Kolejka (Firmy do zmiany):</h3>
          <div className="bg-white border rounded p-2 h-96 overflow-y-auto shadow-inner">
            {state?.queue.map((id, idx) => (
              <div key={idx} className="p-1 mb-1 bg-blue-100 rounded text-sm">
                Branża: <strong>{id}</strong>
              </div>
            ))}
            {state?.queue.length === 0 && (
              <span className="text-gray-400 text-sm">System stabilny</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketVisualizer;
