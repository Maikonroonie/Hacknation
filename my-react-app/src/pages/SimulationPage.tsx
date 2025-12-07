import { useEffect, useState } from "react";
import Papa from "papaparse";
import Layout from "../components/Layout";
import SimulationView, { DataRecord } from "../components/SimulationView";

const SimulationPage = () => {
  const [data, setData] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 1. Sprawdzamy czy plik istnieje
        const filePath = "/data/processed/MASTER_DATA.csv";
        console.log(` Próba pobrania pliku: ${filePath}`);

        const response = await fetch(filePath);

        if (!response.ok) {
          throw new Error(
            `Błąd HTTP: ${response.status} - Nie znaleziono pliku w ${filePath}`
          );
        }

        const csvText = await response.text();

        if (!csvText || csvText.length < 10) {
          throw new Error("Plik CSV jest pusty lub uszkodzony.");
        }

        // 2. Parsujemy CSV
        const result = Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          delimiter: ",", // Wymuszamy przecinek (standardowy format z Pythona)
        });

        if (result.errors.length > 0) {
          console.warn("Ostrzeżenia parsera CSV:", result.errors);
        }

        // 3. Konwertujemy dane
        const parsedData = result.data.map((d: any) => {
          // Funkcja pomocnicza do czyszczenia liczb
          const cleanNum = (val: any, defaultVal = 50) => {
            if (val === undefined || val === null || val === "")
              return defaultVal;
            // Zamiana przecinka na kropkę
            const str = String(val).replace(",", ".");
            const num = parseFloat(str);
            return isNaN(num) ? defaultVal : num;
          };

          return {
            Date: d.Date || "2024-01-01",
            PKD_Code: d.PKD_Code || "00",
            PKO_SCORE_FINAL: cleanNum(d.PKO_SCORE_FINAL, 0),
            Norm_Growth: cleanNum(d.Norm_Growth),
            Norm_Liquidity: cleanNum(d.Norm_Liquidity),
            Norm_Employ: cleanNum(d.Norm_Employ),
            Norm_Google: cleanNum(d.Norm_Google),
            Norm_Margin: cleanNum(d.Norm_Margin),
            Norm_Total_Risk: cleanNum(d.Norm_Total_Risk),
            Norm_Bankrupt: cleanNum(d.Norm_Bankrupt),
          };
        }) as DataRecord[];

        console.log(` Załadowano ${parsedData.length} wierszy danych.`);

        if (parsedData.length === 0) {
          throw new Error("Plik CSV nie zawiera żadnych danych.");
        }

        setData(parsedData);
        setLoading(false);
      } catch (err: any) {
        console.error(" BŁĄD KRYTYCZNY:", err);
        setError(err.message || "Wystąpił nieznany błąd.");
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto mb-8">
        <h1 className="text-3xl font-light text-slate-800 tracking-tight">
          Symulator{" "}
          <span className="font-bold text-[#002D72]">Stress-Test</span>
        </h1>
      </div>

      {loading && (
        <div className="p-10 text-center text-slate-500 animate-pulse">
          Ładowanie modelu danych...
        </div>
      )}

      {error && (
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <h3 className="font-bold text-lg mb-2">Błąd ładowania danych</h3>
          <p>{error}</p>
          <p className="text-sm mt-2 opacity-75">
            Upewnij się, że plik <code>MASTER_DATA.csv</code> znajduje się w
            folderze <code>public/data/processed/</code>.
          </p>
        </div>
      )}

      {!loading && !error && data.length > 0 && <SimulationView data={data} />}
    </Layout>
  );
};

export default SimulationPage;
