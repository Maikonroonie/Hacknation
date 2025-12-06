import React, { useState, useEffect, useRef } from "react";
import { bfsGenerator } from "./bfsAlg";
import { layoutNodesInCircle } from "./dataUtils";
import { GraphData, BFSState } from "./types";

// Przykładowe dane - ZASTĄP JE IMPORTEM SWOJEGO PLIKU JSON
// Jeśli masz plik JSON, zaimportuj go: import rawData from '../../data/graph/prep/twoj_plik.json';
const MOCK_RAW_NODES = ["A", "B", "C", "D", "E", "F"];
const MOCK_RAW_EDGES = [
  { source: "A", target: "B" },
  { source: "A", target: "C" },
  { source: "B", target: "D" },
  { source: "C", target: "E" },
  { source: "D", target: "F" },
  { source: "E", target: "F" },
];

const BFSVisualizer = () => {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [step, setStep] = useState<BFSState | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const generatorRef = useRef<Generator<BFSState> | null>(null);
  const timerRef = useRef<any>(null);

  // 1. Ładowanie i przygotowanie danych przy starcie
  useEffect(() => {
    // Tutaj użyj swoich danych z JSON.
    // Jeśli JSON ma strukturę { nodes: [{id: '1'}], links: [...] }, musisz je tu zmapować.
    const processedGraph = layoutNodesInCircle(MOCK_RAW_NODES, MOCK_RAW_EDGES);
    setGraph(processedGraph);
  }, []);

  // 2. Obsługa animacji
  const startAnimation = () => {
    if (!graph) return;

    // Reset
    if (timerRef.current) clearInterval(timerRef.current);

    // Inicjalizacja generatora (startujemy od pierwszego węzła)
    const startNode = graph.nodes[0].id;
    generatorRef.current = bfsGenerator(graph, startNode);
    setIsRunning(true);

    // Pętla interwału
    timerRef.current = setInterval(() => {
      const next = generatorRef.current?.next();

      if (next && !next.done) {
        setStep(next.value);
      } else {
        clearInterval(timerRef.current);
        setIsRunning(false);
      }
    }, 1000); // Prędkość: 1 sekunda na krok
  };

  const stopAnimation = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setIsRunning(false);
  };

  if (!graph) return <div>Ładowanie danych...</div>;

  return (
    <div className="p-4 border rounded shadow bg-white max-w-4xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Wizualizacja BFS</h2>

      <div className="flex gap-4 mb-4">
        <button
          onClick={startAnimation}
          disabled={isRunning}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {step ? "Restart" : "Start"}
        </button>
        <button
          onClick={stopAnimation}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          Stop
        </button>
      </div>

      {/* Wyświetlanie Kolejki */}
      <div className="mb-4 p-2 bg-gray-100 rounded">
        <strong>Kolejka: </strong>
        {step?.queue.length === 0 ? (
          <span className="text-gray-500">Pusta</span>
        ) : (
          step?.queue.join(" → ")
        )}
      </div>

      {/* Wizualizacja SVG */}
      <svg width="600" height="400" className="border bg-gray-50 mx-auto block">
        {/* Krawędzie */}
        {graph.edges.map((edge, i) => {
          const s = graph.nodes.find((n) => n.id === edge.source)!;
          const t = graph.nodes.find((n) => n.id === edge.target)!;

          // Sprawdź czy krawędź jest częścią ścieżki BFS
          const isPath =
            step?.path.includes(`${edge.source}-${edge.target}`) ||
            step?.path.includes(`${edge.target}-${edge.source}`);

          return (
            <line
              key={i}
              x1={s.x}
              y1={s.y}
              x2={t.x}
              y2={t.y}
              stroke={isPath ? "#22c55e" : "#ccc"}
              strokeWidth={isPath ? 3 : 1}
            />
          );
        })}

        {/* Węzły */}
        {graph.nodes.map((node) => {
          let color = "white"; // Domyślny
          if (step?.visited.includes(node.id)) color = "#86efac"; // Odwiedzony (zielony jasny)
          if (step?.queue.includes(node.id)) color = "#93c5fd"; // W kolejce (niebieski)
          if (step?.currentNode === node.id) color = "#fbbf24"; // Aktualny (pomarańczowy)

          return (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                r={20}
                fill={color}
                stroke="black"
              />
              <text
                x={node.x}
                y={node.y}
                dy="5"
                textAnchor="middle"
                className="text-sm font-bold pointer-events-none"
              >
                {node.id}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="mt-2 text-sm text-gray-600 flex justify-center gap-4">
        <span>🟡 Aktualny</span>
        <span>🔵 W kolejce</span>
        <span>🟢 Odwiedzony</span>
      </div>
    </div>
  );
};

export default BFSVisualizer;
