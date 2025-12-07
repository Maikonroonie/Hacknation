import { useEffect, useState } from 'react';
import Papa from 'papaparse';
import Layout from '../components/Layout';
import { PKD_NAMES } from '../utils/dataLoader'; 
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  RefreshCcw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Play,
  RotateCcw,
} from "lucide-react";

interface RawData {
  Date: string;
  PKD_Code: string;
  PKO_SCORE_FINAL?: string;
  Norm_Growth?: string;
  Norm_Liquidity?: string;
  Norm_Employ?: string;
  Norm_Google?: string;
  Norm_Margin?: string;
  Norm_Total_Risk?: string;
  Norm_Bankrupt?: string;
}

const SimulationPage = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/data/processed/MASTER_DATA.csv');
        const csvText = await response.text();
        
        const result = Papa.parse<RawData>(csvText, {
          header: true,
          skipEmptyLines: true,
        });

        const processed = result.data.map(d => ({
          ...d,
          PKO_SCORE_FINAL: parseFloat((d.PKO_SCORE_FINAL || '0').replace(',', '.')),
          Norm_Growth: parseFloat((d.Norm_Growth || '50').replace(',', '.')),
          Norm_Liquidity: parseFloat((d.Norm_Liquidity || '50').replace(',', '.')),
          Norm_Employ: parseFloat((d.Norm_Employ || '50').replace(',', '.')),
          Norm_Google: parseFloat((d.Norm_Google || '50').replace(',', '.')),
          Norm_Margin: parseFloat((d.Norm_Margin || '50').replace(',', '.')),
          Norm_Total_Risk: parseFloat((d.Norm_Total_Risk || '50').replace(',', '.')),
          Norm_Bankrupt: parseFloat((d.Norm_Bankrupt || '50').replace(',', '.')),
        }));

        setData(processed);
        setLoading(false);
      } catch (err) {
        console.error("Błąd ładowania danych do symulacji:", err);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-pko-navy">Symulator Rynkowy (Stress Test)</h1>
        <p className="text-gray-500 mt-1">
          Sprawdź, jak zmiana parametrów makroekonomicznych wpłynie na kondycję wybranego sektora.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin h-10 w-10 border-4 border-pko-navy border-t-transparent rounded-full"></div>
        </div>
      ) : (
        <SimulationView data={data} />
      )}
    </Layout>
  );
};


const SimulationView = ({ data }: { data: any[] }) => {
  const pkdList = Array.from(new Set(data.map((d) => d.PKD_Code))).sort();
  const defaultPkd = pkdList.find(pkd => pkd === '41') || pkdList[0] || "10";
  const [selectedPkd, setSelectedPkd] = useState(defaultPkd); 

  const [params, setParams] = useState({
    revenue: 0,
    liquidity: 0,
    employment: 0,
    wibor: 0,
    energy: 0,
    sentiment: 0,
  });

  const sectorData = data
    .filter((d) => d.PKD_Code === selectedPkd)
    .sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime());

  const lastRecord = sectorData[sectorData.length - 1];

  const calculateScore = (record: any, simulation: any) => {
    if (!record) return 0;
    

    const riskMap: Record<string, { w: number, e: number }> = {
      '41': { w: 1.0, e: 0.3 }, 
      '68': { w: 1.0, e: 0.2 }, 
      '49': { w: 0.5, e: 0.9 }, 
      '35': { w: 0.3, e: -0.5 }, 
      '10': { w: 0.4, e: 0.6 }, 
      '24': { w: 0.4, e: 1.0 }, 
      '62': { w: 0.1, e: 0.1 }, 
      'default': { w: 0.5, e: 0.5 },
    };
    const sens = riskMap[record.PKD_Code] || riskMap["default"];

    let growthScore = Math.min(100, Math.max(0, record.Norm_Growth + simulation.revenue * 1.5));
    let liqScore = Math.min(100, Math.max(0, record.Norm_Liquidity + simulation.liquidity * 2));
    let emplScore = Math.min(100, Math.max(0, record.Norm_Employ + simulation.employment * 1.5));
    let googleScore = Math.min(100, Math.max(0, record.Norm_Google + simulation.sentiment));

    let baseRisk = record.Norm_Total_Risk || 50;
    let addedRisk = (simulation.wibor * 5 * sens.w) + (simulation.energy * 0.2 * sens.e);
    let riskScore = Math.min(100, Math.max(0, baseRisk + addedRisk));

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
  // Koniec logiki symulacji

  const currentScore = lastRecord ? lastRecord.PKO_SCORE_FINAL : 0;
  const simScore = calculateScore(lastRecord, params);
  const diff = simScore - currentScore;

  const resetParams = () =>
    setParams({
      revenue: 0, liquidity: 0, employment: 0,
      wibor: 0, energy: 0, sentiment: 0,
    });
    
  const sectorName = PKD_NAMES[selectedPkd] || `Kod: ${selectedPkd}`;

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 pb-10">
      
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
            className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-lg font-bold text-pko-navy focus:ring-2 focus:ring-blue-500 outline-none"
          >
            {pkdList.map((pkd) => (
              <option key={pkd} value={pkd}>
                {PKD_NAMES[pkd] || `PKD ${pkd}`}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-6 flex-1 overflow-y-auto pr-2">
          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            <RefreshCcw size={18} className="text-blue-600" /> Parametry Symulacji
          </h3>

          <Slider label="Dynamika Przychodów" val={params.revenue} set={(v: number) => setParams({ ...params, revenue: v })} min={-20} max={20} unit="%" color="green" />
          <Slider label="Płynność Finansowa" val={params.liquidity} set={(v: number) => setParams({ ...params, liquidity: v })} min={-20} max={20} unit="pkt" color="emerald" />
          <Slider label="Zatrudnienie" val={params.employment} set={(v: number) => setParams({ ...params, employment: v })} min={-10} max={10} unit="%" color="teal" />
          
          <div className="h-px bg-slate-100 my-4"></div>

          <Slider label="Stopy % (WIBOR)" val={params.wibor} set={(v: number) => setParams({ ...params, wibor: v })} min={-5} max={5} step={0.25} unit="pp" color="rose" desc="Wrażliwość sektora uwzględniona." />
          <Slider label="Ceny Energii" val={params.energy} set={(v: number) => setParams({ ...params, energy: v })} min={-50} max={50} unit="%" color="orange" />
          <Slider label="Sentyment Google" val={params.sentiment} set={(v: number) => setParams({ ...params, sentiment: v })} min={-30} max={30} unit="pkt" color="blue" />
        </div>

        <button onClick={resetParams} className="mt-6 flex items-center justify-center gap-2 w-full py-3 bg-slate-100 hover:bg-slate-200 text-pko-navy font-semibold rounded-lg transition-colors">
          <RotateCcw size={18} /> Resetuj Ustawienia
        </button>
      </div>

      <div className="xl:col-span-8 flex flex-col gap-6">
        
        <h2 className="text-2xl font-bold text-slate-800">{sectorName} (PKD: {selectedPkd})</h2>

        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10"><Play size={100} /></div>
            <div className="text-sm font-bold text-slate-400 uppercase">Obecny Score</div>
            <div className="text-5xl font-black text-pko-navy mt-2">{currentScore.toFixed(1)}</div>
            <div className="text-sm text-slate-500 mt-2 font-medium">Stan faktyczny (Model)</div>
          </div>

          <div className={`p-6 rounded-2xl border-2 shadow-sm relative overflow-hidden transition-all duration-300 ${diff >= 0 ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
            <div className="text-sm font-bold text-slate-500 uppercase">Symulacja</div>
            <div className="flex items-baseline gap-4 mt-2">
              <div className={`text-5xl font-black ${diff >= 0 ? "text-green-700" : "text-red-700"}`}>{simScore.toFixed(1)}</div>
              <div className={`text-xl font-bold flex items-center ${diff >= 0 ? "text-green-600" : "text-red-600"}`}>
                {diff > 0 ? "+" : ""}{diff.toFixed(1)}
                {diff >= 0 ? <TrendingUp size={24} className="ml-1" /> : <TrendingDown size={24} className="ml-1" />}
              </div>
            </div>
            <div className="text-sm text-slate-600 mt-2 font-medium">Prognozowany wynik</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex-1 min-h-[400px]">
          <h3 className="font-bold text-lg text-pko-navy mb-6">Projekcja Wpływu na Trend</h3>
          <ResponsiveContainer width="100%" height="85%">
            <AreaChart data={sectorData.slice(-12)}>
              <defs>
                <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#002D72" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#002D72" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="Date" tickFormatter={(d) => d.substring(0, 7)} axisLine={false} tickLine={false} tick={{ fill: "#64748b" }} dy={10} />
              <YAxis domain={[0, 100]} hide />
              <Tooltip contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }} labelFormatter={(l) => l.substring(0, 10)} />
              
              <ReferenceLine y={currentScore} stroke="#94a3b8" strokeDasharray="3 3" label={{ value: "Obecny", fill: "#94a3b8", fontSize: 12 }} />
              <ReferenceLine y={simScore} stroke={diff >= 0 ? "#22c55e" : "#ef4444"} strokeWidth={2} label={{ value: "Symulacja", fill: diff >= 0 ? "#16a34a" : "#dc2626", fontSize: 12, fontWeight: "bold" }} />
              
              <Area type="monotone" dataKey="PKO_SCORE_FINAL" stroke="#002D72" strokeWidth={3} fillOpacity={1} fill="url(#colorScore)" name="Historia" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* AI INSIGHT */}
        <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 flex gap-4 items-start">
          <AlertTriangle className="text-blue-600 mt-1 flex-shrink-0" />
          <div>
            <h4 className="font-bold text-blue-900 text-sm uppercase">Wniosek Modelu Wrażliwości</h4>
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

const Slider = ({ label, val, set, min, max, step = 1, unit, color, desc }: any) => {
    const colors: Record<string, any> = {
        green:   { text: 'text-green-600', bg: 'bg-green-50', accent: 'accent-green-600' },
        emerald: { text: 'text-emerald-600', bg: 'bg-emerald-50', accent: 'accent-emerald-600' },
        teal:    { text: 'text-teal-600', bg: 'bg-teal-50', accent: 'accent-teal-600' },
        rose:    { text: 'text-rose-600', bg: 'bg-rose-50', accent: 'accent-rose-600' },
        orange:  { text: 'text-orange-600', bg: 'bg-orange-50', accent: 'accent-orange-600' },
        blue:    { text: 'text-blue-600', bg: 'bg-blue-50', accent: 'accent-blue-600' },
    };

    const c = colors[color] || colors['blue'];

    return (
        <div>
            <div className="flex justify-between mb-1 items-end">
            <label className="font-bold text-xs text-slate-500 uppercase">{label}</label>
            <span className={`font-mono text-sm font-bold px-2 py-0.5 rounded ${c.text} ${c.bg}`}>
                {val > 0 ? "+" : ""}{val} {unit}
            </span>
            </div>
            <input 
                type="range" 
                min={min} 
                max={max} 
                step={step} 
                value={val} 
                onChange={(e) => set(parseFloat(e.target.value))} 
                className={`w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer ${c.accent} transition-all`} 
            />
            {desc && <p className="text-[10px] text-slate-400 mt-1 leading-tight">{desc}</p>}
        </div>
    );
};

export default SimulationPage;