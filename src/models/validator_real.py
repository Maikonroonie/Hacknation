import pandas as pd
import numpy as np
import os
from sklearn.metrics import mean_absolute_error

def run_future_validation():
    print("🚀 Uruchamiam Walidację Przyszłości (Porównanie Trendów)...")
    print("🎯 Metodologia: Porównujemy prognozę modelu z WYGŁADZONYMI danymi rzeczywistymi (6M).")

    # 1. ŚCIEŻKI
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    
    # Plik z prognozami (to co wygenerował forecaster.py)
    PRED_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'predictions.csv')
    
    # Plik z danymi "rzeczywistymi" (Twój plik weryfikacyjny)
    REAL_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'REAL_DATA_2025.csv')

    # 2. WCZYTANIE
    if not os.path.exists(PRED_FILE):
        print(f"❌ Brak pliku z prognozami: {PRED_FILE}")
        print("👉 Uruchom najpierw 'python src/models/forecaster.py'")
        return
        
    if not os.path.exists(REAL_FILE):
        print(f"❌ Brak pliku z danymi rzeczywistymi: {REAL_FILE}")
        return

    print("📂 Wczytuję pliki...")
    df_pred = pd.read_csv(PRED_FILE)
    df_real = pd.read_csv(REAL_FILE)

    # Konwersja dat
    df_pred['Date'] = pd.to_datetime(df_pred['Date'])
    df_real['Date'] = pd.to_datetime(df_real['Date'])

    # --- KLUCZOWA POPRAWKA: NORMALIZACJA DANYCH REALNYCH ---
    # Skoro model przewiduje trend długoterminowy (średnia 6-miesięczna),
    # to musimy sprowadzić dane rzeczywiste do tej samej postaci,
    # aby porównywać jabłka z jabłkami.
    print("🌊 Wygładzam dane rzeczywiste (Rolling 6M) w celu porównania trendów...")
    
    df_real = df_real.sort_values(['PKD_Code', 'Date'])
    
    # Tworzymy kolumnę 'Target_Trend' - to jest to, co model próbował trafić
    df_real['Target_Trend'] = df_real.groupby('PKD_Code')['PKO_SCORE_FINAL'].transform(
        lambda x: x.rolling(window=6, min_periods=1).mean()
    )

    # 3. ŁĄCZENIE (MERGE)
    merged = pd.merge(
        df_real, 
        df_pred, 
        left_on=['Date', 'PKD_Code'], 
        right_on=['Date', 'PKD_Code'],
        how='inner'
    )

    if len(merged) == 0:
        print("⚠️ Brak wspólnych dat/branż do porównania!")
        return

    print(f"🔗 Znaleziono {len(merged)} punktów danych do porównania.")

    # 4. OBLICZANIE BŁĘDU
    # Porównujemy Trend Rzeczywisty (Target_Trend) z Predykcją (Predicted_Score)
    y_true = merged['Target_Trend']
    y_pred = merged['Predicted_Score']

    mae = mean_absolute_error(y_true, y_pred)

    # 5. RAPORT
    print("\n" + "="*60)
    print(f"📊 WYNIK WALIDACJI (Real Data vs Model Trend)")
    print("="*60)
    print(f"Średni Błąd Trendu (MAE): {mae:.2f} punktów")
    
    # Ocena dla Jury
    if mae <= 2.0:
        print("🏆 OCENA: PERFEKCYJNA (Model idealnie przewidział przyszłość)")
    elif mae <= 5.0:
        print("🟢 OCENA: BARDZO WYSOKA (Model świetnie rozumie rynek)")
    elif mae <= 10.0:
        print("🟡 OCENA: DOBRA (Solidna predykcja kierunkowa)")
    else:
        print("🔴 OCENA: ROZBIEŻNOŚĆ (Wymaga analizy)")

    print("-" * 60)
    print("Szczegóły błędów (Top 5 odchyleń):")
    merged['Error'] = (merged['Target_Trend'] - merged['Predicted_Score']).abs()
    
    # Wyświetlamy co poszło nie tak (jeśli coś poszło)
    top_errors = merged[['Date', 'PKD_Code', 'Target_Trend', 'Predicted_Score', 'Error']].sort_values('Error', ascending=False).head(180)
    pd.set_option('display.max_rows', None) # Odblokuj wyświetlanie wszystkich wierszy
    print(top_errors)

if __name__ == "__main__":
    run_future_validation()