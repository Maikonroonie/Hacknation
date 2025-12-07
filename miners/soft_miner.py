import pandas as pd
import requests
import os
import io
import numpy as np
from datetime import datetime


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) 

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Hacknation",'my-react-app','public', "data", "processed")
OUTPUT_FILE = "soft_data.csv"

FRED_OIL_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU"

PKD_LIST = [
    "PKD_01", "PKD_10", "PKD_16", "PKD_23", "PKD_24", 
    "PKD_29", "PKD_31", "PKD_35", "PKD_41", "PKD_46", 
    "PKD_47", "PKD_49", "PKD_55", "PKD_62", "PKD_68"
]

risk_sensitivity = {
        'PKD_41': {'wibor': 1.0, 'energy': 0.3}, # Budowlanka
        'PKD_68': {'wibor': 1.0, 'energy': 0.2}, # Nieruchomości
        'PKD_24': {'wibor': 0.4, 'energy': 1.0}, # Metale
        'PKD_35': {'wibor': 0.3, 'energy': -0.5},# Energetyka
        'PKD_49': {'wibor': 0.5, 'energy': 0.9}, # Transport
        'PKD_10': {'wibor': 0.4, 'energy': 0.6}, # Spożywka
        'PKD_62': {'wibor': 0.1, 'energy': 0.1}, # IT
        'default': {'wibor': 0.5, 'energy': 0.5}
    }
def fetch_oil_history():
    try:
        response = requests.get(FRED_OIL_URL, timeout=10)
        response.raise_for_status()
        content = response.content.decode('utf-8')
        
        df = pd.read_csv(io.StringIO(content))
        df.columns = ['Data', 'Oil_USD']
        
        df = df[df['Oil_USD'] != '.']
        df['Oil_USD'] = pd.to_numeric(df['Oil_USD'])
        df['Data'] = pd.to_datetime(df['Data'])
        
        return df
    except Exception as e:
        dates = pd.date_range(start='2020-01-01', end=datetime.now(), freq='D')
        return pd.DataFrame({'Data': dates, 'Oil_USD': 65.0})
    

def fetch_nbp_history(table, code, column_name, start_year=2020):
    all_data = []
    current_year = datetime.now().year
    
    for year in range(start_year, current_year + 1):
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        if year == current_year:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"http://api.nbp.pl/api/cenyzlota/{start_date}/{end_date}/?format=json" if code == 'gold' \
              else f"http://api.nbp.pl/api/exchangerates/rates/{table}/{code}/{start_date}/{end_date}/?format=json"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Prosta pętla tylko po kursach walut
                for rate in data['rates']:
                    all_data.append({
                        'Data': rate['effectiveDate'], 
                        column_name: rate['mid']
                    })
        except: pass         
    return pd.DataFrame(all_data)

def generate_interest_rates():
    rates_history = [
        ('2020-03-18', 1.00), ('2020-05-29', 0.10),
        ('2021-10-07', 0.50), ('2022-01-05', 2.25), ('2022-09-08', 6.75),
        ('2023-10-05', 5.75)
    ]
    df = pd.DataFrame(rates_history, columns=['Data', 'Stopa_Ref'])
    df['Data'] = pd.to_datetime(df['Data'])
    
    full_range = pd.date_range(start='2020-01-01', end=datetime.now(), freq='D')
    df = df.set_index('Data').reindex(full_range).ffill().reset_index()
    df.rename(columns={'index': 'Data'}, inplace=True)
    df['Stopa_Ref'] = df['Stopa_Ref'].bfill()
    return df


def calculate_metrics(master_df, pkd_list):
    df = master_df.copy()
    
    if 'Oil_USD' in df.columns:
        df['Cena_Paliwa'] = df['Oil_USD'] * df['Kurs_USD']
    else:
        df['Cena_Paliwa'] = 65.0 * df['Kurs_USD']
    df['Delta_WIBOR'] = df['Stopa_Ref'].diff(4).fillna(0)
    df['Delta_Energy'] = df['Cena_Paliwa'].diff(4).fillna(0)

    final_dfs = []

    for pkd in pkd_list:
        weights = risk_sensitivity.get(pkd, risk_sensitivity['default'])
        w_wibor = weights.get('wibor', 0.5)
        w_energy = weights.get('energy', 0.5)      

        sector_df = df.copy()
        sector_df['Kod_PKD'] = pkd
 
        risk_impulse = (sector_df['Delta_WIBOR'] * w_wibor) + (sector_df['Delta_Energy'] * w_energy)
        
        sector_df['News_Sentiment'] = (-1 * risk_impulse / 5).clip(-1, 1)

        raw_trend = 50 + (risk_impulse * 5)
        
        noise = np.random.normal(0, 4, len(sector_df))
        raw_trend = raw_trend + noise
        
        sector_df['Google_Trend_Score'] = raw_trend.rolling(window=4, min_periods=1).mean()
        
        sector_df['Google_Trend_Score'] = sector_df['Google_Trend_Score'].clip(10, 100)
        sector_df['WIBOR'] = sector_df['Stopa_Ref']
        
        cols = ['Data', 'Kod_PKD', 'Google_Trend_Score', 'WIBOR', 'Cena_Paliwa']
        final_dfs.append(sector_df[cols])

    return pd.concat(final_dfs)

def main():
    if not os.path.exists(OUTPUT_DIR):
        try: os.makedirs(OUTPUT_DIR)
        except: pass

    oil_df = fetch_oil_history()
    usd_df = fetch_nbp_history('A', 'USD', 'Kurs_USD', start_year=2020)
    rates_df = generate_interest_rates()

    if usd_df.empty or oil_df.empty:
        return

    usd_df['Data'] = pd.to_datetime(usd_df['Data'])
    
    master_df = pd.merge(usd_df, rates_df, on='Data', how='left')
    master_df = pd.merge(master_df, oil_df, on='Data', how='left') 
    
    master_df = master_df.sort_values('Data').ffill().dropna()

    master_df = master_df.set_index('Data').resample('W').mean().reset_index()

    final_df = calculate_metrics(master_df, PKD_LIST)
    
    final_df = final_df.sort_values(by=['Data', 'Kod_PKD'])

    full_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    final_df.to_csv(full_path, index=False)

if __name__ == "__main__":
    main()