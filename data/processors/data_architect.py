import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

# --- KONFIGURACJA ---
# Ustaw na False, gdy koledzy dostarczą prawdziwe pliki csv do folderu data/processed/
USE_MOCK_DATA = True 

# Ścieżki (zakładając, że uruchamiasz skrypt z głównego katalogu projektu)
PATH_HARD = 'data/processed/hard_data.csv'
PATH_SOFT = 'data/processed/soft_data.csv'
PATH_OUTPUT = 'data/processed/MASTER_DATA.csv'

# Lista 15 kluczowych branż (z Twojego obrazka)
KEY_INDUSTRIES = [
    '01', '10', '16', '23', '24', '29', '31', '35', # Produkcyjne
    '41', '68',                                     # Budowlane
    '46', '47', '49', '55', '62'                    # Usługowe
]

def generate_mock_data():
    """Generuje sztuczne dane, żebyś mógł pracować zanim Minerzy skończą."""
    print("⚠️ GENEROWANIE MOCK DATA (Sztuczne dane)...")
    dates = pd.date_range(start='2021-01-01', periods=48, freq='MS')
    
    hard_data = []
    soft_data = []
    
    for pkd in KEY_INDUSTRIES:
        base_revenue = np.random.randint(500, 2000)
        base_trend = np.random.randint(20, 80)
        
        for date in dates:
            # Hard Data (Finanse)
            rev = base_revenue + (np.sin(date.month) * 100) + np.random.randint(-50, 50)
            profit = rev * np.random.uniform(0.05, 0.15)
            hard_data.append([date, pkd, rev, profit])
            
            # Soft Data (Makro + Google)
            g_trend = base_trend + np.random.randint(-10, 10)
            wibor = 5.85 if date.year > 2021 else 0.5
            energy = 100 + (date.year - 2020) * 20
            soft_data.append([date, pkd, g_trend, wibor, energy])
            
    df_hard = pd.DataFrame(hard_data, columns=['Date', 'PKD_Code', 'Revenue', 'Profit'])
    df_soft = pd.DataFrame(soft_data, columns=['Date', 'PKD_Code', 'Google_Trends', 'WIBOR', 'Energy_Price'])
    
    return df_hard, df_soft

def load_data():
    if USE_MOCK_DATA:
        return generate_mock_data()
    
    if not os.path.exists(PATH_HARD) or not os.path.exists(PATH_SOFT):
        raise FileNotFoundError("Brakuje plików CSV! Ustaw USE_MOCK_DATA = True lub poproś Minerów o dane.")
        
    df_hard = pd.read_csv(PATH_HARD, parse_dates=['Date'], dtype={'PKD_Code': str})
    df_soft = pd.read_csv(PATH_SOFT, parse_dates=['Date'], dtype={'PKD_Code': str})
    return df_hard, df_soft

def calculate_index(df):
    print("⚙️ Przeliczanie Algorytmu PKO FutureIndex...")
    
    # 1. Feature Engineering (Wskaźniki dynamiki)
    # Sortujemy, żeby liczyć zmiany miesiąc do miesiąca
    df = df.sort_values(['PKD_Code', 'Date'])
    
    # Dynamika Przychodów (R/R - rok do roku)
    df['Rev_Growth_YoY'] = df.groupby('PKD_Code')['Revenue'].pct_change(periods=12).fillna(0)
    
    # Rentowność (Zysk / Przychód)
    df['Profit_Margin'] = df['Profit'] / df['Revenue']
    df['Profit_Margin'] = df['Profit_Margin'].fillna(0)

    # 2. Mapowanie Ryzyka (Expert Knowledge z Twojego obrazka)
    # Określamy, kogo boli WIBOR (kredyty), a kogo ENERGIA
    risk_sensitivity = {
        '41': {'wibor': 1.0, 'energy': 0.3}, # Budowlanka - boli WIBOR
        '68': {'wibor': 1.0, 'energy': 0.2}, # Nieruchomości - boli WIBOR
        '24': {'wibor': 0.4, 'energy': 1.0}, # Metale - boli prąd!
        '35': {'wibor': 0.3, 'energy': -0.5},# Energetyka - jak prąd drożeje, oni zarabiają (ujemne ryzyko)
        '62': {'wibor': 0.1, 'energy': 0.1}, # IT - luz
        '49': {'wibor': 0.5, 'energy': 0.8}, # Transport - paliwo/energia
    }
    
    # Funkcja pomocnicza do ryzyka
    def get_risk_factor(pkd, factor_type):
        return risk_sensitivity.get(pkd, {'wibor': 0.5, 'energy': 0.5}).get(factor_type, 0.5)

    df['Risk_WIBOR_Weight'] = df['PKD_Code'].apply(lambda x: get_risk_factor(x, 'wibor'))
    df['Risk_Energy_Weight'] = df['PKD_Code'].apply(lambda x: get_risk_factor(x, 'energy'))

    # 3. Normalizacja (Skalowanie wszystkiego do 0-100)
    scaler = MinMaxScaler(feature_range=(0, 100))
    
    # Skalujemy dane wejściowe
    cols_to_norm = ['Rev_Growth_YoY', 'Profit_Margin', 'Google_Trends', 'WIBOR', 'Energy_Price']
    for col in cols_to_norm:
        # Normalizacja globalna (żeby porównywać branże między sobą)
        df[f'Norm_{col}'] = scaler.fit_transform(df[[col]])

    # 4. FINALNY WZÓR (ALGORITHM)
    # Indeks = (Kondycja * 0.2) + (Rozwój * 0.3) + (Sentyment * 0.3) - (Ryzyko * 0.2)
    
    # Obliczamy Składnik Ryzyka (WIBOR + Energia ważone wrażliwością)
    df['Total_Risk_Score'] = (
        (df['Norm_WIBOR'] * df['Risk_WIBOR_Weight']) + 
        (df['Norm_Energy_Price'] * df['Risk_Energy_Weight'])
    )
    # Normalizujemy ryzyko znowu do 0-100
    df['Norm_Total_Risk'] = scaler.fit_transform(df[['Total_Risk_Score']])

    # GŁÓWNE RÓWNANIE
    df['PKO_SCORE'] = (
        (0.2 * df['Norm_Profit_Margin']) +  # KONDYCJA
        (0.3 * df['Norm_Rev_Growth_YoY']) + # ROZWÓJ
        (0.3 * df['Norm_Google_Trends']) -  # SENTYMENT
        (0.2 * df['Norm_Total_Risk'])       # RYZYKO
    )

    # Przeskaluj wynik końcowy na ładne 0-100 pkt
    df['PKO_SCORE_FINAL'] = scaler.fit_transform(df[['PKO_SCORE']])
    
    return df

def main():
    # 1. Wczytaj
    df_hard, df_soft = load_data()
    
    # 2. Merge
    print(f"📦 Łączenie danych... Hard: {df_hard.shape}, Soft: {df_soft.shape}")
    master_df = pd.merge(df_hard, df_soft, on=['Date', 'PKD_Code'], how='inner')
    
    # 3. Policz Indeks
    master_df = calculate_index(master_df)
    
    # 4. Zapisz
    # Upewnij się, że folder istnieje
    os.makedirs(os.path.dirname(PATH_OUTPUT), exist_ok=True)
    master_df.to_csv(PATH_OUTPUT, index=False)
    print(f"✅ SUKCES! Plik zapisany: {PATH_OUTPUT}")
    print(master_df[['Date', 'PKD_Code', 'PKO_SCORE_FINAL']].tail())

if __name__ == "__main__":
    main()