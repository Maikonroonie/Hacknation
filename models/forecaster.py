import pandas as pd
import numpy as np
import os
from prophet import Prophet
import logging

# Wyłączamy logi bibliotek
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)

def run_forecaster_final():
    print("🚀 Uruchamiam AI Forecaster (Wersja 'GOLD': MAE 6.88)...")
    print("🔮 Konfiguracja: Agresywne Wygładzanie (6M) + Sztywny Trend + Makro")

    # ==========================================
    # 1. KONFIGURACJA
    # ==========================================
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    
    INPUT_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'MASTER_DATA.csv')
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'predictions.csv')

    TARGET_COL = 'PKO_SCORE_FINAL'
    
    # Zmienne makro (Regressors)
    REGRESSORS = ['WIBOR', 'Google_Trends', 'Energy_Price']

    # COVID Events (Event Modeling)
    covid_lockdowns = pd.DataFrame([
        {'holiday': 'lockdown_1', 'ds': '2020-03-01', 'lower_window': 0, 'upper_window': 2},
        {'holiday': 'lockdown_2', 'ds': '2020-10-01', 'lower_window': 0, 'upper_window': 3},
        {'holiday': 'lockdown_3', 'ds': '2021-03-01', 'lower_window': 0, 'upper_window': 1},
    ])
    covid_lockdowns['ds'] = pd.to_datetime(covid_lockdowns['ds'])

    # Zakres dat do prognozy (2 lata do przodu)
    TARGET_DATES = pd.date_range(start='2024-06-01', end='2026-05-31', freq='MS')

    # ==========================================
    # 2. WCZYTANIE I PRZYGOTOWANIE
    # ==========================================
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Błąd: Brak pliku {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # --- KROK ZWYCIĘSKI: AGRESYWNE WYGŁADZANIE (WINDOW = 6) ---
    # To dało nam wynik 6.88 MAE. Usuwamy szum, zostawiamy strategiczny trend.
    print("🌊 Wygładzam dane historyczne (Rolling Mean 6M)...")
    
    df = df.sort_values(['PKD_Code', 'Date'])
    
    # Wygładzamy Score oraz zmienne makro
    cols_to_smooth = [TARGET_COL] + [r for r in REGRESSORS if r in df.columns]
    
    for col in cols_to_smooth:
        df[col] = df.groupby('PKD_Code')[col].transform(
            lambda x: x.rolling(window=6, min_periods=1).mean()
        )

    # Uzupełniamy luki na początku (powstałe przez rolling window)
    df = df.groupby('PKD_Code').apply(lambda group: group.bfill().ffill()).reset_index(drop=True)

    unique_pkds = df['PKD_Code'].unique()
    all_forecasts = []

    print(f"🧠 Generuję stabilne prognozy dla {len(unique_pkds)} branż...")

    # ==========================================
    # 3. PĘTLA PO BRANŻACH
    # ==========================================
    for pkd in unique_pkds:
        train_df = df[df['PKD_Code'] == pkd].copy().sort_values('Date')
        prophet_train = train_df.rename(columns={'Date': 'ds', TARGET_COL: 'y'})

        # --- KONFIGURACJA ZWYCIĘSKA ---
        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            holidays=covid_lockdowns,      # Pamięć o COVID
            changepoint_prior_scale=0.01   # <--- BARDZO SZTYWNY TREND (Klucz do sukcesu)
        )

        # Dodajemy Regressory
        for reg in REGRESSORS:
            if reg in prophet_train.columns:
                m.add_regressor(reg)

        try:
            m.fit(prophet_train)
        except Exception as e:
            print(f"⚠️ Błąd dla branży {pkd}: {e}")
            continue

        # --- TWORZENIE PRZYSZŁOŚCI ---
        future = pd.DataFrame({'ds': TARGET_DATES})
        
        # Wypełnianie przyszłych wartości regressorów (Last Value Carry Forward)
        last_known_row = prophet_train.iloc[-1]
        
        for reg in REGRESSORS:
            if reg in prophet_train.columns:
                future[reg] = last_known_row[reg]

        # Predykcja
        forecast = m.predict(future)

        # Przygotowanie wyniku
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        result['PKD_Code'] = pkd
        
        # Clipping (0-100)
        for col in ['yhat', 'yhat_lower', 'yhat_upper']:
            result[col] = result[col].clip(0, 100).round(1)

        result = result.rename(columns={
            'yhat': 'Predicted_Score',
            'yhat_lower': 'Confidence_Lower',
            'yhat_upper': 'Confidence_Upper',
            'ds': 'Date'
        })

        all_forecasts.append(result)

    # ==========================================
    # 4. ZAPIS
    # ==========================================
    if all_forecasts:
        final_df = pd.concat(all_forecasts, ignore_index=True)
        final_df = final_df.sort_values(['PKD_Code', 'Date'])
        final_df.to_csv(OUTPUT_FILE, index=False)
        
        print("\n" + "="*50)
        print(f"✅ SUKCES! Plik wynikowy: {OUTPUT_FILE}")
        print("="*50)
        print("💡 Te prognozy są teraz spójne z wynikiem Backtestu (MAE 6.88).")
        print("💡 Wykresy w aplikacji będą bardzo gładkie i profesjonalne.")
    else:
        print("❌ Nie udało się wygenerować żadnych prognoz.")

if __name__ == "__main__":
    run_forecaster_final()