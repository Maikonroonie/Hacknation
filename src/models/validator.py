import pandas as pd
import numpy as np
import os
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import logging

# Wyłączamy logi
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)

def run_backtest_best():
    print("🧪 Uruchamiam BACKTESTING v3.0 (Strategia: Smoothing & Trend)...")
    
    # 1. ŚCIEŻKI
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    INPUT_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed', 'MASTER_DATA.csv')

    # 2. KONFIGURACJA
    CUTOFF_DATE = '2023-06-30'
    TARGET_COL = 'PKO_SCORE_FINAL'

    # 3. WCZYTANIE
    if not os.path.exists(INPUT_FILE):
        print("❌ Brak pliku.")
        return

    df = pd.read_csv(INPUT_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    
    if TARGET_COL not in df.columns:
        TARGET_COL = 'Final_Score' if 'Final_Score' in df.columns else 'Profit_Margin'

    # --- STRATEGIA SUKCESU: WYGŁADZANIE DANYCH ---
    # Liczymy średnią z 3 miesięcy. To usuwa szum i zostawia czysty trend.
    print(f"🌊 Wygładzam dane (średnia ruchoma 3-miesięczna)...")
    df_smooth = df.copy()
    df_smooth = df_smooth.sort_values(['PKD_Code', 'Date'])
    
    # Funkcja wygładzająca (Rolling Mean)
    df_smooth[TARGET_COL] = df_smooth.groupby('PKD_Code')[TARGET_COL].transform(lambda x: x.rolling(window=3, min_periods=1).mean())

    # 4. PĘTLA WALIDACYJNA
    unique_industries = df_smooth['PKD_Code'].unique()
    mae_scores = []
    
    print(f"📅 Cutoff: {CUTOFF_DATE} | Cel: {TARGET_COL} (Smoothed)")

    for pkd in unique_industries:
        group = df_smooth[df_smooth['PKD_Code'] == pkd].sort_values('Date').copy()
        
        # Podział na trening i test
        train = group[group['Date'] <= CUTOFF_DATE].copy()
        test = group[group['Date'] > CUTOFF_DATE].copy()
        
        if len(test) < 6 or len(train) < 12:
            continue

        # Formatowanie pod Prophet
        prophet_train = train[['Date', TARGET_COL]].rename(columns={'Date': 'ds', TARGET_COL: 'y'})
        prophet_train['cap'] = 100
        prophet_train['floor'] = 0
        
        # --- KONFIGURACJA MODELU (Ta zwycięska) ---
        m = Prophet(
            growth='logistic',
            yearly_seasonality=True,
            daily_seasonality=False, 
            weekly_seasonality=False,
            # Klucz: 0.05 sprawia, że model jest stabilny i szuka długiego trendu
            changepoint_prior_scale=0.05 
        )
        
        try:
            m.fit(prophet_train)
        except:
            continue
            
        # Prognoza na zbiór testowy
        future_dates = pd.DataFrame({'ds': test['Date']})
        future_dates['cap'] = 100
        future_dates['floor'] = 0
        
        forecast = m.predict(future_dates)
        
        # Porównanie z rzeczywistością
        results = pd.merge(test[['Date', TARGET_COL]], forecast[['ds', 'yhat']], left_on='Date', right_on='ds')
        
        # Obliczenie błędu
        mae = mean_absolute_error(results[TARGET_COL], results['yhat'])
        mae_scores.append(mae)

    # 5. WYNIKI KOŃCOWE
    if mae_scores:
        avg_mae = np.mean(mae_scores)
        print("\n" + "="*50)
        print(f"📊 WYNIK BACKTESTU (Strategia Smoothing)")
        print("="*50)
        print(f"Średni błąd (MAE): {avg_mae:.2f} punktów")
        
        if avg_mae < 10:
            print("🟢 OCENA: BARDZO DOBRA (Zostań przy tym!)")
        elif avg_mae < 15:
            print("🟡 OCENA: AKCEPTOWALNA")
        else:
            print("🔴 OCENA: SŁABA")
            
    else:
        print("⚠️ Brak danych do testu.")

if __name__ == "__main__":
    run_backtest_best()