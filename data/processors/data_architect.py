import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

# --- KONFIGURACJA ---
# True  = Generuj wszystko sztucznie (bezpiecznik na demo)
# False = Wczytaj hard_data.csv I soft_data.csv z folderu data/processed/
USE_MOCK_DATA = False 

# Ścieżki do plików
PATH_HARD = 'data/processed/hard_data.csv'
PATH_SOFT = 'data/processed/soft_data.csv'
PATH_OUTPUT = 'data/processed/MASTER_DATA.csv'

# Lista branż (do generatora mocków)
KEY_INDUSTRIES = ['01', '10', '16', '23', '24', '29', '31', '35', '41', '46', '47', '49', '55', '62', '68']

 

def generate_full_mock_data():
    """Plan B: Generuje kompletny zestaw danych (Hard + Soft) z powietrza."""
    print("⚠️ TRYB MOCK: Generowanie w pełni sztucznych danych...")
    dates = pd.date_range(start='2020-01-01', periods=54, freq='MS') # Do połowy 2024
    
    mock_data = []
    for pkd in KEY_INDUSTRIES:
        base_rev = np.random.randint(2000, 10000)
        base_trend = np.random.randint(30, 80)
        
        for date in dates:
            # Hard Data Sim
            rev = base_rev + (np.sin(date.month) * 500) + np.random.randint(-200, 200)
            profit = rev * np.random.uniform(0.05, 0.20)
            bankr = np.random.randint(0, 100) # Liczba upadłości
            
            # Soft Data Sim
            trend = base_trend + np.random.randint(-10, 10)
            wibor = 5.85 if date.year > 2021 else 0.2
            energy = 100 + (date.year - 2020) * 20
            
            mock_data.append([date, pkd, rev, profit, bankr, trend, wibor, energy])
            
    df = pd.DataFrame(mock_data, columns=['Date', 'PKD_Code', 'Revenue', 'Profit', 'Bankruptcy_Rate', 'Google_Trends', 'WIBOR', 'Energy_Price'])
    return df

def load_real_data():
    """Plan A: Wczytuje prawdziwe pliki, robi upsampling Hard Data i łączy z Soft Data."""
    print("📂 TRYB REAL: Wczytywanie plików CSV...")
    
    # 1. Sprawdź czy pliki istnieją
    if not os.path.exists(PATH_HARD) or not os.path.exists(PATH_SOFT):
        print(f"❌ BŁĄD: Brakuje plików! Upewnij się, że masz '{PATH_HARD}' oraz '{PATH_SOFT}'.")
        return None

    try:
        # --- WCZYTYWANIE HARD DATA (ROCZNE) ---
        print(f"   -> Wczytuję {PATH_HARD}...")
        df_hard = pd.read_csv(PATH_HARD, parse_dates=['Date'], dtype={'PKD_Code': str})
        
        # Upsampling (Roczne -> Miesięczne)
        print("   -> Upsampling danych rocznych do miesięcznych...")
        upsampled_dfs = []
        for pkd, group in df_hard.groupby('PKD_Code'):
            group = group.set_index('Date').resample('MS').interpolate(method='linear')
            group['PKD_Code'] = pkd
            upsampled_dfs.append(group.reset_index())
        
        df_hard_monthly = pd.concat(upsampled_dfs)
        
        # --- WCZYTYWANIE SOFT DATA (MIESIĘCZNE) ---
        print(f"   -> Wczytuję {PATH_SOFT}...")
        df_soft = pd.read_csv(PATH_SOFT, parse_dates=['Date'], dtype={'PKD_Code': str})
        
        # --- ŁĄCZENIE (MERGE) ---
        print("   -> Łączenie danych twardych i miękkich...")
        # Łączymy po Dacie i Kodzie. Używamy 'inner', żeby mieć tylko miesiące, gdzie mamy komplet danych.
        master_df = pd.merge(df_hard_monthly, df_soft, on=['Date', 'PKD_Code'], how='inner')
        
        # Filtrujemy przyszłość (na wszelki wypadek)
        master_df = master_df[master_df['Date'] <= pd.Timestamp.now()]
        
        return master_df

    except Exception as e:
        print(f"❌ WYJĄTEK PODCZAS ŁADOWANIA: {e}")
        return None

def calculate_index(df):
    """Logika biznesowa PKO BP."""
    print("⚙️ Przeliczanie Algorytmu PKO FutureIndex...")
    
    # Sortowanie
    df = df.sort_values(['PKD_Code', 'Date'])
    
    # 1. Feature Engineering
    # Dynamika przychodów (Rok do Roku)
    df['Rev_Growth_YoY'] = df.groupby('PKD_Code')['Revenue'].pct_change(periods=12).fillna(0)
    # Marża
    df['Profit_Margin'] = df['Profit'] / df['Revenue']
    df['Profit_Margin'] = df['Profit_Margin'].fillna(0)

    # 2. Mapowanie Ryzyka (Expert Knowledge)
    risk_sensitivity = {
        '41': {'wibor': 1.0, 'energy': 0.3}, # Budowlanka
        '68': {'wibor': 1.0, 'energy': 0.2}, # Nieruchomości
        '24': {'wibor': 0.4, 'energy': 1.0}, # Huty
        '35': {'wibor': 0.3, 'energy': -0.5},# Energetyka
        '49': {'wibor': 0.5, 'energy': 0.8}, # Transport
        '10': {'wibor': 0.4, 'energy': 0.6}, # Spożywka
    }
    
    def get_risk(pkd, kind):
        return risk_sensitivity.get(pkd, {'wibor': 0.5, 'energy': 0.5}).get(kind, 0.5)

    df['Risk_WIBOR_Weight'] = df['PKD_Code'].apply(lambda x: get_risk(x, 'wibor'))
    df['Risk_Energy_Weight'] = df['PKD_Code'].apply(lambda x: get_risk(x, 'energy'))

    # 3. Normalizacja (0-100)
    scaler = MinMaxScaler(feature_range=(0, 100))
    cols_to_norm = ['Rev_Growth_YoY', 'Profit_Margin', 'Google_Trends', 'WIBOR', 'Energy_Price', 'Bankruptcy_Rate']
    
    for col in cols_to_norm:
        if col in df.columns:
            # Obsługa stałych wartości (żeby nie dzielić przez 0)
            if df[col].std() == 0:
                 df[f'Norm_{col}'] = 50
            else:
                df[f'Norm_{col}'] = scaler.fit_transform(df[[col]])
        else:
            print(f"⚠️ Uwaga: Brak kolumny {col} w danych wejściowych!")
            df[f'Norm_{col}'] = 50 # Default

    # 4. Ryzyko Złożone
    df['Total_Risk_Score'] = (
        (df['Norm_WIBOR'] * df['Risk_WIBOR_Weight']) + 
        (df['Norm_Energy_Price'] * df['Risk_Energy_Weight'])
    )
    df['Norm_Total_Risk'] = scaler.fit_transform(df[['Total_Risk_Score']])

    # 5. FINALNY WZÓR
    df['PKO_SCORE'] = (
        (0.20 * df['Norm_Profit_Margin']) + 
        (0.25 * df['Norm_Rev_Growth_YoY']) + 
        (0.25 * df['Norm_Google_Trends']) - 
        (0.15 * df['Norm_Total_Risk']) - 
        (0.15 * df['Norm_Bankruptcy_Rate']) 
    )
    
    # Skalowanie wyniku do 0-100
    df['PKO_SCORE_FINAL'] = scaler.fit_transform(df[['PKO_SCORE']])
    
    return df

def main():
    # KROK 1: Wybierz źródło danych
    if USE_MOCK_DATA:
        master_df = generate_full_mock_data()
    else:
        master_df = load_real_data()
        # Fallback: Jeśli ładowanie plików się nie uda, użyj mocka
        if master_df is None:
            print("⚠️ Nie udało się wczytać plików. Przełączam na MOCK DATA.")
            master_df = generate_full_mock_data()

    # KROK 2: Oblicz Indeks
    master_df = calculate_index(master_df)
    
    # KROK 3: Zapisz wynik
    os.makedirs(os.path.dirname(PATH_OUTPUT), exist_ok=True)
    master_df.to_csv(PATH_OUTPUT, index=False)
    
    print(f"✅ SUKCES! Plik zapisany: {PATH_OUTPUT}")
    print(f"   Ilość wierszy: {len(master_df)}")
    print(f"   Zakres dat: {master_df['Date'].min()} - {master_df['Date'].max()}")
    print("Próbka wyniku:")
    print(master_df[['Date', 'PKD_Code', 'PKO_SCORE_FINAL']].tail())

if __name__ == "__main__":
    main()