import pandas as pd
import numpy as np
import os
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging


logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
logging.getLogger('prophet').setLevel(logging.WARNING)


def calculate_metrics(y_true, y_pred, y_train_history):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    r2 = r2_score(y_true, y_pred)
    
    smape = 100/len(y_true) * np.sum(2 * np.abs(y_pred - y_true) / (np.abs(y_true) + np.abs(y_pred) + 1e-10))

    if len(y_true) > 1:
        diff_true = np.diff(y_true)
        diff_pred = np.diff(y_pred)
        da = np.mean(np.sign(diff_true) == np.sign(diff_pred)) * 100 if len(diff_true) > 0 else 0.0
    else:
        da = 0.0

    n = len(y_train_history)
    d = np.abs(np.diff(y_train_history)).sum() / (n - 1)
    mase = mae / d if d != 0 else np.inf

    var_true = np.var(y_true)
    var_pred = np.var(y_pred)
    vr = var_pred / var_true if var_true != 0 else 0.0
    
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape, 'R2': r2, 'SMAPE': smape, 'DA': da, 'MASE': mase, 'VR': vr}


def run_validator_multi_target():
    print("Uruchamiam PEŁNY AUDYT MODELU (8 Metryk)...")

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    
    INPUT_FILE = os.path.join(PROJECT_ROOT, 'my-react-app', 'public', 'data', 'processed', 'MASTER_DATA.csv')

    CUTOFF_DATE = '2023-06-30'
    
    TARGETS = [
        'PKO_SCORE_FINAL', 'Rank_Growth', 'Rank_Slowdown', 'Rank_Loan_Needs', 'Rank_Trend_Signal'
    ]
    
    REGRESSORS = ['WIBOR', 'Google_Trends', 'Energy_Price']

    covid_lockdowns = pd.DataFrame([
        {'holiday': 'lockdown_1', 'ds': '2020-03-01', 'lower_window': 0, 'upper_window': 2},
        {'holiday': 'lockdown_2', 'ds': '2020-10-01', 'lower_window': 0, 'upper_window': 3},
        {'holiday': 'lockdown_3', 'ds': '2021-03-01', 'lower_window': 0, 'upper_window': 1},
    ])
    covid_lockdowns['ds'] = pd.to_datetime(covid_lockdowns['ds'])

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Brak pliku {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    df['Date'] = pd.to_datetime(df['Date'])

    print("🌊 Wygładzam dane historyczne (Rolling Mean 6M)...")
    df_smooth = df.copy().sort_values(['PKD_Code', 'Date'])
    cols_to_smooth = TARGETS + [r for r in REGRESSORS if r in df.columns]
    
    for col in cols_to_smooth:
        if col in df_smooth.columns:
            df_smooth[col] = df_smooth.groupby('PKD_Code')[col].transform(
                lambda x: x.rolling(window=6, min_periods=1).mean()
            )

    unique_industries = df_smooth['PKD_Code'].unique()
    final_metrics = {}

    print(f"Data Splitu: {CUTOFF_DATE}")
    print("-" * 120)

    for target in TARGETS:
        if target not in df_smooth.columns: continue
            
        print(f"🚀 Testuję: {target}...")
        all_y_true = []
        all_y_pred = []
        all_train_history = []
        
        for pkd in unique_industries:
            group = df_smooth[df_smooth['PKD_Code'] == pkd].sort_values('Date').copy()
            
            train = group[group['Date'] <= CUTOFF_DATE].copy()
            test = group[group['Date'] > CUTOFF_DATE].copy()
            
            if len(test) < 6 or len(train) < 12: continue

            all_train_history.extend(train[target].values)
            
            prophet_train = train.rename(columns={'Date': 'ds', target: 'y'})

            m = Prophet(
                yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False,
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

                soft_clipped = forecast['yhat'].values.clip(0, 100)
                
                all_y_true.extend(test[target].values)
                all_y_pred.extend(soft_clipped)
                
            except Exception:
                continue

        if all_y_true:
            m = calculate_metrics(all_y_true, all_y_pred, all_train_history)
            final_metrics[target] = m
            print(f"   -> MAE: {m['MAE']:.2f} | MASE: {m['MASE']:.2f} | VR: {m['VR']:.2f}")

    print("\n" + "="*120)
    print(f"RAPORT KOŃCOWY (AUDYT 8 METRYK)")
    print("="*120)
    print(f"{'WSKAŹNIK':<22} | {'MAE':<6} | {'RMSE':<6} | {'MAPE':<6} | {'R2':<7} | {'SMAPE':<6} | {'DA %':<6} | {'MASE':<6} | {'VR':<6} | {'OCENA'}")
    print("-" * 120)
    
    for target, m in final_metrics.items():
        if not m: continue
        rating = "WYBITNA" if m['MAE'] < 10 and m['MASE'] < 1 else "BARDZO DOBRA" if m['MAE'] < 15 and m['MASE'] < 1.5 else "DOBRA"
        r2_str = f"{m['R2']:.2f}"
        print(f"{target:<22} | {m['MAE']:<6.2f} | {m['RMSE']:<6.2f} | {m['MAPE']:<6.1f} | {r2_str:<7} | {m['SMAPE']:<6.1f} | {m['DA']:<6.1f} | {m['MASE']:<6.2f} | {m['VR']:<6.2f} | {rating}")
    
    print("="*120)

if __name__ == "__main__":
    run_validator_multi_target()