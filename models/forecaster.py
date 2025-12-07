import pandas as pd
import numpy as np
import os
from prophet import Prophet
import logging

logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)

def run_forecaster_final():
    print("ruchamiam AI Forecaster MULTI-TARGET (Wersja 'DIAMOND')...")
    print("Konfiguracja: Przewidywanie Score + 4 Rankingów Strategicznych")

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) 
    
    INPUT_FILE = os.path.join(PROJECT_ROOT, 'my-react-app', 'public', 'data', 'processed', 'MASTER_DATA.csv')
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'my-react-app', 'public', 'data', 'processed', 'predictions.csv')

    print(f"📂 Szukam pliku w: {INPUT_FILE}")

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
    TARGET_DATES = pd.date_range(start='2024-07-01', end='2026-06-30', freq='MS')

    if not os.path.exists(INPUT_FILE):
        print(f"Błąd: Brak pliku {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    
    print("Wygładzam dane historyczne (wszystkie wskaźniki)...")
    df = df.sort_values(['PKD_Code', 'Date'])

    cols_to_smooth = TARGETS + [r for r in REGRESSORS if r in df.columns]
    
    for col in cols_to_smooth:
        if col in df.columns:
            df[col] = df.groupby('PKD_Code')[col].transform(
                lambda x: x.rolling(window=6, min_periods=1).mean()
            )

    df = df.groupby('PKD_Code').apply(lambda group: group.bfill().ffill()).reset_index(drop=True)

    unique_pkds = df['PKD_Code'].unique()
    all_forecasts = []

    print(f" Generuję prognozy dla {len(unique_pkds)} branż...")

    for pkd in unique_pkds:
        pkd_forecast_df = pd.DataFrame({'Date': TARGET_DATES})
        pkd_forecast_df['PKD_Code'] = pkd
        
        train_df_base = df[df['PKD_Code'] == pkd].copy().sort_values('Date')

        for target_col in TARGETS:
            if target_col not in train_df_base.columns:
                continue

            prophet_train = train_df_base.rename(columns={'Date': 'ds', target_col: 'y'})

            m = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                holidays=covid_lockdowns,
                changepoint_prior_scale=0.01 
            )

            for reg in REGRESSORS:
                if reg in prophet_train.columns:
                    m.add_regressor(reg)

            try:
                m.fit(prophet_train)
            except Exception:
                continue

            future = pd.DataFrame({'ds': TARGET_DATES})
            last_known_row = prophet_train.iloc[-1]
            for reg in REGRESSORS:
                if reg in prophet_train.columns:
                    future[reg] = last_known_row[reg]

            forecast = m.predict(future)
            
            suffix = "_Predicted"
            
            if target_col == 'PKO_SCORE_FINAL':
                pkd_forecast_df['Predicted_Score'] = forecast['yhat'].clip(0, 100).round(1).values
                pkd_forecast_df['Confidence_Lower'] = forecast['yhat_lower'].clip(0, 100).round(1).values
                pkd_forecast_df['Confidence_Upper'] = forecast['yhat_upper'].clip(0, 100).round(1).values
            else:
                clean_name = target_col + suffix
                pkd_forecast_df[clean_name] = forecast['yhat'].clip(0, 100).round(1).values

        all_forecasts.append(pkd_forecast_df)

    if all_forecasts:
        final_df = pd.concat(all_forecasts, ignore_index=True)
        final_df = final_df.sort_values(['PKD_Code', 'Date'])

        desired_order = [
            'Date', 
            'Predicted_Score', 
            'Confidence_Lower', 
            'Confidence_Upper', 
            'PKD_Code', 
            'Rank_Growth_Predicted', 
            'Rank_Slowdown_Predicted', 
            'Rank_Loan_Needs_Predicted', 
            'Rank_Trend_Signal_Predicted'
        ]
        
        cols_to_save = [c for c in desired_order if c in final_df.columns]
        
        remaining = [c for c in final_df.columns if c not in cols_to_save]
        
        final_df = final_df[cols_to_save + remaining]
        
        final_df.to_csv(OUTPUT_FILE, index=False)
        
        print("\n" + "="*50)
        print(f"SUKCES! Plik wynikowy: {OUTPUT_FILE}")
        print("="*50)
        print("Struktura pliku (pierwsze 5 kolumn):")
        print(final_df.columns.tolist()[:5])
    else:
        print(" Nie udało się wygenerować prognoz.")

if __name__ == "__main__":
    run_forecaster_final()