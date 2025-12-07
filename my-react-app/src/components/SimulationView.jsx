import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
} from "recharts";
import {
  RefreshCcw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Play,
  RotateCcw,
} from "lucide-react";

const SimulationView = ({ data }) => {
  // 1. Stan aplikacji
  const pkdList = [...new Set(data.map((d) => d.PKD_Code))].sort();
  const [selectedPkd, setSelectedPkd] = useState("41"); // Domyślnie Budownictwo

  // Parametry symulacji (Zmiany wprowadzane przez użytkownika)
  const [params, setParams] = useState({
    revenue: 0, // Zmiana przychodów (%)
    liquidity: 0, // Zmiana płynności (pkt)
    employment: 0, // Zmiana zatrudnienia (%)
    wibor: 0, // Zmiana WIBOR (pp)
    energy: 0, // Zmiana cen energii (%)
    sentiment: 0, // Zmiana Google Trends (pkt)
  });

  // 2. Pobieramy historię dla wybranej branży
  const sectorData = data
    .filter((d) => d.PKD_Code === selectedPkd)
    .sort((a, b) => new Date(a.Date) - new Date(b.Date));

  const lastRecord = sectorData[sectorData.length - 1];

  // 3. SILNIK SYMULACJI (Kopia logiki z Pythona w JS)
  const calculateScore = (record, simulation) => {
    if (!record) return 0;

    // Pobieramy bazowe znormalizowane wartości
    // Musimy uwzględnić wrażliwość (Hardcoded z Pythona)
    const riskMap = {
      41: { w: 1.0, e: 0.3 }, // Budownictwo
      68: { w: 1.0, e: 0.2 }, // Nieruchomości
      49: { w: 0.5, e: 0.9 }, // Transport
      35: { w: 0.3, e: -0.5 }, // Energetyka
      10: { w: 0.4, e: 0.6 }, // Spożywka
      24: { w: 0.4, e: 1.0 }, // Metale
      62: { w: 0.1, e: 0.1 }, // IT
      default: { w: 0.5, e: 0.5 },
    };
    const sens = riskMap[record.PKD_Code] || riskMap["default"];

    // --- APLIKUJEMY ZMIANY ---
    // Przyjmujemy uproszczony przelicznik: 1% zmiany realnej = ~1-2 pkt w skali 0-100

    // Pozytywy
    let growthScore = Math.min(
      100,
      Math.max(0, record.Norm_Growth + simulation.revenue * 1.5)
    );
    let liqScore = Math.min(
      100,
      Math.max(0, record.Norm_Liquidity + simulation.liquidity * 2)
    );
    let emplScore = Math.min(
      100,
      Math.max(0, record.Norm_Employ + simulation.employment * 1.5)
    );
    let googleScore = Math.min(
      100,
      Math.max(0, record.Norm_Google + simulation.sentiment)
    );

    // Negatywy (Ryzyko)
    // WIBOR i Energia: Zmiana * Wrażliwość * Mnożnik wpływu
    // Pamiętaj: W Pythonie liczyliśmy (100 - Ryzyko). Tutaj liczymy ile punktów TRACIMY.
    let baseRisk = record.Norm_Total_Risk || 50;
    let addedRisk =
      simulation.wibor * 5 * sens.w + simulation.energy * 0.2 * sens.e;
    let riskScore = Math.min(100, Math.max(0, baseRisk + addedRisk));

    // WZÓR FINALNY (Wagi z Pythona V7.0)
    // (0.15*Margin) + (0.15*Growth) + (0.10*Liq) + (0.10*Empl) + (0.20*Google)
    // + (0.15*(100-Risk)) + (0.15*(100-Bankrupt))

    let final =
      0.15 * record.Norm_Margin +
      0.15 * growthScore +
      0.1 * liqScore +
      0.1 * emplScore +
      0.2 * googleScore +
      0.15 * (100 - riskScore) +
      0.15 * (100 - record.Norm_Bankrupt);

    return Math.max(0, Math.min(100, final));
  };

  const currentScore = lastRecord ? lastRecord.PKO_SCORE_FINAL : 0;
  const simScore = calculateScore(lastRecord, params);
  const diff = simScore - currentScore;

  // Reset function
  const resetParams = () =>
    setParams({
      revenue: 0,
      liquidity: 0,
      employment: 0,
      wibor: 0,
      energy: 0,
      sentiment: 0,
    });

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 p-6">
      {/* 1. PANEL KONTROLNY (Lewa kolumna) */}
      <div className="xl:col-span-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col h-full">
        <div className="mb-6 pb-6 border-b border-slate-100">
          <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
            Wybierz Sektor
          </label>
          <select
            value={selectedPkd}
            onChange={(e) => {
              setSelectedPkd(e.target.value);
              resetParams();
            }}
            className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-lg font-bold text-[#002D72] focus:ring-2 focus:ring-blue-500 outline-none"
          >
            {pkdList.map((pkd) => (
              <option key={pkd} value={pkd}>
                PKD {pkd}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-6 flex-1 overflow-y-auto pr-2">
          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            <RefreshCcw size={18} className="text-blue-600" /> Parametry
            Symulacji
          </h3>

          <Slider
            label="Dynamika Przychodów"
            val={params.revenue}
            set={(v) => setParams({ ...params, revenue: v })}
            min={-20}
            max={20}
            unit="%"
            color="green"
          />
          <Slider
            label="Płynność Finansowa"
            val={params.liquidity}
            set={(v) => setParams({ ...params, liquidity: v })}
            min={-20}
            max={20}
            unit="pkt"
            color="emerald"
          />
          <Slider
            label="Zatrudnienie"
            val={params.employment}
            set={(v) => setParams({ ...params, employment: v })}
            min={-10}
            max={10}
            unit="%"
            color="teal"
          />

          <div className="h-px bg-slate-100 my-4"></div>

          <Slider
            label="Stopy % (WIBOR)"
            val={params.wibor}
            set={(v) => setParams({ ...params, wibor: v })}
            min={-5}
            max={5}
            step={0.25}
            unit="pp"
            color="rose"
            desc="Wrażliwość sektora uwzględniona automatycznie."
          />
          <Slider
            label="Ceny Energii"
            val={params.energy}
            set={(v) => setParams({ ...params, energy: v })}
            min={-50}
            max={50}
            unit="%"
            color="orange"
          />
          <Slider
            label="Sentyment Google"
            val={params.sentiment}
            set={(v) => setParams({ ...params, sentiment: v })}
            min={-30}
            max={30}
            unit="pkt"
            color="blue"
          />
        </div>

        <button
          onClick={resetParams}
          className="mt-6 flex items-center justify-center gap-2 w-full py-3 bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold rounded-lg transition-colors"
        >
          <RotateCcw size={18} /> Resetuj Ustawienia
        </button>
      </div>

      {/* 2. DASHBOARD WYNIKÓW (Prawa kolumna) */}
      <div className="xl:col-span-8 flex flex-col gap-6">
        {/* KAFELKI WYNIKU */}
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Play size={100} />
            </div>
            <div className="text-sm font-bold text-slate-400 uppercase">
              Obecny Score
            </div>
            <div className="text-5xl font-black text-slate-800 mt-2">
              {currentScore.toFixed(1)}
            </div>
            <div className="text-sm text-slate-500 mt-2 font-medium">
              Stan na podstawie twardych danych
            </div>
          </div>

          <div
            className={`p-6 rounded-2xl border-2 shadow-sm relative overflow-hidden transition-all duration-300 ${
              diff >= 0
                ? "bg-green-50 border-green-200"
                : "bg-red-50 border-red-200"
            }`}
          >
            <div className="text-sm font-bold text-slate-500 uppercase">
              Symulacja
            </div>
            <div className="flex items-baseline gap-4 mt-2">
              <div
                className={`text-5xl font-black ${
                  diff >= 0 ? "text-green-700" : "text-red-700"
                }`}
              >
                {simScore.toFixed(1)}
              </div>
              <div
                className={`text-xl font-bold flex items-center ${
                  diff >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {diff > 0 ? "+" : ""}
                {diff.toFixed(1)}
                {diff >= 0 ? (
                  <TrendingUp size={24} className="ml-1" />
                ) : (
                  <TrendingDown size={24} className="ml-1" />
                )}
              </div>
            </div>
            <div className="text-sm text-slate-600 mt-2 font-medium">
              Prognozowany wynik po zmianach
            </div>
          </div>
        </div>

        {/* WYKRES SCENARIUSZOWY */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex-1 min-h-[400px]">
          <h3 className="font-bold text-lg text-[#002D72] mb-6">
            Projekcja Wpływu na Trend
          </h3>
          <ResponsiveContainer width="100%" height="85%">
            <AreaChart data={sectorData.slice(-12)}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#002D72" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#002D72" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="#e2e8f0"
              />
              <XAxis
                dataKey="Date"
                tickFormatter={(d) => d.substring(0, 7)}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#64748b" }}
                dy={10}
              />
              <YAxis domain={[0, 100]} hide />
              <Tooltip
                contentStyle={{
                  borderRadius: "8px",
                  border: "none",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                }}
                labelFormatter={(l) => l.substring(0, 10)}
              />
              <ReferenceLine
                y={currentScore}
                stroke="#94a3b8"
                strokeDasharray="3 3"
                label={{ value: "Obecny", fill: "#94a3b8", fontSize: 12 }}
              />
              <ReferenceLine
                y={simScore}
                stroke={diff >= 0 ? "#22c55e" : "#ef4444"}
                strokeWidth={2}
                label={{
                  value: "Symulacja",
                  fill: diff >= 0 ? "#16a34a" : "#dc2626",
                  fontSize: 12,
                  fontWeight: "bold",
                }}
              />

              <Area
                type="monotone"
                dataKey="PKO_SCORE_FINAL"
                stroke="#002D72"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorScore)"
                name="Historia"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* AI INSIGHT */}
        <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 flex gap-4 items-start">
          <AlertTriangle className="text-blue-600 mt-1 flex-shrink-0" />
          <div>
            <h4 className="font-bold text-blue-900 text-sm uppercase">
              Wniosek Modelu Wrażliwości
            </h4>
            <p className="text-sm text-blue-800 mt-1 leading-relaxed">
              {diff < -5
                ? "Zmiana parametrów drastycznie obniża zdolność kredytową sektora. Szczególnie wysoka wrażliwość na koszty (WIBOR/Energia). Zalecany monitoring."
                : diff > 5
                ? "Poprawa warunków makroekonomicznych może uczynić ten sektor liderem wzrostu w portfelu banku."
                : "Sektor wykazuje wysoką odporność (Resilience) na wprowadzone zmiany parametrów. Stabilny kandydat do finansowania."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const Slider = ({ label, val, set, min, max, step = 1, unit, color, desc }) => (
  <div>
    <div className="flex justify-between mb-1 items-end">
      <label className="font-bold text-xs text-slate-500 uppercase">
        {label}
      </label>
      <span
        className={`font-mono text-sm font-bold text-${color}-600 bg-${color}-50 px-2 py-0.5 rounded`}
      >
        {val > 0 ? "+" : ""}
        {val} {unit}
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={val}
      onChange={(e) => set(parseFloat(e.target.value))}
      className={`w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-${color}-600 hover:accent-${color}-500 transition-all`}
    />
    {desc && (
      <p className="text-[10px] text-slate-400 mt-1 leading-tight">{desc}</p>
    )}
  </div>
);

export default SimulationView;
