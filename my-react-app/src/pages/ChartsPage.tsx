import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import Papa from 'papaparse';
import Layout from '../components/Layout';
import { PKD_NAMES } from '../utils/dataLoader';
import { Link } from 'react-router-dom';

// Typy danych
interface RawData {
  Date: string;
  PKD_Code: string;
  PKO_SCORE_FINAL?: string;
  Predicted_Score?: string;
}

interface ChartDataPoint {
  date: string;
  history: number | null;
  prediction: number | null;
}

interface IndustryData {
  pkdCode: string;
  pkdName: string;
  data: ChartDataPoint[];
}

const ChartsPage = () => {
  const [industries, setIndustries] = useState<IndustryData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [masterRes, predRes] = await Promise.all([
          fetch('/data/processed/MASTER_DATA.csv'),
          fetch('/data/processed/predictions.csv')
        ]);

        const masterText = await masterRes.text();
        const predText = await predRes.text();

        const master = Papa.parse<RawData>(masterText, { header: true, skipEmptyLines: true }).data;
        const preds = Papa.parse<RawData>(predText, { header: true, skipEmptyLines: true }).data;

        // 1. Znajdź wszystkie unikalne kody PKD
        // Używamy Set, żeby usunąć duplikaty i sortujemy, żeby były po kolei
        const allPkds = Array.from(new Set(master.map(d => d.PKD_Code))).filter(Boolean).sort();

        // 2. Przetwórz dane dla każdego PKD
        const processedData = allPkds.map(pkdCode => {
          // --- HISTORIA ---
          const historyData = master
            .filter(d => d.PKD_Code === pkdCode)
            .map(d => ({
              date: d.Date,
              history: parseFloat((d.PKO_SCORE_FINAL || '0').replace(',', '.')),
              prediction: null
            }))
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

          const lastHistoryPoint = historyData[historyData.length - 1];
          const lastDate = lastHistoryPoint ? new Date(lastHistoryPoint.date) : new Date();

          // --- PREDYKCJA ---
          const predictionData = preds
            .filter(d => d.PKD_Code === pkdCode)
            // Bierzemy tylko daty nowsze niż historia
            .filter(d => new Date(d.Date) > lastDate)
            .map(d => ({
              date: d.Date,
              history: null,
              prediction: parseFloat((d.Predicted_Score || '0').replace(',', '.'))
            }))
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

          // --- FIX NA DZIURĘ (MOST) ---
          if (lastHistoryPoint) {
            predictionData.unshift({
              date: lastHistoryPoint.date,
              history: null,
              prediction: lastHistoryPoint.history // Start predykcji = koniec historii
            });
          }

          // Łączymy
          const combined = [...historyData, ...predictionData];

          return {
            pkdCode,
            pkdName: PKD_NAMES[pkdCode] || `Branża ${pkdCode}`,
            data: combined
          };
        });

        setIndustries(processedData);
        setLoading(false);
      } catch (err) {
        console.error("Błąd ładowania wykresów:", err);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <Layout>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-pko-navy">Zestawienie Wykresów</h2>
        <p className="text-gray-600 mt-1">
          Pełny przegląd trendów historycznych i prognoz AI dla wszystkich {industries.length} monitorowanych sektorów.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin h-10 w-10 border-4 border-pko-navy border-t-transparent rounded-full"></div>
        </div>
      ) : (
        // Grid dostosowuje się do ekranu: 1 kolumna na telefonie, 2 na tablecie, 3 na dużym ekranie
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-10">
          {industries.map((industry) => (
            <div key={industry.pkdCode} className="bg-white p-4 rounded-xl shadow border border-gray-200 hover:shadow-md transition-shadow">
              
              {/* Nagłówek wykresu */}
              <div className="flex justify-between items-start mb-4 h-12">
                <div className="flex-1 pr-2">
                  <h3 className="font-bold text-sm text-pko-navy line-clamp-2 leading-tight" title={industry.pkdName}>
                    {industry.pkdName}
                  </h3>
                  <span className="text-xs text-gray-400 font-mono">PKD: {industry.pkdCode}</span>
                </div>
                <Link 
                  to={`/industry/${industry.pkdCode}`}
                  className="text-[10px] uppercase font-bold text-pko-blue bg-blue-50 px-2 py-1 rounded hover:bg-blue-100 transition-colors whitespace-nowrap"
                >
                  Szczegóły
                </Link>
              </div>

              {/* Wykres */}
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={industry.data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id={`grad-${industry.pkdCode}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#002D72" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#002D72" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                    <XAxis dataKey="date" hide />
                    <YAxis domain={[0, 100]} style={{ fontSize: '10px' }} tickCount={5} />
                    <Tooltip 
                      labelStyle={{ fontSize: '10px', color: '#666' }}
                      itemStyle={{ fontSize: '11px', fontWeight: 'bold' }}
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                    />
                    
                    {/* Linia odniesienia "TERAZ" */}
                    <ReferenceLine x="2024-06-01" stroke="#ccc" strokeDasharray="3 3" />
                    
                    {/* Historia */}
                    <Area 
                      type="monotone" 
                      dataKey="history" 
                      stroke="#002D72" 
                      strokeWidth={2} 
                      fill={`url(#grad-${industry.pkdCode})`} 
                      fillOpacity={1}
                      name="Historia"
                      connectNulls={true}
                    />
                    
                    {/* Predykcja */}
                    <Area 
                      type="monotone" 
                      dataKey="prediction" 
                      stroke="#D6001C" 
                      strokeWidth={2} 
                      strokeDasharray="3 3" 
                      fill="transparent" 
                      name="Prognoza AI"
                      connectNulls={true}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
};

export default ChartsPage;