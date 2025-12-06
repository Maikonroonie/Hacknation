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
  revenue: number;
  type: 'Historia' | 'Prognoza AI'; // Czy to dane historyczne czy predykcja
}

const RankingPage = () => {
  const [loading, setLoading] = useState(true);
  
  // Przechowujemy surowe dane, żeby móc filtrować
  const [rawHistory, setRawHistory] = useState<MasterRecord[]>([]);
  const [rawPredictions, setRawPredictions] = useState<PredictionRecord[]>([]);
  
  // Lista wszystkich dostępnych dat (unikalne, posortowane)
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  
  // Aktualnie wybrana data
  const [selectedDate, setSelectedDate] = useState<string>('');

  // 1. Ładowanie danych przy starcie
  useEffect(() => {
    const fetchData = async () => {
      const { rawMaster, rawPredictions } = await loadDashboardData();
      
      setRawHistory(rawMaster);
      setRawPredictions(rawPredictions);

      // Wyciągamy unikalne daty z obu zbiorów
      const historyDates = new Set(rawMaster.map(d => d.Date));
      const predictionDates = new Set(rawPredictions.map(d => d.Date));
      
      // Łączymy i sortujemy (od najnowszej do najstarszej)
      const allDates = Array.from(new Set([...historyDates, ...predictionDates]))
        .sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

      setAvailableDates(allDates);
      
      // Domyślnie wybieramy najnowszą dostępną datę
      if (allDates.length > 0) {
        setSelectedDate(allDates[0]);
      }
      
      setLoading(false);
    };
    fetchData();
  }, []);

  // 2. Przeliczanie rankingu "na żywo" gdy zmienia się data
  const currentRanking = useMemo(() => {
    if (!selectedDate) return [];

    const rankingMap = new Map<string, TableRow>();

    // Sprawdzamy czy dla tej daty mamy historię
    const historyForDate = rawHistory.filter(d => d.Date === selectedDate);
    
    // Sprawdzamy czy dla tej daty mamy predykcje
    const predictionsForDate = rawPredictions.filter(d => d.Date === selectedDate);

    // Najpierw ładujemy historię (jeśli jest)
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

    // Potem ładujemy/nadpisujemy predykcjami (jeśli są dla tej daty)
    // (Zazwyczaj data jest albo w historii albo w predykcji, ale predykcja ma priorytet jeśli data ta sama)
    predictionsForDate.forEach(item => {
      if (item.PKD_Code) {
        // Dla predykcji revenue może być 0 lub nieznane, bierzemy score
        rankingMap.set(item.PKD_Code, {
          pkdCode: item.PKD_Code,
          pkdName: PKD_NAMES[item.PKD_Code] || item.PKD_Code,
          score: parseFloat(item.Predicted_Score.replace(',', '.')),
          revenue: 0, // W modelu predykcyjnym często nie ma revenue, można dać 0 lub szukać z ostatniego miesiąca historii
          type: 'Prognoza AI'
        });
      }
    });

    // Zamiana na tablicę i sortowanie
    return Array.from(rankingMap.values())
      .sort((a, b) => b.score - a.score);

  }, [selectedDate, rawHistory, rawPredictions]);


  // Obliczenia KPI dla wybranej daty
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
          <p className="text-sm text-gray-500 mt-1">
            Analiza sytuacji rynkowej w wybranym okresie.
          </p>
        </div>

        {/* SELECTOR DATY */}
        <div className="bg-white p-2 rounded-lg shadow-sm border border-gray-200">
          <label className="block text-xs font-bold text-gray-400 mb-1 ml-1">WYBIERZ OKRES:</label>
          <select 
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-gray-50 border border-gray-300 text-pko-navy text-sm rounded-md focus:ring-pko-blue focus:border-pko-blue block w-48 p-2 font-mono"
          >
            {availableDates.map(date => {
              // Sprytne sprawdzanie czy data jest z przyszłości (czy jest w predykcjach)
              const isFuture = rawPredictions.some(p => p.Date === date) && !rawHistory.some(h => h.Date === date);
              return (
                <option key={date} value={date}>
                  {date} {isFuture ? '(Prognoza)' : ''}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-pko-navy border-t-transparent rounded-full animate-spin mb-4"></div>
          <span className="text-gray-500 font-medium">Ładowanie danych historycznych...</span>
        </div>
      ) : (
        <>
          {/* KPI */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-green-500 transition-all hover:shadow-md">
              <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Lider Rankingu</p>
              <div className="flex justify-between items-end mt-2">
                <div className="overflow-hidden">
                  <h3 className="text-lg font-bold text-pko-navy truncate max-w-[180px]" title={topIndustry?.pkdName}>
                    {topIndustry?.pkdName || '-'}
                  </h3>
                  <p className="text-xs text-gray-400 font-mono">PKD: {topIndustry?.pkdCode}</p>
                </div>
                <span className="text-3xl font-bold text-green-600">{topIndustry?.score.toFixed(1)}</span>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-pko-blue transition-all hover:shadow-md">
              <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Średnia Rynkowa</p>
              <div className="flex justify-between items-end mt-2">
                <div>
                  <h3 className="text-lg font-bold text-pko-navy">Cały Rynek</h3>
                  <p className="text-xs text-gray-400">Wszystkie sektory</p>
                </div>
                <div className="text-right">
                  <span className="text-3xl font-bold text-pko-navy">{avgScore}</span>
                  <span className="text-xs block text-gray-400">pkt</span>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-pko-red transition-all hover:shadow-md">
              <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Najsłabszy Wynik</p>
              <div className="flex justify-between items-end mt-2">
                <div className="overflow-hidden">
                  <h3 className="text-lg font-bold text-pko-navy truncate max-w-[180px]" title={lowIndustry?.pkdName}>
                    {lowIndustry?.pkdName || '-'}
                  </h3>
                  <p className="text-xs text-gray-400 font-mono">PKD: {lowIndustry?.pkdCode}</p>
                </div>
                <span className="text-3xl font-bold text-pko-red">{lowIndustry?.score.toFixed(1)}</span>
              </div>
            </div>
          </div>

          {/* TABELA */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
            <div className="p-4 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <span className="text-sm font-bold text-gray-500 uppercase">Dane dla: <span className="text-pko-navy">{selectedDate}</span></span>
              <span className={`text-xs px-2 py-1 rounded border ${
                currentRanking[0]?.type === 'Prognoza AI' 
                  ? 'bg-purple-100 text-purple-700 border-purple-200' 
                  : 'bg-blue-100 text-blue-700 border-blue-200'
              }`}>
                Źródło: {currentRanking[0]?.type || 'Brak danych'}
              </span>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-xs text-gray-500 uppercase bg-white border-b border-gray-200">
                    <th className="px-6 py-4 font-semibold w-12">#</th>
                    <th className="px-6 py-4 font-semibold">Branża</th> 
                    {/* Ukrywamy przychód dla predykcji, bo zazwyczaj go nie ma */}
                    {currentRanking[0]?.type !== 'Prognoza AI' && (
                        <th className="px-6 py-4 font-semibold text-right">Przychód (PLN)</th>
                    )}
                    <th className="px-6 py-4 font-semibold text-right">Score</th>
                    <th className="px-6 py-4 font-semibold text-center">Status</th>
                    <th className="px-6 py-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {currentRanking.map((item, index) => (
                    <tr key={item.pkdCode} className="hover:bg-gray-50 transition-all group">
                      <td className="px-6 py-4 text-gray-400 font-mono text-sm">{index + 1}</td>
                      
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="font-bold text-pko-navy text-sm">
                            {item.pkdName}
                          </span>
                          <span className="text-xs text-gray-400 font-mono">
                            Kod: {item.pkdCode}
                          </span>
                        </div>
                      </td>

                      {item.type !== 'Prognoza AI' && (
                        <td className="px-6 py-4 text-right font-mono text-gray-600 text-sm">
                          {item.revenue > 0 ? `${item.revenue.toLocaleString('pl-PL', { maximumFractionDigits: 0 })} mln` : '-'}
                        </td>
                      )}

                      <td className="px-6 py-4 text-right font-bold text-pko-text text-lg">
                        {item.score.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          item.score >= 60 ? 'bg-green-100 text-green-800' :
                          item.score >= 40 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {item.score >= 60 ? 'Stabilny' : item.score >= 40 ? 'Umiarkowany' : 'Ryzyko'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link 
                          to={`/industry/${item.pkdCode}`} 
                          className="text-sm font-medium text-pko-navy hover:text-pko-red transition-colors opacity-0 group-hover:opacity-100"
                        >
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