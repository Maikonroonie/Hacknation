import { useState, useMemo, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  SlidersHorizontal,
  RotateCcw,
  Calendar,
  TrendingUp,
  TrendingDown,
  Play,
} from "lucide-react";

export interface DataRecord {
  Date: string;
  PKD_Code: string;
  PKO_SCORE_FINAL: number;
  Norm_Growth: number;
  Norm_Liquidity: number;
  Norm_Employ: number;
  Norm_Google: number;
  Norm_Margin: number;
  Norm_Total_Risk: number;
  Norm_Bankrupt: number;
}

// Typ dla stanu parametrów
interface SimulationParams {
  revenue: number;
  liquidity: number;
  employment: number;
  wibor: number;
  energy: number;
  sentiment: number;
}

interface SliderProps {
  label: string;
  val: number;
  set: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  unit: string;
  isRisk?: boolean;
  color?: string;
}

const INDUSTRY_NAMES: Record<string, string> = {
  "01": "Rolnictwo",
  "10": "Prod. Żywności",
  "16": "Prod. Drewna",
  "23": "Minerały",
  "24": "Metale",
  "29": "Motoryzacja",
  "31": "Meble",
  "35": "Energetyka",
  "41": "Budownictwo",
  "46": "Hurt",
  "47": "Detal",
  "49": "Transport",
  "55": "HoReCa",
  "62": "IT / Tech",
  "68": "Nieruchomości",
};

const SimulationView = ({ data }: { data: DataRecord[] }) => {
  const pkdList = useMemo(
    () => Array.from(new Set(data.map((d) => d.PKD_Code))).sort(),
    [data]
  );
  const [selectedPkd, setSelectedPkd] = useState<string>("");

  useEffect(() => {
    if (pkdList.length > 0 && !selectedPkd) {
      setSelectedPkd(pkdList.includes("41") ? "41" : pkdList[0]);
    }
  }, [pkdList, selectedPkd]);

  const sectorData = useMemo(() => {
    if (!selectedPkd) return [];
    return data
      .filter((d) => d.PKD_Code === selectedPkd)
      .sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime());
  }, [data, selectedPkd]);

  const [dateIndex, setDateIndex] = useState(0);

  useEffect(() => {
    if (sectorData.length > 0) setDateIndex(sectorData.length - 1);
  }, [sectorData.length]);

  const currentRecord = sectorData[dateIndex];

  // Inicjalizacja stanu z typem
  const [params, setParams] = useState<SimulationParams>({
    revenue: 0,
    liquidity: 0,
    employment: 0,
    wibor: 0,
    energy: 0,
    sentiment: 0,
  });

  const resetParams = () =>
    setParams({
      revenue: 0,
      liquidity: 0,
      employment: 0,
      wibor: 0,
      energy: 0,
      sentiment: 0,
    });

  // --- MATEMATYKA ---
  // Obliczamy score bazując na aktualnych wartościach + parametrach symulacji
  const { simScore, diff, realScore } = useMemo(() => {
    if (!currentRecord) return { simScore: 0, diff: 0, realScore: 0 };

    const riskMap: any = {
      "41": { w: 1.0, e: 0.3 },
      "68": { w: 1.0, e: 0.2 },
      "49": { w: 0.5, e: 0.9 },
      "35": { w: 0.3, e: -0.5 },
      "10": { w: 0.4, e: 0.6 },
      "24": { w: 0.4, e: 1.0 },
      "62": { w: 0.1, e: 0.1 },
      default: { w: 0.5, e: 0.5 },
    };
    const sens = riskMap[currentRecord.PKD_Code] || riskMap["default"];

    // Bazowe wartości
    const baseGrowth = currentRecord.Norm_Growth;
    const baseLiq = currentRecord.Norm_Liquidity;
    const baseEmpl = currentRecord.Norm_Employ;
    const baseGoogle = currentRecord.Norm_Google;
    const baseRisk = currentRecord.Norm_Total_Risk;

    // Wartości po symulacji
    const newGrowth = Math.max(
      0,
      Math.min(100, baseGrowth + params.revenue * 1.5)
    );
    const newLiq = Math.max(0, Math.min(100, baseLiq + params.liquidity * 2));
    const newEmpl = Math.max(
      0,
      Math.min(100, baseEmpl + params.employment * 1.5)
    );
    const newGoogle = Math.max(0, Math.min(100, baseGoogle + params.sentiment));

    const addedRisk = params.wibor * 5 * sens.w + params.energy * 0.2 * sens.e;
    const newRisk = Math.max(0, Math.min(100, baseRisk + addedRisk));

    // Score bazowy
    const baseScore =
      0.15 * currentRecord.Norm_Margin +
      0.15 * baseGrowth +
      0.1 * baseLiq +
      0.1 * baseEmpl +
      0.2 * baseGoogle +
      0.15 * (100 - baseRisk) +
      0.15 * (100 - currentRecord.Norm_Bankrupt);

    // Score po symulacji
    const simScoreCalc =
      0.15 * currentRecord.Norm_Margin +
      0.15 * newGrowth +
      0.1 * newLiq +
      0.1 * newEmpl +
      0.2 * newGoogle +
      0.15 * (100 - newRisk) +
      0.15 * (100 - currentRecord.Norm_Bankrupt);

    const difference = simScoreCalc - baseScore;
    const realScoreValue = currentRecord.PKO_SCORE_FINAL;
    const finalSimScore = Math.max(
      0,
      Math.min(100, realScoreValue + difference)
    );

    // DEBUG
    console.log(" DEBUG Symulacji:", {
      PKD: currentRecord.PKD_Code,
      params,
      baseLiq,
      newLiq,
      baseScore: baseScore.toFixed(2),
      simScoreCalc: simScoreCalc.toFixed(2),
      difference: difference.toFixed(2),
      realScore: realScoreValue.toFixed(2),
      finalSimScore: finalSimScore.toFixed(2),
    });

    return {
      simScore: finalSimScore,
      diff: difference,
      realScore: realScoreValue,
    };
  }, [currentRecord, params]);

  const chartData = [
    {
      name: "Faktyczny",
      score: parseFloat(realScore.toFixed(1)),
      fill: "#94a3b8",
    },
    {
      name: "Symulacja",
      score: parseFloat(simScore.toFixed(1)),
      fill: diff >= 0 ? "#10b981" : "#f43f5e",
    },
  ];

  if (!currentRecord)
    return (
      <div className="p-10 text-center text-slate-400">Ładowanie danych...</div>
    );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pb-10">
      {/* LEWY PANEL */}
      <div className="lg:col-span-4 space-y-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Wybierz Sektor
          </label>
          <select
            value={selectedPkd}
            onChange={(e) => {
              setSelectedPkd(e.target.value);
              resetParams();
            }}
            className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-medium focus:ring-2 focus:ring-[#002D72] outline-none"
          >
            {pkdList.map((pkd) => (
              <option key={pkd} value={pkd}>
                PKD {pkd}{" "}
                {INDUSTRY_NAMES[pkd] ? `- ${INDUSTRY_NAMES[pkd]}` : ""}
              </option>
            ))}
          </select>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-slate-800 flex gap-2 items-center">
              <SlidersHorizontal size={18} /> Parametry
            </h3>
            <button
              onClick={resetParams}
              className="text-xs text-slate-400 hover:text-[#D31145] flex items-center gap-1 transition-colors"
            >
              <RotateCcw size={12} /> Reset
            </button>
          </div>
          <div className="space-y-6">
            <Slider
              label="Dynamika Przychodów"
              val={params.revenue}
              set={(v: number) => setParams({ ...params, revenue: v })}
              min={-20}
              max={20}
              unit="%"
              color="green"
            />
            <Slider
              label="Płynność Finansowa"
              val={params.liquidity}
              set={(v: number) => setParams({ ...params, liquidity: v })}
              min={-20}
              max={20}
              unit="pkt"
              color="emerald"
            />
            <Slider
              label="Zatrudnienie"
              val={params.employment}
              set={(v: number) => setParams({ ...params, employment: v })}
              min={-10}
              max={10}
              unit="%"
              color="teal"
            />
            <hr className="border-slate-100" />
            <Slider
              label="Stopy % (WIBOR)"
              val={params.wibor}
              set={(v: number) => setParams({ ...params, wibor: v })}
              min={-5}
              max={5}
              step={0.25}
              unit="pp"
              isRisk
              color="rose"
            />
            <Slider
              label="Ceny Energii"
              val={params.energy}
              set={(v: number) => setParams({ ...params, energy: v })}
              min={-50}
              max={50}
              unit="%"
              isRisk
              color="orange"
            />
            <Slider
              label="Sentyment Google"
              val={params.sentiment}
              set={(v: number) => setParams({ ...params, sentiment: v })}
              min={-30}
              max={30}
              unit="pkt"
              color="blue"
            />
          </div>
        </div>
      </div>

      {/* PRAWY PANEL */}
      <div className="lg:col-span-8 space-y-6">
        {/* OŚ CZASU */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <Calendar size={16} /> Data Analizy
            </h3>
            <span className="text-lg font-bold text-[#002D72] bg-blue-50 px-4 py-1 rounded-md border border-blue-100">
              {currentRecord?.Date?.substring(0, 7) || "..."}
            </span>
          </div>

          <input
            type="range"
            min={0}
            max={Math.max(0, sectorData.length - 1)}
            step={1}
            value={dateIndex}
            onChange={(e) => setDateIndex(parseInt(e.target.value))}
            className="w-full h-3 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#002D72]"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-2 font-bold">
            <span>{sectorData[0]?.Date?.substring(0, 4)}</span>
            <span>
              {sectorData[sectorData.length - 1]?.Date?.substring(0, 4)}
            </span>
          </div>
        </div>

        {/* GŁÓWNY WYKRES PORÓWNAWCZY */}
        <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-lg font-bold text-[#002D72]">
                Wynik Stress-Testu
              </h3>
              <p className="text-xs text-slate-400 uppercase mt-1">
                Porównanie Scenariuszy
              </p>
            </div>
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xl ${
                Math.abs(diff) > 0.01
                  ? diff > 0
                    ? "bg-emerald-50 text-emerald-600"
                    : "bg-rose-50 text-rose-600"
                  : "bg-slate-50 text-slate-400"
              }`}
            >
              {diff > 0 ? "+" : ""}
              {diff.toFixed(1)} pkt
              {diff > 0.01 && <TrendingUp size={20} />}
              {diff < -0.01 && <TrendingDown size={20} />}
            </div>
          </div>

          {/* KONTENER WYKRESU */}
          <div className="w-full" style={{ height: "400px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                barCategoryGap="20%"
                margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#f1f5f9"
                />
                <XAxis
                  dataKey="name"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 14, fontWeight: "bold", fill: "#64748b" }}
                  dy={10}
                />
                <YAxis domain={[0, 100]} hide />
                <Tooltip
                  cursor={{ fill: "transparent" }}
                  contentStyle={{
                    borderRadius: "12px",
                    border: "none",
                    boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                  }}
                />
                <Bar
                  dataKey="score"
                  radius={[8, 8, 0, 0]}
                  label={{
                    position: "top",
                    fill: "#334155",
                    fontSize: 16,
                    fontWeight: "bold",
                    formatter: (v: any) => v.toFixed(1),
                  }}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- KOMPONENT SLIDERA (TYPE-SAFE) ---
const Slider = ({
  label,
  val,
  set,
  min,
  max,
  step = 1,
  unit,
  isRisk,
  color = "blue",
}: SliderProps) => {
  const percent = ((val - min) / (max - min)) * 100;

  const colors: Record<string, string> = {
    green: "bg-green-600",
    emerald: "bg-emerald-600",
    teal: "bg-teal-600",
    rose: "bg-rose-600",
    orange: "bg-orange-500",
    blue: "bg-[#002D72]",
  };
  const badgeColors: Record<string, string> = {
    green: "text-green-600 bg-green-50",
    emerald: "text-emerald-600 bg-emerald-50",
    teal: "text-teal-600 bg-teal-50",
    rose: "text-rose-600 bg-rose-50",
    orange: "text-orange-600 bg-orange-50",
    blue: "text-blue-600 bg-blue-50",
  };

  const barColor = isRisk ? "bg-rose-500" : colors[color] || colors.blue;
  const badgeStyle = isRisk
    ? "text-rose-600 bg-rose-50"
    : badgeColors[color] || badgeColors.blue;

  return (
    <div>
      <div className="flex justify-between mb-1">
        <label className="text-[10px] font-bold text-slate-500 uppercase">
          {label}
        </label>
        <span
          className={`text-[10px] font-mono font-bold px-1.5 rounded ${
            val !== 0 ? badgeStyle : "text-slate-300"
          }`}
        >
          {val > 0 ? "+" : ""}
          {val} {unit}
        </span>
      </div>
      <div className="relative w-full h-1.5 bg-slate-100 rounded-full cursor-pointer">
        <div
          className={`absolute h-full rounded-full ${barColor}`}
          style={{ width: `${percent}%` }}
        ></div>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={val}
          onChange={(e) => set(parseFloat(e.target.value))}
          className="absolute w-full h-full opacity-0 cursor-pointer z-10"
        />
      </div>
    </div>
  );
};

export default SimulationView;
