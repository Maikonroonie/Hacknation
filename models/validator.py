import pandas as pd
import numpy as np
import os
from prophet import Prophet
from sklearn.metrics import mean_absolute_error
import logging

# Wyłączamy logi bibliotek, żeby było czytelnie
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)

def run_validator_multi_target():
    print("🧪 Uruchamiam BACKTEST MULTI-TARGET (Wersja 'DIAMOND')...")
    print("Sprawdzam skuteczność modelu dla KAŻDEGO wskaźnika z osobna.")
    
    # ==========================================
    # 1. KONFIGURACJA
    # ==========================================
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Wyjście z 'models' do 'Hacknation'
    
    INPUT_FILE = os.path.join(PROJECT_ROOT, 'my-react-app', 'public', 'data', 'processed', 'MASTER_DATA.csv')

    CUTOFF_DATE = '2023-06-30'
    
    # Lista wskaźników do sprawdzenia
    TARGETS = [
        'PKO_SCORE_FINAL', 
        'Rank_Growth', 
        'Rank_Slowdown', 
        'Rank_Loan_Needs', 
        'Rank_Trend_Signal'
    ]
    
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
    
    print("🌊 Wygładzam dane historyczne (Rolling Mean 6M)...")
    
    df_smooth = df.copy().sort_values(['PKD_Code', 'Date'])
    
    # Wygładzamy WSZYSTKIE cele i regresory
    cols_to_smooth = TARGETS + [r for r in REGRESSORS if r in df.columns]
    
    for col in cols_to_smooth:
        if col in df_smooth.columns:
            df_smooth[col] = df_smooth.groupby('PKD_Code')[col].transform(
                lambda x: x.rolling(window=6, min_periods=1).mean()
            )

    unique_industries = df_smooth['PKD_Code'].unique()
    
    print(f"📅 Data Splitu: {CUTOFF_DATE}")
    print(f"🔍 Testuję {len(TARGETS)} wskaźników na {len(unique_industries)} branżach...")
    print("-" * 60)

    # Słownik na wyniki końcowe
    final_results = {}

    # ==========================================
    # 3. GŁÓWNA PĘTLA PO WSKAŹNIKACH
    # ==========================================
    for target in TARGETS:
        if target not in df_smooth.columns:
            print(f"⚠️ Pomijam {target} (brak kolumny)")
            continue
            
        print(f"🚀 Testuję wskaźnik: {target}...")
        mae_scores = []
        
        # Pętla po branżach dla danego wskaźnika
        for pkd in unique_industries:
            group = df_smooth[df_smooth['PKD_Code'] == pkd].sort_values('Date').copy()
            
            train = group[group['Date'] <= CUTOFF_DATE].copy()
            test = group[group['Date'] > CUTOFF_DATE].copy()
            
            if len(test) < 6 or len(train) < 12:
                continue

            prophet_train = train.rename(columns={'Date': 'ds', target: 'y'})
            
            # --- KONFIGURACJA MODELU (Ta sama co w forecasterze) ---
            m = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                holidays=covid_lockdowns,
                changepoint_prior_scale=0.01
            )
            
            valid_regressors = []
            for reg in REGRESSORS:
                if reg in prophet_train.columns and not prophet_train[reg].isnull().all():
                    m.add_regressor(reg)
                    valid_regressors.append(reg)
            
            try:
                m.fit(prophet_train)
                
                future = test[['Date'] + valid_regressors].rename(columns={'Date': 'ds'})
                forecast = m.predict(future)
                
                results = pd.merge(test[['Date', target]], forecast[['ds', 'yhat']], left_on='Date', right_on='ds')
                
                mae = mean_absolute_error(results[target], results['yhat'])
                mae_scores.append(mae)
            except Exception:
                continue

        # Zapisujemy średni wynik dla tego wskaźnika
        if mae_scores:
            avg_mae = np.mean(mae_scores)
            final_results[target] = avg_mae
            print(f"   -> Średnie MAE: {avg_mae:.2f}")
        else:
            print(f"   -> Brak wyników.")

    # ==========================================
    # 4. RAPORT KOŃCOWY
    # ==========================================
    print("\n" + "="*60)
    print(f"📊 RAPORT SKUTECZNOŚCI MODELI (BACKTEST)")
    print("="*60)
    print(f"{'WSKAŹNIK':<25} | {'MAE (Błąd)':<12} | {'OCENA'}")
    print("-" * 60)
    
    for target, mae in final_results.items():
        # Ocena opisowa w zależności od wyniku
        if mae < 10:
            rating = "🟢 WYBITNA"
        elif mae < 15:
            rating = "🟢 BARDZO DOBRA"
        elif mae < 20:
            rating = "🟡 DOBRA"
        else:
            rating = "🔴 ŚREDNIA"
            
        print(f"{target:<25} | {mae:<12.2f} | {rating}")
    
    print("="*60)
    print("💡 Interpretacja: MAE < 10 oznacza błąd prognozy poniżej 10 punktów (na skali 100).")

if __name__ == "__main__":
    run_validator_multi_target()