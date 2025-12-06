import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import Papa from 'papaparse';
import Layout from '../components/Layout';
import { PKD_NAMES } from '../utils/dataLoader'; // Importujemy słownik nazw

// Lokalne definicje typów dla surowych danych z CSV
interface RawData {
  Date: string;
  PKD_Code: string;
  PKO_SCORE_FINAL?: string; // W pliku historycznym
  Predicted_Score?: string; // W pliku predykcji
}

// Typ danych gotowych do wykresu
interface ChartData {
  date: string;
  history: number | null;
  prediction: number | null;
}

const IndustryPage = () => {
  const { pkdId } = useParams(); // Pobieramy kod PKD z adresu URL
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Pobieramy oba pliki CSV równolegle
        const [masterRes, predRes] = await Promise.all([
          fetch('/data/processed/MASTER_DATA.csv'),
          fetch('/data/processed/predictions.csv')
        ]);

        const masterText = await masterRes.text();
        const predText = await predRes.text();

        // Parsujemy CSV do obiektów
        const master = Papa.parse<RawData>(masterText, { header: true, skipEmptyLines: true }).data;
        const preds = Papa.parse<RawData>(predText, { header: true, skipEmptyLines: true }).data;

        // Filtrujemy historię dla wybranej branży
        const historyData = master
          .filter(d => d.PKD_Code === pkdId)
          .map(d => ({
            date: d.Date,
            history: parseFloat((d.PKO_SCORE_FINAL || '0').replace(',', '.')),
            prediction: null
          }));

        // Filtrujemy predykcje dla wybranej branży
        const predictionData = preds
          .filter(d => d.PKD_Code === pkdId)
          .map(d => ({
            date: d.Date,
            history: null,
            prediction: parseFloat((d.Predicted_Score || '0').replace(',', '.'))
          }));

        // Łączymy dane w jedną tablicę i sortujemy chronologicznie
        const combined = [...historyData, ...predictionData].sort((a, b) => 
          new Date(a.date).getTime() - new Date(b.date).getTime()
        );

        setChartData(combined);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    };

    fetchData();
  }, [pkdId]);

  // Pobieramy nazwę branży ze słownika
  const industryName = PKD_NAMES[pkdId || ''] || `Branża ${pkdId}`;

  return (
    <Layout>
      <div className="mb-6">
        <Link to="/" className="text-sm text-gray-500 hover:text-pko-navy mb-2 inline-block font-medium">
          &larr; Wróć do rankingu
        </Link>
        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <h1 className="text-3xl font-bold text-pko-navy">
            {industryName}
          </h1>
          <span className="bg-gray-200 text-gray-600 px-2 py-1 rounded text-sm font-mono font-bold">
            PKD: {pkdId}
          </span>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64 bg-white rounded-xl border border-gray-200">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-pko-navy"></div>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="font-bold text-lg text-pko-navy">Prognoza Kondycji (PKO Score)</h3>
              <p className="text-sm text-gray-500">Dane historyczne vs. model predykcyjny AI</p>
            </div>
            
            {/* Legenda */}
            <div className="flex gap-6 text-sm">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-pko-navy"></span>
                <span className="text-gray-700 font-medium">Historia</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-pko-red"></span>
                <span className="text-gray-700 font-medium">Prognoza AI</span>
              </div>
            </div>
          </div>

          <div className="h-[450px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorHistory" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#002D72" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#002D72" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#D6001C" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#D6001C" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                
                <XAxis 
                  dataKey="date" 
                  style={{ fontSize: '11px', fill: '#666' }} 
                  tickFormatter={(str) => str.substring(0, 7)} 
                  minTickGap={30}
                />
                <YAxis domain={[0, 100]} style={{ fontSize: '11px', fill: '#666' }} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    borderRadius: '8px', 
                    border: '1px solid #e5e7eb', 
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' 
                  }}
                  itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                  labelStyle={{ color: '#6B7280', fontSize: '11px', marginBottom: '4px' }}
                />
                
                <ReferenceLine x="2024-06-01" stroke="#9CA3AF" strokeDasharray="3 3" label={{ value: 'TERAZ', position: 'insideTopLeft', fill: '#9CA3AF', fontSize: 10 }} />
                
                <Area 
                  type="monotone" 
                  dataKey="history" 
                  stroke="#002D72" 
                  strokeWidth={3}
                  fillOpacity={1} 
                  fill="url(#colorHistory)" 
                  name="Historia"
                  connectNulls
                />
                <Area 
                  type="monotone" 
                  dataKey="prediction" 
                  stroke="#D6001C" 
                  strokeWidth={3}
                  strokeDasharray="5 5"
                  fillOpacity={1} 
                  fill="url(#colorPred)" 
                  name="Prognoza"
                  connectNulls
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default IndustryPage;