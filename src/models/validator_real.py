import pandas as pd
import numpy as np
import os
from sklearn.metrics import mean_absolute_error

def run_future_validation():
    print("🚀 Uruchamiam Walidację Przyszłości (Porównanie z REAL_DATA_2025)...")

    # 1. ŚCIEŻKI
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    
    # Plik z prognozami (wygenerowany przez forecaster.py)
    PRED_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'predictions.csv')
    
    # Plik z danymi "rzeczywistymi" (stworzony ręcznie)
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

    # 3. ŁĄCZENIE (MERGE)
    # Łączymy prognozę z rzeczywistością po Dacie i Kodzie Branży
    # Używamy 'inner join', żeby porównać tylko te miesiące, które mamy w obu plikach
    merged = pd.merge(
        df_real, 
        df_pred, 
        left_on=['Date', 'PKD_Code'], 
        right_on=['Date', 'PKD_Code'],
        how='inner'
    )

    if len(merged) == 0:
        print("⚠️ Brak wspólnych dat/branż do porównania!")
        print(f"Zakres dat w Real: {df_real['Date'].min().date()} - {df_real['Date'].max().date()}")
        print(f"Zakres dat w Pred: {df_pred['Date'].min().date()} - {df_pred['Date'].max().date()}")
        return

    print(f"🔗 Znaleziono {len(merged)} punktów danych do porównania.")

    # 4. OBLICZANIE BŁĘDU
    # PKO_SCORE_FINAL (z REAL_DATA) vs Predicted_Score (z predictions)
    y_true = merged['PKO_SCORE_FINAL']
    y_pred = merged['Predicted_Score']

    mae = mean_absolute_error(y_true, y_pred)

    # 5. RAPORT
    print("\n" + "="*60)
    print(f"📊 WYNIK WALIDACJI (Lipiec 2024 - Czerwiec 2025)")
    print("="*60)
    print(f"Średni Błąd (MAE): {mae:.2f} punktów")
    
    # Ocena dla Jury
    if mae <= 2.0:
        print("🏆 OCENA: NIEMOŻLIWIE IDEALNA (Perfekcja)")
    elif mae <= 5.0:
        print("🟢 OCENA: BARDZO WYSOKA SKUTECZNOŚĆ")
    elif mae <= 10.0:
        print("🟡 OCENA: DOBRA (Standard rynkowy)")
    else:
        print("🔴 OCENA: ROZBIEŻNOŚĆ (Model przewidział co innego)")

    print("-" * 60)
    print("Przykładowe porównanie (Rzeczywistość vs Prognoza):")
    merged['Roznica'] = (merged['PKO_SCORE_FINAL'] - merged['Predicted_Score']).abs()
    # Wyświetlamy 5 wierszy z największym błędem, żeby zobaczyć gdzie jest problem
    print(merged[['Date', 'PKD_Code', 'PKO_SCORE_FINAL', 'Predicted_Score', 'Roznica']].sort_values('Roznica', ascending=False).head(5))

if __name__ == "__main__":
    run_future_validation()