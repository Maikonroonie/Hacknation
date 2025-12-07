import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { loadDashboardData, PKD_NAMES } from '../utils/dataLoader';
// Zmieniamy MasterRecord na typ, który zawiera również Predicted pola (dla PredictionRecord)
import type { MasterRecord, PredictionRecord } from '../types'; 

// --- FUNKCJE POMOCNICZE (STATUS I DATY) ---

// Czyszczenie daty ze spacji (kluczowe dla uniknięcia błędów filtrowania)
const trimDate = (dateString: string | undefined): string => {
    return dateString ? dateString.trim() : '';
};

// Funkcja dynamicznego statusu
const getDynamicStatus = (rankKey: string, value: number) => {
    let label = 'N/A';
    let className = 'bg-gray-100 text-gray-800';

    if (value === 0) return { label: 'Brak danych', className: 'bg-gray-100 text-gray-500' };

    // 1. Domyślny PKO Score (progi 60/40)
    if (rankKey === 'PKO_SCORE_FINAL') {
        if (value >= 60) { label = 'Stabilny'; className = 'bg-green-100 text-green-800' }
        else if (value >= 40) { label = 'Umiarkowany'; className = 'bg-yellow-100 text-yellow-800' }
        else { label = 'Ryzyko'; className = 'bg-red-100 text-red-800' }
    } 
    // 2. Rankingi, gdzie NIŻSZA wartość jest lepsza (Slowdown, Loan_Needs)
    else if (rankKey === 'Rank_Slowdown' || rankKey === 'Rank_Loan_Needs') {
        // Progi odwrócone (30 to dobry rank, 70 to zły)
        if (value <= 30) { label = 'NISKIE RYZYKO'; className = 'bg-green-100 text-green-800' }
        else if (value <= 70) { label = 'UMIARKOWANE'; className = 'bg-yellow-100 text-yellow-800' }
        else { label = 'WYSOKIE RYZYKO'; className = 'bg-red-100 text-red-800' }
    } 
    // 3. Rankingi, gdzie WYŻSZA wartość jest lepsza (Growth, Trend)
    else if (rankKey === 'Rank_Growth' || rankKey === 'Rank_Trend_Signal') {
        // Progi standardowe (70 to dobry rank, 40 to zły)
        if (value >= 70) { label = 'Wysoki Rank'; className = 'bg-green-100 text-green-800' }
        else if (value >= 40) { label = 'Średni Rank'; className = 'bg-yellow-100 text-yellow-800' }
        else { label = 'Niski Rank'; className = 'bg-red-100 text-red-800' }
    }

    return { label, className };
};


// --- KONFIGURACJA RANKINGU ---
const RANKING_OPTIONS = [
  { key: 'PKO_SCORE_FINAL', label: 'PKO Score (Główny)' },
  { key: 'Rank_Growth', label: 'Ranking Wzrostu (Growth)' },
  { key: 'Rank_Slowdown', label: 'Ranking Spowolnienia (Slowdown)' },
  { key: 'Rank_Loan_Needs', label: 'Ranking Zapotrzebowania na Kredyt' },
  { key: 'Rank_Trend_Signal', label: 'Ranking Sygnału Trendu' },
];

// Typ lokalny dla wiersza tabeli
interface TableRow {
  pkdCode: string;
  pkdName: string;
  score: number; // PKO_SCORE_FINAL
  rankGrowth: number;
  rankSlowdown: number;
  rankLoanNeeds: number;
  rankTrendSignal: number;
  type: 'Historia' | 'Prognoza AI';
}

const RankingPage = () => {
  const [loading, setLoading] = useState(true);
  const [rawHistory, setRawHistory] = useState<MasterRecord[]>([]);
  const [rawPredictions, setRawPredictions] = useState<PredictionRecord[]>([]);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  
  const [selectedRanking, setSelectedRanking] = useState<string>('PKO_SCORE_FINAL');

  // 1. Ładowanie danych
  useEffect(() => {
    const fetchData = async () => {
      const { rawMaster, rawPredictions } = await loadDashboardData();
      
      setRawHistory(rawMaster);
      setRawPredictions(rawPredictions);

      // Czyszczenie dat dla prawidłowego dopasowania i przechowywania w stanie
      const historyDates = new Set(rawMaster.map(d => trimDate(d.Date)));
      const predictionDates = new Set(rawPredictions.map(d => trimDate(d.Date)));
      
      const allDates = Array.from(new Set([...historyDates, ...predictionDates]))
        .filter(d => d.length > 0)
        .sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

      setAvailableDates(allDates);
      
      if (allDates.length > 0) setSelectedDate(allDates[0]);
      
      setLoading(false);
    };
    fetchData();
  }, []);

  // 2. Logika pobierania wartości do sortowania
  const getSortValue = (item: TableRow, key: string) => {
    switch (key) {
      case 'PKO_SCORE_FINAL':
        return item.score;
      case 'Rank_Growth':
        return item.rankGrowth;
      case 'Rank_Slowdown':
        return item.rankSlowdown;
      case 'Rank_Loan_Needs':
        return item.rankLoanNeeds;
      case 'Rank_Trend_Signal':
        return item.rankTrendSignal;
      default:
        return item.score;
    }
  };

  // 3. Obliczanie rankingu (Filtrowanie i Sortowanie)
  const currentRanking = useMemo(() => {
    if (!selectedDate) return [];

    const rankingMap = new Map<string, TableRow>();
    
    // Filtrowanie musi użyć trimDate
    const historyForDate = rawHistory.filter(d => trimDate(d.Date) === selectedDate);
    const predictionsForDate = rawPredictions.filter(d => trimDate(d.Date) === selectedDate);

    // Parowanie wyników z CSV
    const parseRankValue = (value: string | number | undefined): number => 
        parseFloat(((value ?? 0) as string).toString().replace(',', '.'));

    historyForDate.forEach(item => {
      const pkdCode = item.PKD_Code === '1' ? '01' : item.PKD_Code;
      
      if (pkdCode) {
        rankingMap.set(pkdCode, {
          pkdCode: pkdCode,
          pkdName: PKD_NAMES[pkdCode] || pkdCode,
          score: parseRankValue(item.PKO_SCORE_FINAL),
          // Historia używa standardowych nazw Rank_Growth
          rankGrowth: parseRankValue(item.Rank_Growth),
          rankSlowdown: parseRankValue(item.Rank_Slowdown),
          rankLoanNeeds: parseRankValue(item.Rank_Loan_Needs),
          rankTrendSignal: parseRankValue(item.Rank_Trend_Signal),
          type: 'Historia',
        });
      }
    });

    predictionsForDate.forEach(item => {
      const pkdCode = item.PKD_Code === '1' ? '01' : item.PKD_Code;
      
      if (pkdCode) {
        rankingMap.set(pkdCode, {
          pkdCode: pkdCode,
          pkdName: PKD_NAMES[pkdCode] || pkdCode,
          score: parseRankValue(item.Predicted_Score),
          // ZMIANA: Prognoza używa nowych nazw pól (Rank_Growth_Predicted)
          rankGrowth: parseRankValue(item.Rank_Growth_Predicted),
          rankSlowdown: parseRankValue(item.Rank_Slowdown_Predicted),
          rankLoanNeeds: parseRankValue(item.Rank_Loan_Needs_Predicted),
          rankTrendSignal: parseRankValue(item.Rank_Trend_Signal_Predicted),
          type: 'Prognoza AI',
        });
      }
    });

    // --- KLUCZOWA ZMIANA SORTOWANIA ---
    const rankingArray = Array.from(rankingMap.values());
    
    // Sprawdzamy, czy wybrany ranking to "Slowdown" lub "Loan_Needs" (czyli sortowanie rosnące)
    const isAscending = 
        selectedRanking === 'Rank_Slowdown' || 
        selectedRanking === 'Rank_Loan_Needs';

    // Sortowanie dynamiczne: (a - b) dla rosnąco, (b - a) dla malejąco
    return rankingArray.sort((a, b) => {
        const valA = getSortValue(a, selectedRanking);
        const valB = getSortValue(b, selectedRanking);
        
        if (isAscending) {
            return valA - valB;
        }
        return valB - valA;
    });

  }, [selectedDate, selectedRanking, rawHistory, rawPredictions]);

  // KPI - Obliczenia
  const topIndustry = currentRanking[0];
  const lowIndustry = currentRanking[currentRanking.length - 1];
  const avgScore = currentRanking.length > 0 
    ? (currentRanking.reduce((acc, item) => acc + item.score, 0) / currentRanking.length).toFixed(1) 
    : 0;

  const currentRankingLabel = RANKING_OPTIONS.find(o => o.key === selectedRanking)?.label || '';


  return (
    <Layout>
      <div className="flex flex-col md:flex-row justify-between items-end mb-8 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-pko-navy">Ranking Kondycji Branż</h2>
          <p className="text-sm text-gray-500 mt-1">Wybierz datę i typ rankingu, aby zobaczyć stan rynku.</p>
        </div>

        {/* SELECTORY DATY I RANKINGU */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Wybór Okresu */}
          <div className="bg-white p-3 rounded-lg shadow-sm border border-gray-200">
            <label className="block text-xs font-bold text-gray-400 mb-1">WYBIERZ OKRES:</label>
            <select 
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-gray-50 border border-gray-300 text-pko-navy font-bold text-sm rounded focus:ring-pko-blue focus:border-pko-blue block w-40 p-2"
            >
              {availableDates.map(date => {
                const isFuture = rawPredictions.some(p => trimDate(p.Date) === date) && !rawHistory.some(h => trimDate(h.Date) === date);
                return <option key={date} value={date}>{date} {isFuture ? '(PROGNOZA AI)' : ''}</option>;
              })}
            </select>
          </div>
          
          {/* Wybór Typu Rankingu */}
          <div className="bg-white p-3 rounded-lg shadow-sm border border-gray-200">
            <label className="block text-xs font-bold text-gray-400 mb-1">TYP RANKINGU:</label>
            <select 
              value={selectedRanking}
              onChange={(e) => setSelectedRanking(e.target.value)}
              className="bg-gray-50 border border-gray-300 text-pko-navy font-bold text-sm rounded focus:ring-pko-red focus:border-pko-red block w-48 p-2"
            >
              {RANKING_OPTIONS.map(option => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><div className="animate-spin h-10 w-10 border-4 border-pko-navy border-t-transparent rounded-full"></div></div>
      ) : (
        <>
          {/* KAFELKI KPI (PKO Score) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-green-500">
              <p className="text-xs text-gray-400 font-bold uppercase">Lider Rankingu (Wg PKO Score)</p>
              <div className="flex justify-between items-end mt-2">
                <div className="overflow-hidden">
                  <h3 className="text-lg font-bold text-pko-navy truncate max-w-[180px]" title={topIndustry?.pkdName}>{topIndustry?.pkdName || '-'}</h3>
                  <p className="text-xs text-gray-400 font-mono">PKD: {topIndustry?.pkdCode}</p>
                </div>
                <span className="text-3xl font-bold text-green-600">{topIndustry?.score.toFixed(1)}</span>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-pko-blue">
              <p className="text-xs text-gray-400 font-bold uppercase">Średnia PKO Score</p>
              <div className="flex justify-between items-end mt-2">
                <h3 className="text-lg font-bold text-pko-navy">Cały Rynek</h3>
                <div className="text-right">
                  <span className="text-3xl font-bold text-pko-navy">{avgScore}</span>
                  <span className="text-xs block text-gray-400">pkt</span>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border-l-4 border-pko-red">
              <p className="text-xs text-gray-400 font-bold uppercase">Najsłabszy Wynik (Wg PKO Score)</p>
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
                Ranking wg: <span className="text-pko-navy">{currentRankingLabel}</span>
                
                {/* DYNAMICZNY OPIS SORTOWANIA */}
                {(selectedRanking === 'Rank_Slowdown' || selectedRanking === 'Rank_Loan_Needs') && (
                  <span className="text-xs text-gray-400 ml-3">
                    (Niższe wartości są lepsze)
                  </span>
                )}
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
                    <th className="px-6 py-4 text-right">Wynik {selectedRanking.includes('Rank_') ? '' : '(PKO Score)'}</th>
                    <th className="px-6 py-4 text-center">Status</th>
                    <th className="px-6 py-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {currentRanking.map((item, index) => {
                      const rankValue = getSortValue(item, selectedRanking);
                      const isScore = selectedRanking === 'PKO_SCORE_FINAL';

                      const { label: statusLabel, className: statusClass } = getDynamicStatus(selectedRanking, rankValue);
                                            
                      return (
                        <tr key={item.pkdCode} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 text-gray-400 font-mono text-sm">{index + 1}</td>
                          <td className="px-6 py-4">
                            <div className="flex flex-col">
                              <span className="font-bold text-pko-navy text-sm">{item.pkdName}</span>
                              <span className="text-xs text-gray-400 font-mono">Kod: {item.pkdCode}</span>
                            </div>
                          </td>
                          
                          <td className="px-6 py-4 text-right font-bold text-pko-text text-lg">
                            {isScore ? rankValue.toFixed(2) : Math.round(rankValue)}
                          </td>
                          
                          <td className="px-6 py-4 text-center">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}`}>
                              {statusLabel}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <Link to={`/industry/${item.pkdCode}`} className="text-sm font-medium text-pko-navy hover:text-pko-red transition-colors">
                              Analiza &rarr;
                            </Link>
                          </td>
                        </tr>
                      );
                  })}
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