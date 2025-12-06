import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

# --- KONFIGURACJA ---
# Ustaw na False, bo masz już plik hard_data.csv!
USE_MOCK_DATA = False 

# Ścieżki
PATH_HARD = 'data/processed/hard_data.csv'
PATH_SOFT = 'data/processed/soft_data.csv' # To wygenerujemy w locie
PATH_OUTPUT = 'data/processed/MASTER_DATA.csv'

def generate_mock_data_fallback():
    """Awaryjny generator, gdyby nie było pliku CSV."""
    print("⚠️ BRAK PLIKU CSV - Generowanie pełnych danych sztucznych...")
    dates = pd.date_range(start='2020-01-01', periods=48, freq='MS')
    mock_data = []
    codes = ['41', '47', '49', '55', '62'] # Przykładowe
    for pkd in codes:
        for date in dates:
            rev = np.random.randint(1000, 5000)
            mock_data.append([date, pkd, rev, rev*0.1, 0.05, 50, 5.85, 100])
    
    df = pd.DataFrame(mock_data, columns=['Date', 'PKD_Code', 'Revenue', 'Profit', 'Bankruptcy_Rate', 'Google_Trends', 'WIBOR', 'Energy_Price'])
    return df

def load_and_process_data():
    """
    Funkcja Hybrydowa:
    1. Czyta Twoje REALNE dane twarde (roczne).
    2. Zamienia je na miesięczne (Upsampling/Interpolacja).
    3. Generuje do nich pasujące dane miękkie (Mock Soft Data).
    """
    if USE_MOCK_DATA:
        return generate_mock_data_fallback()

    print(f"📂 Wczytuję realne dane twarde z: {PATH_HARD}...")
    
    try:
        # 1. Wczytanie Hard Data
        # Używamy dtype={'PKD_Code': str}, żeby nie zgubić zera na początku (np. '01')
        df_hard = pd.read_csv(PATH_HARD, parse_dates=['Date'], dtype={'PKD_Code': str})
        
        # 2. UPSAMPLING (Zmiana Roczne -> Miesięczne)
        print("📈 Przeliczanie danych rocznych na miesięczne (Interpolacja liniowa)...")
        upsampled_dfs = []
        
        # Grupujemy po branży, żeby interpolować każdą osobno
        for pkd, group in df_hard.groupby('PKD_Code'):
            group = group.set_index('Date')
            
            # Resample do początku miesiąca ('MS') i interpolacja wartości między latami
            group_monthly = group.resample('MS').interpolate(method='linear')
            
            # Kolumna PKD znika przy resample, przywracamy ją
            group_monthly['PKD_Code'] = pkd
            
            upsampled_dfs.append(group_monthly.reset_index())
            
        # Sklejamy z powrotem w jedną całość
        df_monthly = pd.concat(upsampled_dfs)
        
        # Ucinamy dane z przyszłości (interpolacja może dodać miesiące do końca roku 2024)
        df_monthly = df_monthly[df_monthly['Date'] <= pd.Timestamp.now()]

        # 3. GENEROWANIE SOFT DATA (Dopasowanie do nowych dat)
        print("⚠️ Generowanie pasujących danych miękkich (Google Trends, Makro)...")
        
        # Listy na nowe dane
        g_trends = []
        wibors = []
        energies = []
        
        for index, row in df_monthly.iterrows():
            date = row['Date']
            pkd = row['PKD_Code']
            
            # --- Symulacja Google Trends ---
            # Sezonowość (sinusoida) + losowość
            base_trend = 50
            seasonality = np.sin(date.month) * 15
            trend = base_trend + seasonality + np.random.randint(-10, 10)
            g_trends.append(max(0, min(100, trend))) # Ograniczenie 0-100
            
            # --- Symulacja WIBOR (Realistyczna historia) ---
            if date.year < 2021:
                wibor = 0.2 + np.random.uniform(0, 0.1) # Niskie stopy
            elif date.year == 2021:
                wibor = 0.2 + (date.month * 0.4) # Wzrost w 2021
            else:
                wibor = 5.85 + np.random.uniform(-0.2, 0.2) # Wysokie stopy teraz
            wibors.append(wibor)
            
            # --- Symulacja Cen Energii ---
            # Trend rosnący od 2020
            energy = 100 + (date.year - 2020) * 40 + (np.sin(date.month) * 10)
            energies.append(energy)
            
        # Dodajemy nowe kolumny do DataFrame
        df_monthly['Google_Trends'] = g_trends
        df_monthly['WIBOR'] = wibors
        df_monthly['Energy_Price'] = energies
        
        return df_monthly

    except FileNotFoundError:
        print(f"❌ BŁĄD: Nie znaleziono pliku {PATH_HARD}!")
        return generate_mock_data_fallback()

def calculate_index(df):
    print("⚙️ Przeliczanie Algorytmu PKO FutureIndex...")
    
    # 1. Feature Engineering
    df = df.sort_values(['PKD_Code', 'Date'])
    
    # Dynamika przychodów (Rok do Roku)
    # pct_change(12) porównuje ten sam miesiąc z zeszłym rokiem
    df['Rev_Growth_YoY'] = df.groupby('PKD_Code')['Revenue'].pct_change(periods=12).fillna(0)
    
    # Marża zysku
    df['Profit_Margin'] = df['Profit'] / df['Revenue']
    df['Profit_Margin'] = df['Profit_Margin'].fillna(0)

    # 2. Mapowanie Ryzyka (Expert Knowledge)
    risk_sensitivity = {
        '41': {'wibor': 1.0, 'energy': 0.3}, # Budowlanka
        '68': {'wibor': 1.0, 'energy': 0.2}, # Nieruchomości
        '24': {'wibor': 0.4, 'energy': 1.0}, # Huty/Metale
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
        # Obsługa błędów, gdyby kolumna była stała (np. same zera)
        if df[col].std() == 0:
            df[f'Norm_{col}'] = 50 # Neutralna wartość
        else:
            df[f'Norm_{col}'] = scaler.fit_transform(df[[col]])

    # 4. Obliczanie Ryzyka Złożonego
    df['Total_Risk_Score'] = (
        (df['Norm_WIBOR'] * df['Risk_WIBOR_Weight']) + 
        (df['Norm_Energy_Price'] * df['Risk_Energy_Weight'])
    )
    df['Norm_Total_Risk'] = scaler.fit_transform(df[['Total_Risk_Score']])

    # --- FINALNY WZÓR ---
    # Zysk (+) | Wzrost (+) | Google (+) | Ryzyko (-) | Upadłość (-)
    df['PKO_SCORE'] = (
        (0.20 * df['Norm_Profit_Margin']) + 
        (0.25 * df['Norm_Rev_Growth_YoY']) + 
        (0.25 * df['Norm_Google_Trends']) - 
        (0.15 * df['Norm_Total_Risk']) - 
        (0.15 * df['Norm_Bankruptcy_Rate']) # Upadłość obniża wynik!
    )
    
    # Skalujemy wynik końcowy na 0-100
    df['PKO_SCORE_FINAL'] = scaler.fit_transform(df[['PKO_SCORE']])
    
    return df

def main():
    # 1. Ładowanie Hybrydowe
    master_df = load_and_process_data()
    
    if master_df is not None:
        # 2. Obliczenia
        master_df = calculate_index(master_df)
        
        # 3. Zapis
        os.makedirs(os.path.dirname(PATH_OUTPUT), exist_ok=True)
        master_df.to_csv(PATH_OUTPUT, index=False)
        print(f"✅ SUKCES! Plik zapisany: {PATH_OUTPUT}")
        print("Przykładowe wyniki (ostatnie 5 miesięcy):")
        print(master_df[['Date', 'PKD_Code', 'PKO_SCORE_FINAL']].tail())

if __name__ == "__main__":
    main()