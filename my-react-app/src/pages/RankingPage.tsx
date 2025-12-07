import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { loadDashboardData, PKD_NAMES } from '../utils/dataLoader';
import type { MasterRecord, PredictionRecord } from '../types';

// Typ lokalny dla wiersza tabeli
interface TableRow {
  pkdCode: string;
  pkdName: string;
  score: number;
  revenue: number; // Zostawiamy w typie, żeby nie psuć logiki ładowania, ale nie wyświetlamy
  type: 'Historia' | 'Prognoza AI';
}

const RankingPage = () => {
  const [loading, setLoading] = useState(true);
  const [rawHistory, setRawHistory] = useState<MasterRecord[]>([]);
  const [rawPredictions, setRawPredictions] = useState<PredictionRecord[]>([]);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');

  // 1. Ładowanie danych
  useEffect(() => {
    const fetchData = async () => {
      const { rawMaster, rawPredictions } = await loadDashboardData();
      
      setRawHistory(rawMaster);
      setRawPredictions(rawPredictions);

      const historyDates = new Set(rawMaster.map(d => d.Date));
      const predictionDates = new Set(rawPredictions.map(d => d.Date));
      const allDates = Array.from(new Set([...historyDates, ...predictionDates]))
        .sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

      setAvailableDates(allDates);
      
      if (allDates.length > 0) setSelectedDate(allDates[0]);
      
      setLoading(false);
    };
    fetchData();
  }, []);

  // 2. Logika filtrowania rankingu po dacie
  const currentRanking = useMemo(() => {
    if (!selectedDate) return [];

    const rankingMap = new Map<string, TableRow>();

    const historyForDate = rawHistory.filter(d => d.Date === selectedDate);
    const predictionsForDate = rawPredictions.filter(d => d.Date === selectedDate);

    historyForDate.forEach(item => {
      if (item.PKD_Code) {
        rankingMap.set(item.PKD_Code, {
          pkdCode: item.PKD_Code,
          pkdName: PKD_NAMES[item.PKD_Code] || item.PKD_Code,
          score: parseFloat(item.PKO_SCORE_FINAL.replace(',', '.')),
          revenue: parseFloat(item.Revenue ? item.Revenue.replace(',', '.') : '0'),
          type: 'Historia'
        });
      }
    });

    predictionsForDate.forEach(item => {
      if (item.PKD_Code) {
        rankingMap.set(item.PKD_Code, {
          pkdCode: item.PKD_Code,
          pkdName: PKD_NAMES[item.PKD_Code] || item.PKD_Code,
          score: parseFloat(item.Predicted_Score.replace(',', '.')),
          revenue: 0,
          type: 'Prognoza AI'
        });
      }
    });

    return Array.from(rankingMap.values()).sort((a, b) => b.score - a.score);

  }, [selectedDate, rawHistory, rawPredictions]);

  // KPI - Obliczenia
  const topIndustry = currentRanking[0];
  const lowIndustry = currentRanking[currentRanking.length - 1];
  const avgScore = currentRanking.length > 0 
    ? (currentRanking.reduce((acc, item) => acc + item.score, 0) / currentRanking.length).toFixed(1) 
    : 0;

  return (
    <Layout>
      <div className="flex flex-col md:flex-row justify-between items-end mb-8 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-pko-navy">Ranking Kondycji Branż</h2>
          <p className="text-sm text-gray-500 mt-1">Wybierz datę, aby zobaczyć stan rynku (historyczny lub prognozowany).</p>
        </div>

        {/* DATE PICKER */}
        <div className="bg-white p-3 rounded-lg shadow-sm border border-gray-200">
          <label className="block text-xs font-bold text-gray-400 mb-1">WYBIERZ OKRES:</label>
          <select 
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-gray-50 border border-gray-300 text-pko-navy font-bold text-sm rounded focus:ring-pko-blue focus:border-pko-blue block w-64 p-2"
          >
            {availableDates.map(date => {
              const isFuture = rawPredictions.some(p => p.Date === date) && !rawHistory.some(h => h.Date === date);
              return <option key={date} value={date}>{date} {isFuture ? '(PROGNOZA AI)' : ''}</option>;
            })}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><div className="animate-spin h-10 w-10 border-4 border-pko-navy border-t-transparent rounded-full"></div></div>
      ) : (
        <>
          {/* KAFELKI KPI */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-green-500">
              <p className="text-xs text-gray-400 font-bold uppercase">Lider Rankingu</p>
              <div className="flex justify-between items-end mt-2">
                <div className="overflow-hidden">
                  <h3 className="text-lg font-bold text-pko-navy truncate max-w-[180px]" title={topIndustry?.pkdName}>{topIndustry?.pkdName || '-'}</h3>
                  <p className="text-xs text-gray-400 font-mono">PKD: {topIndustry?.pkdCode}</p>
                </div>
                <span className="text-3xl font-bold text-green-600">{topIndustry?.score.toFixed(1)}</span>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-pko-blue">
              <p className="text-xs text-gray-400 font-bold uppercase">Średnia Rynkowa</p>
              <div className="flex justify-between items-end mt-2">
                <h3 className="text-lg font-bold text-pko-navy">Cały Rynek</h3>
                <div className="text-right">
                  <span className="text-3xl font-bold text-pko-navy">{avgScore}</span>
                  <span className="text-xs block text-gray-400">pkt</span>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-pko-red">
              <p className="text-xs text-gray-400 font-bold uppercase">Najsłabszy Wynik</p>
              <div className="flex justify-between items-end mt-2">
                <div className="overflow-hidden">
                  <h3 className="text-lg font-bold text-pko-navy truncate max-w-[180px]" title={lowIndustry?.pkdName}>{lowIndustry?.pkdName || '-'}</h3>
                  <p className="text-xs text-gray-400 font-mono">PKD: {lowIndustry?.pkdCode}</p>
                </div>
                <span className="text-3xl font-bold text-pko-red">{lowIndustry?.score.toFixed(1)}</span>
              </div>
            </div>
          </div>

          {/* TABELA */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
            <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <span className="text-sm font-bold text-gray-600">
                Dane dla: <span className="text-pko-navy">{selectedDate}</span>
              </span>
              <span className={`text-xs px-2 py-1 rounded border font-bold ${currentRanking[0]?.type === 'Prognoza AI' ? 'bg-purple-100 text-purple-700 border-purple-200' : 'bg-blue-100 text-blue-700 border-blue-200'}`}>
                Źródło: {currentRanking[0]?.type || 'Brak'}
              </span>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-xs text-gray-500 uppercase bg-white border-b border-gray-200">
                    <th className="px-6 py-4 w-12">#</th>
                    <th className="px-6 py-4">Branża</th>
                    {/* USUNIĘTO KOLUMNĘ PRZYCHÓD Z NAGŁÓWKA */}
                    <th className="px-6 py-4 text-right">Score</th>
                    <th className="px-6 py-4 text-center">Status</th>
                    <th className="px-6 py-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {currentRanking.map((item, index) => (
                    <tr key={item.pkdCode} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 text-gray-400 font-mono text-sm">{index + 1}</td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="font-bold text-pko-navy text-sm">{item.pkdName}</span>
                          <span className="text-xs text-gray-400 font-mono">Kod: {item.pkdCode}</span>
                        </div>
                      </td>
                      
                      {/* USUNIĘTO KOLUMNĘ PRZYCHÓD Z WIERSZY */}

                      <td className="px-6 py-4 text-right font-bold text-pko-text text-lg">{item.score.toFixed(2)}</td>
                      <td className="px-6 py-4 text-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${item.score >= 60 ? 'bg-green-100 text-green-800' : item.score >= 40 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                          {item.score >= 60 ? 'Stabilny' : item.score >= 40 ? 'Umiarkowany' : 'Ryzyko'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link to={`/industry/${item.pkdCode}`} className="text-sm font-medium text-pko-navy hover:text-pko-red transition-colors">
                          Analiza &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
};

export default RankingPage;