import pandas as pd
import numpy as np
import os
from prophet import Prophet
import logging

# Wyłączamy logi
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)

def run_forecaster_prophet():
    print("🚀 Uruchamiam AI Forecaster (Celowany Okres)...")
    print("🔮 Cel: Prognozy od 01.06.2024 do 31.05.2026.")

    # ==========================================
    # 1. KONFIGURACJA
    # ==========================================
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    
    INPUT_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'MASTER_DATA.csv')
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'predictions.csv')

    TARGET_COL = 'PKO_SCORE_FINAL'
    
    # DEFINIUJEMY DOKŁADNY ZAKRES DAT DO PROGNOZY
    # 'MS' oznacza pierwszy dzień miesiąca (Month Start)
    TARGET_DATES = pd.date_range(start='2024-06-01', end='2026-05-31', freq='MS')

    # ==========================================
    # 2. WCZYTANIE I PRZYGOTOWANIE DANYCH
    # ==========================================
    if not os.path.exists(INPUT_FILE):
        print(f"❌ BŁĄD: Nie widzę pliku: {INPUT_FILE}")
        return

    print(f"📂 Wczytuję dane z: {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)

    if 'Date' not in df.columns:
        print("❌ BŁĄD: Brak kolumny 'Date'.")
        return
    
    if TARGET_COL not in df.columns:
        # Fallback
        TARGET_COL = 'Final_Score' if 'Final_Score' in df.columns else 'Profit_Margin'

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])

    # --- WYGŁADZANIE DANYCH (Strategia Sukcesu) ---
    print("🌊 Wygładzam dane historyczne (Rolling Mean 3M)...")
    df = df.sort_values(['PKD_Code', 'Date'])
    df[TARGET_COL] = df.groupby('PKD_Code')[TARGET_COL].transform(lambda x: x.rolling(window=3, min_periods=1).mean())

    # ==========================================
    # 3. TRENOWANIE I PROGNOZOWANIE
    # ==========================================
    unique_industries = df['PKD_Code'].unique()
    print(f"🏭 Generuję prognozy dla {len(unique_industries)} branż...")
    
    all_forecasts = []

    for pkd in unique_industries:
        # Bierzemy całą dostępną historię do treningu
        group = df[df['PKD_Code'] == pkd].copy().sort_values('Date')

        if len(group) < 5: continue

        # Formatowanie pod Prophet
        prophet_df = group[['Date', TARGET_COL]].rename(columns={'Date': 'ds', TARGET_COL: 'y'})
        prophet_df['cap'] = 100
        prophet_df['floor'] = 0

        # Model (Ustawienia v3.0 - Stabilne)
        m = Prophet(
            growth='logistic',
            yearly_seasonality=True, 
            daily_seasonality=False, 
            weekly_seasonality=False,
            changepoint_prior_scale=0.05 
        )
        
        try:
            m.fit(prophet_df)
        except:
            continue

        # --- TWORZENIE DAT PRZYSZŁYCH (Pod Twoje wymaganie) ---
        future = pd.DataFrame({'ds': TARGET_DATES})
        future['cap'] = 100
        future['floor'] = 0
        
        # Predykcja
        forecast = m.predict(future)

        # Przygotowanie wyniku
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        result['PKD_Code'] = pkd
        
        # Zaokrąglanie i limity
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
        
        # Ostateczne sortowanie
        final_df = final_df.sort_values(['PKD_Code', 'Date'])

        final_df.to_csv(OUTPUT_FILE, index=False)
        
        print("\n" + "="*60)
        print(f"🏆 SUKCES! Wygenerowano plik: {OUTPUT_FILE}")
        print(f"📅 Zakres dat: {final_df['Date'].min().date()}  ->  {final_df['Date'].max().date()}")
        print("="*60)
        print(final_df.head())
    else:
        print("⚠️ Nie udało się wygenerować prognoz.")

if __name__ == "__main__":
    run_forecaster_prophet()