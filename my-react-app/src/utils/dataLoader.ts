import Papa from 'papaparse';
import type { MasterRecord, PredictionRecord, IndustrySummary } from '../types';
export const PKD_NAMES: Record<string, string> = {
  "1": "Rolnictwo i uprawy",
  "01": "Rolnictwo i uprawy",
  "10": "Produkcja spożywcza",
  "16": "Produkcja wyrobów z drewna",
  "23": "Produkcja z surowców niemetalicznych",
  "24": "Produkcja metali",
  "29": "Produkcja pojazdów samochodowych",
  "31": "Produkcja mebli",
  "35": "Energetyka i media",
  "41": "Roboty budowlane",
  "46": "Handel hurtowy",
  "47": "Handel detaliczny",
  "49": "Transport lądowy i rurociągowy",
  "55": "Zakwaterowanie (Hotele)",
  "62": "Oprogramowanie i doradztwo IT",
  "68": "Obsługa rynku nieruchomości"
};

const fetchCsv = async <T>(path: string): Promise<T[]> => {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  const reader = response.body?.getReader();
  const result = await reader?.read();
  const decoder = new TextDecoder('utf-8');
  const csv = decoder.decode(result?.value);
  
  return new Promise((resolve) => {
    Papa.parse(csv, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => resolve(results.data as T[]),
    });
  });
};

export const loadDashboardData = async () => {
  try {
    const [masterData, predictionData] = await Promise.all([
      fetchCsv<MasterRecord>('/data/processed/MASTER_DATA.csv'),
      fetchCsv<PredictionRecord>('/data/processed/predictions.csv')
    ]);

    const industriesMap = new Map<string, IndustrySummary>();

    masterData.forEach(row => {
      if (row.PKD_Code && row.PKO_SCORE_FINAL) {
        const score = parseFloat(row.PKO_SCORE_FINAL.replace(',', '.'));
        const revenue = parseFloat(row.Revenue ? row.Revenue.replace(',', '.') : '0');
        
        industriesMap.set(row.PKD_Code, {
          pkdCode: row.PKD_Code,
          pkdName: PKD_NAMES[row.PKD_Code] || `Branża ${row.PKD_Code}`,
          currentScore: score,
          revenue: revenue,
        });
      }
    });

    const ranking = Array.from(industriesMap.values())
      .sort((a, b) => b.currentScore - a.currentScore);

    return { ranking, rawMaster: masterData, rawPredictions: predictionData };

  } catch (error) {
    console.error("Błąd ładowania danych:", error);
    return { ranking: [], rawMaster: [], rawPredictions: [] };
  }
};