
/*
// Typy danych surowych z CSV
interface RawData {
  Date: string;
  PKD_Code: string;
  PKO_SCORE_FINAL?: string;
  Predicted_Score?: string;
}

// Typ danych przetworzonych do wykresu
interface ChartData {
  date: string;
  history: number | null;
  prediction: number | null;
}

const IndustryPage = () => {
  const { pkdId } = useParams();
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 1. Pobieranie plików
        const [masterRes, predRes] = await Promise.all([
          fetch('/data/processed/MASTER_DATA.csv'),
          fetch('/data/processed/predictions.csv')
        ]);

        const masterText = await masterRes.text();
        const predText = await predRes.text();

        // 2. Parsowanie CSV
        const master = Papa.parse<RawData>(masterText, { header: true, skipEmptyLines: true }).data;
        const preds = Papa.parse<RawData>(predText, { header: true, skipEmptyLines: true }).data;

        // 3. Przetwarzanie Historii (Niebieska Linia)
        const historyData = master
          .filter(d => d.PKD_Code === pkdId)
          .map(d => ({
            date: d.Date,
            history: parseFloat((d.PKO_SCORE_FINAL || '0').replace(',', '.')),
            prediction: null // W okresie historycznym predykcja jest pusta
          }))
          .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        // Jeśli brak danych historycznych, przerwij
        if (historyData.length === 0) {
          setLoading(false);
          return;
        }

        // Pobieramy ostatni punkt historyczny (to nasz punkt styku)
        const lastHistoryPoint = historyData[historyData.length - 1];
        const lastDate = new Date(lastHistoryPoint.date);

        // 4. Przetwarzanie Predykcji (Czerwona Linia)
        const predictionData = preds
          .filter(d => d.PKD_Code === pkdId)
          // Ważne: Bierzemy tylko daty nowsze niż historia, żeby nie nakładać linii
          .filter(d => new Date(d.Date) > lastDate)
          .map(d => ({
            date: d.Date,
            history: null, // W okresie przyszłym historia jest pusta
            prediction: parseFloat((d.Predicted_Score || '0').replace(',', '.'))
          }))
          .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        // 5. TWORZENIE MOSTU (THE FIX)
        // Dodajemy sztuczny punkt na początku predykcji.
        // Ma on datę i wartość z ostatniego punktu historii.
        const bridgePoint = {
          date: lastHistoryPoint.date,
          history: null, 
          prediction: lastHistoryPoint.history // <--- Tutaj przepisujemy wartość z historii do predykcji
        };

        // Wstawiamy most na początek tablicy predykcji
        predictionData.unshift(bridgePoint);

        // 6. Łączenie danych
        const combined = [...historyData, ...predictionData];

        setChartData(combined);
        setLoading(false);
      } catch (err) {
        console.error("Błąd ładowania danych:", err);
        setLoading(false);
      }
    };

    fetchData();
  }, [pkdId]);

  const industryName = PKD_NAMES[pkdId || ''] || `Branża ${pkdId}`;

  // Znajdź datę graniczną do narysowania pionowej linii "TERAZ"
  const currentDateLine = chartData.find(d => d.history !== null && d.prediction !== null)?.date;

  return (
    <Layout>
      <div className="mb-6">
        <Link to="/" className="text-sm text-gray-500 hover:text-pko-navy mb-2 inline-block font-medium">
          &larr; Wróć do rankingu
        </Link>
        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <h1 className="text-3xl font-bold text-pko-navy">{industryName}</h1>
          <span className="bg-gray-200 text-gray-600 px-2 py-1 rounded text-sm font-mono font-bold">PKD: {pkdId}</span>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64 bg-white rounded-xl border border-gray-200">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-pko-navy"></div>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-lg text-pko-navy">Prognoza Kondycji (PKO Score)</h3>
            <div className="flex gap-6 text-sm">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-pko-navy"></span> Historia
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-pko-red"></span> Prognoza AI
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
                  contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e5e7eb' }}
                  labelStyle={{ color: '#666', marginBottom: '0.5rem' }}
                />
                
                
                {currentDateLine && (
                  <ReferenceLine x={currentDateLine} stroke="#9CA3AF" strokeDasharray="3 3" label={{ value: 'TERAZ', position: 'insideTopLeft', fill: '#9CA3AF', fontSize: 10 }} />
                )}
                
                <Area 
                  type="monotone" 
                  dataKey="history" 
                  stroke="#002D72" 
                  strokeWidth={3} 
                  fillOpacity={1} 
                  fill="url(#colorHistory)" 
                  name="Historia" 
                  connectNulls={true}
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
                  connectNulls={true}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default IndustryPage;*/

import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import Papa from 'papaparse';
import Layout from '../components/Layout';
import { PKD_NAMES } from '../utils/dataLoader';

// Typy danych surowych z CSV
interface RawData {
  Date: string;
  PKD_Code: string;
  PKO_SCORE_FINAL?: string;
  Predicted_Score?: string;
}

// Typ danych przetworzonych do wykresu
interface ChartData {
  date: string;
  history: number | null;
  prediction: number | null;
  isPrediction: boolean; // Flaga pomocnicza
}

const IndustryPage = () => {
  const { pkdId } = useParams();
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  
  // NOWE STANY: Daty i Wybór
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');

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

        // 1. Historia
        const historyData = master
          .filter(d => d.PKD_Code === pkdId)
          .map(d => ({
            date: d.Date,
            history: parseFloat((d.PKO_SCORE_FINAL || '0').replace(',', '.')),
            prediction: null,
            isPrediction: false
          }))
          .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        if (historyData.length === 0) {
          setLoading(false);
          return;
        }

        const lastHistoryPoint = historyData[historyData.length - 1];
        const lastDate = new Date(lastHistoryPoint.date);

        // 2. Predykcja
        const predictionData = preds
          .filter(d => d.PKD_Code === pkdId)
          .filter(d => new Date(d.Date) > lastDate)
          .map(d => ({
            date: d.Date,
            history: null,
            prediction: parseFloat((d.Predicted_Score || '0').replace(',', '.')),
            isPrediction: true
          }))
          .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        // 3. Most (Fix na dziurę)
        if (lastHistoryPoint) {
          predictionData.unshift({
            date: lastHistoryPoint.date,
            history: null,
            prediction: lastHistoryPoint.history,
            isPrediction: false // Most traktujemy technicznie
          });
        }

        const combined = [...historyData, ...predictionData];
        setChartData(combined);

        // 4. WYCIĄGNIĘCIE DAT DO SELECTA
        // Usuwamy duplikaty (np. przez punkt mostu) i sortujemy od najnowszej
        const uniqueDates = Array.from(new Set(combined.map(d => d.date)))
          .sort((a, b) => new Date(b).getTime() - new Date(a).getTime());
        
        setAvailableDates(uniqueDates);
        
        // Domyślnie wybierz najnowszą dostępną datę (przyszłość)
        if (uniqueDates.length > 0) setSelectedDate(uniqueDates[0]);

        setLoading(false);
      } catch (err) {
        console.error("Błąd:", err);
        setLoading(false);
      }
    };

    fetchData();
  }, [pkdId]);

  // --- LOGIKA DO KAFELKÓW (KPI) ---
  const currentDataPoint = useMemo(() => {
    return chartData.find(d => d.date === selectedDate);
  }, [selectedDate, chartData]);

  const currentScore = currentDataPoint 
    ? (currentDataPoint.prediction !== null ? currentDataPoint.prediction : currentDataPoint.history) 
    : 0;

  const isForecast = currentDataPoint?.isPrediction || (currentDataPoint?.prediction !== null && currentDataPoint?.history === null);

  const industryName = PKD_NAMES[pkdId || ''] || `Branża ${pkdId}`;

  return (
    <Layout>
      <div className="mb-8">
        <Link to="/" className="text-sm text-gray-500 hover:text-pko-navy mb-4 inline-block font-medium">
          &larr; Wróć do rankingu
        </Link>
        
        <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-6">
          {/* LEWA STRONA: Tytuł */}
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-bold text-pko-navy">{industryName}</h1>
              <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-sm font-mono font-bold border border-gray-200">
                PKD {pkdId}
              </span>
            </div>
            <p className="text-gray-500">Szczegółowa analiza kondycji finansowej sektora.</p>
          </div>

          {/* PRAWA STRONA: Selector Daty */}
          <div className="bg-white p-3 rounded-xl shadow-sm border border-gray-200">
            <label className="block text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">
              Analizowany okres:
            </label>
            <select 
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-gray-50 border border-gray-300 text-pko-navy font-bold text-sm rounded-lg focus:ring-pko-blue focus:border-pko-blue block w-64 p-2.5"
            >
              {availableDates.map(date => {
                // Sprawdzamy czy data jest w przyszłości na podstawie danych
                const point = chartData.find(d => d.date === date);
                const isPred = point?.isPrediction || (point?.prediction !== null && point?.history === null);
                return (
                  <option key={date} value={date}>
                    {date} {isPred ? '(PROGNOZA AI)' : '(HISTORIA)'}
                  </option>
                );
              })}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-pko-navy border-t-transparent"></div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          
          {/* 1. SEKCJA KPI - Zmienia się wraz z datą */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Kafel 1: Score */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 relative overflow-hidden">
              <div className={`absolute top-0 right-0 w-20 h-20 transform translate-x-8 -translate-y-8 rounded-full opacity-10 ${
                (currentScore || 0) >= 60 ? 'bg-green-600' : 'bg-red-600'
              }`}></div>
              <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-2">PKO Score</p>
              <div className="flex items-baseline gap-2">
                <span className={`text-4xl font-bold ${
                  (currentScore || 0) >= 60 ? 'text-green-600' : 
                  (currentScore || 0) >= 40 ? 'text-yellow-600' : 'text-pko-red'
                }`}>
                  {currentScore?.toFixed(2)}
                </span>
                <span className="text-gray-400 text-sm">/ 100</span>
              </div>
            </div>

            {/* Kafel 2: Status */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
              <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-2">Status Kondycji</p>
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${
                  (currentScore || 0) >= 60 ? 'bg-green-500' : 
                  (currentScore || 0) >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                <span className="text-xl font-bold text-pko-navy">
                  {(currentScore || 0) >= 60 ? 'Stabilna' : 
                   (currentScore || 0) >= 40 ? 'Umiarkowana' : 'Zagrożona'}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Na dzień: <span className="font-mono text-gray-600">{selectedDate}</span>
              </p>
            </div>

            {/* Kafel 3: Źródło */}
            <div className={`p-5 rounded-xl shadow-sm border flex flex-col justify-center ${
              isForecast 
                ? 'bg-purple-50 border-purple-100' 
                : 'bg-blue-50 border-blue-100'
            }`}>
              <p className={`text-xs font-bold uppercase tracking-wider mb-1 ${
                isForecast ? 'text-purple-600' : 'text-blue-600'
              }`}>
                Źródło Danych
              </p>
              <p className={`text-lg font-bold ${isForecast ? 'text-purple-800' : 'text-blue-800'}`}>
                {isForecast ? 'Model AI (Predykcja)' : 'Dane Historyczne'}
              </p>
              {isForecast && (
                <p className="text-[10px] text-purple-600/70 mt-1">Estymacja obarczona ryzykiem modelu</p>
              )}
            </div>
          </div>

          {/* 2. WYKRES */}
          <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-lg text-pko-navy">Trend Zmian w Czasie</h3>
              <div className="flex gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-pko-navy"></span> Historia
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-pko-red"></span> Prognoza AI
                </div>
              </div>
            </div>
            
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorHistory" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#002D72" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#002D72" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#D6001C" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#D6001C" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  
                  <XAxis 
                    dataKey="date" 
                    style={{ fontSize: '11px', fill: '#666' }} 
                    tickFormatter={(str) => str.substring(0, 7)} 
                    minTickGap={40} 
                  />
                  <YAxis domain={[0, 100]} style={{ fontSize: '11px', fill: '#666' }} />
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    labelStyle={{ color: '#666', marginBottom: '4px', fontSize: '12px' }}
                  />
                  
                  {/* PIONOWA LINIA WYBORU DATY */}
                  {selectedDate && (
                    <ReferenceLine 
                      x={selectedDate} 
                      stroke="#000" 
                      strokeOpacity={0.5}
                      strokeDasharray="3 3" 
                    />
                  )}
                  
                  <Area 
                    type="monotone" 
                    dataKey="history" 
                    stroke="#002D72" 
                    strokeWidth={3} 
                    fillOpacity={1} 
                    fill="url(#colorHistory)" 
                    name="Historia" 
                    connectNulls={true}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="prediction" 
                    stroke="#D6001C" 
                    strokeWidth={3} 
                    strokeDasharray="4 4" 
                    fillOpacity={1} 
                    fill="url(#colorPred)" 
                    name="Prognoza" 
                    connectNulls={true}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default IndustryPage;