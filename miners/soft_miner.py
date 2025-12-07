import pandas as pd
import requests
import os
import io
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import warnings

# -------------------- Ścieżki i konfiguracja --------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) 
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Hacknation",'my-react-app','public', "data", "processed")
OUTPUT_FILE = "soft_data_gdelt.csv"

FRED_OIL_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU"

PKD_KEYWORDS = {
    "PKD_01": ["rolnictwo", "plony", "ceny zboża"], 
    "PKD_10": ["spożywczy", "przetwórstwo", "ceny żywności"], 
    "PKD_16": ["drewno", "tartak", "meble"], 
    "PKD_23": ["ceramika", "cement", "szkło budowlane"], 
    "PKD_24": ["stal", "metalurgia", "ceny metali"], 
    "PKD_29": ["motoryzacja", "części samochodowe"], 
    "PKD_31": ["producent mebli", "sprzedaż mebli"], 
    "PKD_35": ["energetyka", "cena gazu", "węgiel", "OZE"], 
    "PKD_41": ["budowa", "deweloper", "nowe mieszkania", "materiały budowlane"], 
    "PKD_46": ["handel hurtowy", "dystrybucja"], 
    "PKD_47": ["handel detaliczny", "sklep internetowy"], 
    "PKD_49": ["transport", "spedycja", "logistyka"], 
    "PKD_55": ["hotelarstwo", "turystyka", "noclegi"], 
    "PKD_62": ["usługi IT", "programista", "sztuczna inteligencja"], 
    "PKD_68": ["nieruchomości", "wynajem", "rynek wtórny"]
}

# -------------------- Funkcje pomocnicze --------------------

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
    except Exception:
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
                for rate in data['rates']:
                    all_data.append({
                        'Data': rate['effectiveDate'], 
                        column_name: rate['mid']
                    })
        except: 
            pass         
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

# -------------------- Funkcje GDELT --------------------

def fetch_gdelt_for_pkd(pkd_code, keywords, date_range):
    from gdelt import gdelt
    import pandas as pd
    gd = gdelt(version=2)
    try:
        results = gd.Search(date_range, table="gkg", output="df", coverage=False)
    except:
        return pd.DataFrame()
    if results is None or results.empty:
        return pd.DataFrame()

    results["match"] = results["V2Themes"].fillna("").apply(
        lambda x: any(k.lower() in x.lower() for k in keywords)
    )
    filtered = results[results["match"]].copy()
    if filtered.empty:
        return pd.DataFrame()

    filtered["Kod_PKD"] = pkd_code

    # obsługa różnych formatów dat
    def parse_date(x):
        x = str(x)
        if len(x) == 8:
            return pd.to_datetime(x, format="%Y%m%d")
        elif len(x) == 14:
            return pd.to_datetime(x, format="%Y%m%d%H%M%S")
        else:
            return pd.NaT
    if "DATEADDED" in filtered.columns:
        filtered["Data"] = pd.to_datetime(filtered["DATEADDED"], format="%Y%m%d%H%M%S", errors='coerce')
    elif "DATE" in filtered.columns:
        filtered["Data"] = filtered["DATE"].apply(parse_date)
    else:
        filtered["Data"] = pd.NaT

    # V2Tone na float
    filtered['V2Tone'] = pd.to_numeric(filtered['V2Tone'], errors='coerce')

    return filtered

def fetch_gdelt_sentiment(PKD_KEYWORDS, days_back=60):
    from datetime import datetime, timedelta
    import pandas as pd

    warnings.filterwarnings("ignore", category=UserWarning)

    end_date = datetime.utcnow() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)

    # dzielimy na batch 7-dniowe
    batch_size = 7
    date_batches = []
    current_start = start_date
    while current_start <= end_date:
        current_end = min(current_start + timedelta(days=batch_size - 1), end_date)
        date_batches.append(pd.date_range(current_start, current_end).strftime('%Y%m%d').tolist())
        current_start = current_end + timedelta(days=1)

    all_results = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        for batch in date_batches:
            futures = [executor.submit(fetch_gdelt_for_pkd, pkd, kws, batch)
                       for pkd, kws in PKD_KEYWORDS.items()]
            for future in futures:
                df = future.result()
                if not df.empty:
                    all_results.append(df)

    if not all_results:
        return pd.DataFrame()

    final_df = pd.concat(all_results, ignore_index=True)
    final_df = final_df[["Kod_PKD", "Data", "GKGRECORDID", "DocumentIdentifier", "V2Tone", "V2Themes"]]
    final_df.rename(columns={'V2Tone': 'Google_Trend_Score'}, inplace=True)

    return final_df

# -------------------- MAIN --------------------

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    oil_df = fetch_oil_history()
    usd_df = fetch_nbp_history('A', 'USD', 'Kurs_USD', start_year=2020)
    rates_df = generate_interest_rates()

    if usd_df.empty or oil_df.empty:
        return

    usd_df['Data'] = pd.to_datetime(usd_df['Data'])
    master_df = pd.merge(usd_df, rates_df, on='Data', how='left')
    master_df = pd.merge(master_df, oil_df, on='Data', how='left') 
    master_df = master_df.sort_values('Data').ffill().dropna()
    master_weekly_df = master_df.set_index('Data').resample('W').mean().reset_index()

    sentiment_df = fetch_gdelt_sentiment(PKD_KEYWORDS, days_back=60)
    if sentiment_df.empty:
        return

    sentiment_weekly_df = sentiment_df.set_index('Data').groupby('Kod_PKD').resample('W')['Google_Trend_Score'].mean().reset_index()

    final_df = pd.merge(
        sentiment_weekly_df,
        master_weekly_df[['Data', 'Stopa_Ref', 'Kurs_USD', 'Oil_USD']],
        on='Data',
        how='left'
    ).dropna()

    final_df['WIBOR'] = final_df['Stopa_Ref']
    final_df['Cena_Paliwa'] = final_df['Oil_USD'] * final_df['Kurs_USD']

    cols = ['Data', 'Kod_PKD', 'Google_Trend_Score', 'WIBOR', 'Cena_Paliwa']
    final_df = final_df[cols]

    full_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    final_df.to_csv(full_path, index=False)
    print(f"Dane zapisane do {full_path}")

if __name__ == "__main__":
    main()
