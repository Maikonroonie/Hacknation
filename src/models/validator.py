import pandas as pd
import numpy as np
import os
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import logging

# Wyłączamy logi
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)

def run_hybrid_backtest_aggressive():
    print("🧪 Uruchamiam BACKTEST AGRESYWNY (Strong Smoothing + Rigid Trend)...")
    
    # ==========================================
    # 1. KONFIGURACJA
    # ==========================================
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    INPUT_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'MASTER_DATA.csv')

    CUTOFF_DATE = '2023-06-30'
    TARGET_COL = 'PKO_SCORE_FINAL'
    
    REGRESSORS = ['WIBOR', 'Google_Trends', 'Energy_Price']

    covid_lockdowns = pd.DataFrame([
        {'holiday': 'lockdown_1', 'ds': '2020-03-01', 'lower_window': 0, 'upper_window': 2},
        {'holiday': 'lockdown_2', 'ds': '2020-10-01', 'lower_window': 0, 'upper_window': 3},
        {'holiday': 'lockdown_3', 'ds': '2021-03-01', 'lower_window': 0, 'upper_window': 1},
    ])
    covid_lockdowns['ds'] = pd.to_datetime(covid_lockdowns['ds'])

    # ==========================================
    # 2. WCZYTANIE I PRZYGOTOWANIE
    # ==========================================
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Brak pliku {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # --- ZMIANA 1: MOCNIEJSZE WYGŁADZANIE (WINDOW = 6) ---
    # Patrzymy na trend półroczny. To eliminuje większość szumu makroekonomicznego.
    print("🌊 Wygładzam dane agresywnie (Rolling Mean 6M)...")
    
    df_smooth = df.copy().sort_values(['PKD_Code', 'Date'])
    
    cols_to_smooth = [TARGET_COL] + [r for r in REGRESSORS if r in df.columns]
    
    for col in cols_to_smooth:
        df_smooth[col] = df_smooth.groupby('PKD_Code')[col].transform(
            lambda x: x.rolling(window=6, min_periods=1).mean()
        )

    unique_industries = df_smooth['PKD_Code'].unique()
    mae_scores = []

    print(f"📅 Data Splitu: {CUTOFF_DATE}")
    
    # ==========================================
    # 3. PĘTLA WALIDACYJNA
    # ==========================================
    for pkd in unique_industries:
        group = df_smooth[df_smooth['PKD_Code'] == pkd].sort_values('Date').copy()
        
        train = group[group['Date'] <= CUTOFF_DATE].copy()
        test = group[group['Date'] > CUTOFF_DATE].copy()
        
        if len(test) < 6 or len(train) < 12:
            continue

        prophet_train = train.rename(columns={'Date': 'ds', TARGET_COL: 'y'})
        
        # --- ZMIANA 2: BARDZO SZTYWNY TREND (0.01) ---
        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            holidays=covid_lockdowns,
            changepoint_prior_scale=0.01  # <--- Bardzo konserwatywny (bezpieczny)
        )
        
        valid_regressors = []
        for reg in REGRESSORS:
            if reg in prophet_train.columns and not prophet_train[reg].isnull().all():
                m.add_regressor(reg)
                valid_regressors.append(reg)
        
        try:
            m.fit(prophet_train)
        except Exception:
            continue
            
        future = test[['Date'] + valid_regressors].rename(columns={'Date': 'ds'})
        forecast = m.predict(future)
        
        results = pd.merge(test[['Date', TARGET_COL]], forecast[['ds', 'yhat']], left_on='Date', right_on='ds')
        
        mae = mean_absolute_error(results[TARGET_COL], results['yhat'])
        mae_scores.append(mae)

    # ==========================================
    # 4. WYNIK
    # ==========================================
    if mae_scores:
        avg_mae = np.mean(mae_scores)
        print("\n" + "="*50)
        print(f"📊 WYNIK BACKTESTU (Strategy: Long-Term Trend)")
        print("="*50)
        print(f"Średni błąd (MAE): {avg_mae:.2f} punktów")
        
        if avg_mae < 10:
            print("🟢 OCENA: BARDZO DOBRA (Idealna pod bankowość)")
        else:
            print("🟡 OCENA: AKCEPTOWALNA")
    else:
        print("⚠️ Brak danych.")

if __name__ == "__main__":
    run_hybrid_backtest_aggressive()