import pandas as pd
import numpy as np
import os
from prophet import Prophet
import logging

# Wyłączamy logi Propheta (jest bardzo gadatliwy w konsoli)
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)

def run_forecaster_prophet():
    print("🚀 Uruchamiam AI Forecaster (Prophet)...")
    print("🔮 Cel: Wygenerowanie prognoz na 24 miesiące w przód.")

    # ==========================================
    # 1. USTALANIE ŚCIEŻEK
    # ==========================================
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    
    INPUT_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'MASTER_DATA.csv')
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'predictions.csv')

    # ==========================================
    # 2. WCZYTANIE DANYCH HISTORYCZNYCH
    # ==========================================
    if not os.path.exists(INPUT_FILE):
        print(f"❌ BŁĄD: Nie widzę pliku wejściowego: {INPUT_FILE}")
        return

    print(f"📂 Wczytuję historię z: {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)

    # Upewniamy się, że mamy kolumnę z Datą i Wynikiem
    if 'Date' not in df.columns:
        print("❌ BŁĄD: Brak kolumny 'Date' w pliku wejściowym! Prophet jej potrzebuje.")
        print("Upewnij się, że kolega dostarczył plik z kolumną 'Date' (YYYY-MM-DD).")
        return
    
    # Wybieramy co prognozować. Priorytet: PKO_SCORE_FINAL (jeśli kolega policzył), potem Profit_Margin
    target_col = 'PKO_SCORE_FINAL' 
    if target_col not in df.columns:
        if 'Final_Score' in df.columns:
            target_col = 'Final_Score'
        elif 'Profit_Margin' in df.columns:
            print("⚠️ Brak Final_Score, trenuję na Profit_Margin!")
            target_col = 'Profit_Margin'
        else:
            print("❌ BŁĄD: Nie wiem co prognozować (brak kolumny z wynikiem).")
            return

    print(f"🎯 Trenuję model na kolumnie: {target_col}")

    # Konwersja daty na format datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']) # Usuwamy wiersze bez daty

    # ==========================================
    # 3. TRENOWANIE MODELI (Pętla po branżach)
    # ==========================================
    unique_industries = df['PKD_Code'].unique()
    print(f"🏭 Znaleziono {len(unique_industries)} unikalnych branż.")
    
    all_forecasts = []

    for pkd in unique_industries:
        # 1. Filtrujemy dane dla jednej branży
        group = df[df['PKD_Code'] == pkd].copy()
        
        # Sortujemy chronologicznie
        group = group.sort_values('Date')

        # Prophet wymaga minimum 2 punktów danych, ale dla sensownej prognozy lepiej mieć więcej
        if len(group) < 5:
            # print(f"⚠️ Pomijam branżę {pkd} (za mało danych: {len(group)})")
            continue

        # 2. Formatowanie pod Prophet (wymaga kolumn 'ds' i 'y')
        prophet_df = group[['Date', target_col]].rename(columns={'Date': 'ds', target_col: 'y'})

        # 3. Inicjalizacja i trening modelu
        # yearly_seasonality=True -> wykrywa, że np. w grudniu budowlanka spada
        m = Prophet(yearly_seasonality=True, daily_seasonality=False, weekly_seasonality=False)
        
        try:
            m.fit(prophet_df)
        except Exception as e:
            print(f"❌ Błąd treningu dla PKD {pkd}: {e}")
            continue

        # 4. Generowanie przyszłych dat (24 miesiące)
        future = m.make_future_dataframe(periods=24, freq='M')
        
        # 5. Predykcja
        forecast = m.predict(future)

        # 6. Czyszczenie wyników
        # Zostawiamy tylko kolumny: Data, Prognoza, Dolna granica, Górna granica
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        
        # Filtrujemy tylko przyszłość (to co jest po ostatniej znanej dacie historycznej)
        last_history_date = prophet_df['ds'].max()
        future_result = result[result['ds'] > last_history_date].copy()

        # Dodajemy z powrotem kod PKD
        future_result['PKD_Code'] = pkd
        
        # Opcjonalnie: Clipujemy wynik, żeby nie wyszedł np. 150/100 albo ujemny
        future_result['yhat'] = future_result['yhat'].clip(0, 100)

        all_forecasts.append(future_result)

    # ==========================================
    # 4. ZAPIS WYNIKÓW
    # ==========================================
    if all_forecasts:
        final_df = pd.concat(all_forecasts, ignore_index=True)
        
        # Zmieniamy nazwy na czytelne dla Frontendu
        final_df = final_df.rename(columns={
            'ds': 'Date',
            'yhat': 'Predicted_Score',
            'yhat_lower': 'Confidence_Lower',
            'yhat_upper': 'Confidence_Upper'
        })

        # Zapis do CSV
        final_df.to_csv(OUTPUT_FILE, index=False)
        
        print("\n" + "="*60)
        print(f"🏆 SUKCES! Wygenerowano prognozy dla {len(unique_industries)} branż.")
        print(f"📅 Horyzont: 24 miesiące.")
        print(f"💾 Plik zapisany: {OUTPUT_FILE}")
        print("="*60)
        print("Przykładowe prognozy:")
        print(final_df.head())
        
    else:
        print("⚠️ Nie udało się wygenerować żadnych prognoz (sprawdź dane wejściowe).")

if __name__ == "__main__":
    run_forecaster_prophet()