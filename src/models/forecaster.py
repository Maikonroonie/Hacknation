import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

def run_scoring_engine():
    print("🚀 Uruchamiam Silnik Oceniający (Scoring Engine) na pliku KOLEGI...")

    # ==========================================
    # 1. USTALANIE ŚCIEŻEK (Input)
    # ==========================================
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    
    # ŚCIEŻKA DO PLIKU WEJŚCIOWEGO (MASTER_DATA.csv)
    FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed', 'MASTER_DATA.csv')
    
    # ŚCIEŻKA DO PLIKU WYJŚCIOWEGO (predictions.csv)
    OUTPUT_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed', 'predictions.csv')

    # ==========================================
    # 2. KONFIGURACJA WAG
    # ==========================================
    WAGA_FINANSE = 0.4      # 40% (Profit_Margin)
    WAGA_RYZYKO = 0.3       # 30% (Norm_Total_Risk)
    WAGA_SENTYMENT = 0.3    # 30% (Google Trends)
    
    # ==========================================
    # 3. WCZYTANIE PLIKU
    # ==========================================
    if not os.path.exists(FILE_PATH):
        print(f"❌ BŁĄD KRYTYCZNY: Nie widzę pliku wejściowego: {FILE_PATH}")
        print("👉 Upewnij się, że plik 'MASTER_DATA.csv' jest w folderze 'data/processed'!")
        return

    print(f"📂 Wczytuję plik: {FILE_PATH}...")
    df = pd.read_csv(FILE_PATH)
    
    # Próba odczytu separatora ';' w razie problemów (choć plik kolegi ma przecinki)
    if len(df.columns) < 2:
        df = pd.read_csv(FILE_PATH, sep=';') 

    # ==========================================
    # 4. PRZYGOTOWANIE DANYCH (MAPPING)
    # ==========================================
    
    # Wyszukujemy kluczowe kolumny po fragmentach nazw
    col_rentownosc = next((c for c in df.columns if 'profit_margin' in c.lower()), None)
    col_upadlosci = next((c for c in df.columns if 'total_risk' in c.lower()), None)
    col_sentyment = next((c for c in df.columns if 'google_trends' in c.lower()), None)
    
    # Upewnienie się, że kolumny są numeryczne i nie mają NaN
    def ensure_numeric(col_name):
        if col_name in df.columns:
            return pd.to_numeric(df[col_name], errors='coerce').fillna(0)
        return 0

    df['Profit_Margin'] = ensure_numeric(col_rentownosc)
    df['Norm_Total_Risk'] = ensure_numeric(col_upadlosci)
    df['Google_Trends'] = ensure_numeric(col_sentyment)

    # ==========================================
    # 5. OBLICZANIE PUNKTÓW (SCORING)
    # ==========================================
    scaler = MinMaxScaler(feature_range=(0, 100))

    # A. Score Finanse (Profit_Margin)
    # Normalizujemy marżę. Clipujemy wartości ekstremalne (-20% do 40%)
    df['Score_Finanse'] = scaler.fit_transform(df[['Profit_Margin']].clip(-0.2, 0.4))

    # B. Score Sentyment (Google Trends)
    df['Score_Sentyment'] = scaler.fit_transform(df[['Google_Trends']])

    # C. Score Ryzyko (Norm_Total_Risk)
    # Robimy inwersję (100 - wynik), bo większe ryzyko to gorszy wynik
    df['Score_Ryzyko'] = 100 - scaler.fit_transform(df[['Norm_Total_Risk']])

    # 6. FINALNY INDEKS (Ważona suma)
    df['Final_Score'] = (
        WAGA_FINANSE * df['Score_Finanse'] +
        WAGA_RYZYKO * df['Score_Ryzyko'] +
        WAGA_SENTYMENT * df['Score_Sentyment']
    )
    
    df['Final_Score'] = df['Final_Score'].round(1)

    # ==========================================
    # 7. KLASYFIKACJA I ZAPIS
    # ==========================================
    def assign_class(score):
        if score >= 70: return "Lider Rozwoju 🚀"
        if score >= 40: return "Stabilna ⚖️"
        return "Zagrożona ⚠️"

    df['Klasa'] = df['Final_Score'].apply(assign_class)
    df = df.sort_values(by='Final_Score', ascending=False)

    # --- ZAPIS DO NOWEGO PLIKU ---
    # Upewniamy się, że folder istnieje (mimo że istniał dla pliku wejściowego)
    output_dir = os.path.dirname(OUTPUT_FILE_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    df.to_csv(OUTPUT_FILE_PATH, index=False)
    
    print("\n" + "="*70)
    print(f"🏆 SUKCES! Wynik (Final Score) zapisano do: {OUTPUT_FILE_PATH}")
    print("======================================================================")
    
    # Pokazujemy podgląd dla Frontendowca
    cols_to_show = ['PKD_Code', 'Date', 'Final_Score', 'Klasa', 'Profit_Margin']
    print(df[cols_to_show].head(5))

if __name__ == "__main__":
    run_scoring_engine()