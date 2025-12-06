import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

# --- KONFIGURACJA ---
USE_MOCK_DATA = False

# Ścieżki do plików
PATH_HARD = 'data/processed/hard_data_extnd.csv'
PATH_SOFT = 'data/processed/soft_data.csv'
PATH_OUTPUT = 'data/processed/MASTER_DATA.csv'

def load_real_data():
    """Wczytuje rozszerzone dane twarde i łączy z miękkimi."""
    print("📂 TRYB REAL: Wczytywanie danych...")
    
    if not os.path.exists(PATH_HARD) or not os.path.exists(PATH_SOFT):
        print(f"❌ BŁĄD: Brakuje plików! Sprawdź czy masz {PATH_HARD} i {PATH_SOFT}")
        return None

    try:
        # --- 1. Hard Data (Roczne -> Miesięczne) ---
        print(f"   -> Przetwarzanie {PATH_HARD}...")
        df_hard = pd.read_csv(PATH_HARD, parse_dates=['Date'], dtype={'PKD_Code': str})
        
        # Obsługa zer w danych historycznych
        cols_to_fix = ['Current_Assets', 'Short_Term_Liabilities', 'Employment', 'Liquidity_Ratio']
        for col in cols_to_fix:
            if col in df_hard.columns:
                df_hard[col] = df_hard[col].replace(0, np.nan)

        # Upsampling (Interpolacja) 
        upsampled_dfs = []
        for pkd, group in df_hard.groupby('PKD_Code'):
            # Usuwamy PKD_Code przed interpolacją, bo to tekst i powoduje warningi
            temp_group = group.drop(columns=['PKD_Code'], errors='ignore')
            
            temp_group = temp_group.sort_values('Date').set_index('Date')
            
            # Wypełniamy braki
            temp_group = temp_group.resample('MS').interpolate(method='linear')
            temp_group = temp_group.bfill().ffill()
            
            # Przywracamy PKD
            temp_group['PKD_Code'] = pkd
            upsampled_dfs.append(temp_group.reset_index())
            
        df_hard_monthly = pd.concat(upsampled_dfs)
        
        # --- 2. Soft Data (Miesięczne/Tygodniowe -> Miesięczne) ---
        print(f"   -> Przetwarzanie {PATH_SOFT}...")
        
        # Wczytujemy kolumnę Data
        df_soft = pd.read_csv(PATH_SOFT, parse_dates=['Data'], dtype={'Kod_PKD': str})
        
        # Ujednolicenie nazw kolumn na angielski standard projektu
        df_soft = df_soft.rename(columns={'Data': 'Date', 'Kod_PKD': 'PKD_Code'})
        
        # Czyszczenie PKD (usuwamy 'PKD_' jeśli jest)
        if 'PKD_Code' in df_soft.columns:
            df_soft['PKD_Code'] = df_soft['PKD_Code'].astype(str).str.replace('PKD_', '')
        
        # Agregacja do miesiąca (średnia) - w razie gdyby dane były tygodniowe
        # Grupujemy tylko po numerycznych kolumnach, żeby uniknąć błędów
        numeric_cols = df_soft.select_dtypes(include=[np.number]).columns.tolist()
        # Dodajemy grupery
        groupers = [pd.Grouper(key='Date', freq='MS'), 'PKD_Code']
        
        df_soft_monthly = df_soft.groupby(groupers)[numeric_cols].mean().reset_index()
        
        # --- 3. Merge ---
        print("   -> Łączenie tabel...")
        master_df = pd.merge(df_hard_monthly, df_soft_monthly, on=['Date', 'PKD_Code'], how='inner')
        
        # Czyszczenie po merge'u
        master_df = master_df.fillna(0)
        
        return master_df

    except Exception as e:
        print(f"❌ Wyjątek w ETL: {e}")
        import traceback
        traceback.print_exc()
        return None

def calculate_index(df):
    print("⚙️ Przeliczanie Algorytmu PKO FutureIndex V7.0...")
    df = df.sort_values(['PKD_Code', 'Date'])
    
    # --- 1. INŻYNIERIA CECH (Wskaźniki) ---
    
    # A. Dynamika Przychodów (YoY)
    df['Rev_Growth_YoY'] = df.groupby('PKD_Code')['Revenue'].pct_change(periods=12).fillna(0)
    
    # B. Marża Zysku
    df['Profit_Margin'] = df['Profit'] / df['Revenue'].replace(0, 1)
    
    # C. Płynność (Liquidity)
    if 'Current_Assets' in df.columns and 'Short_Term_Liabilities' in df.columns:
        df['Liquidity_Calc'] = df['Current_Assets'] / df['Short_Term_Liabilities'].replace(0, 1)
        df['Liquidity_Calc'] = df['Liquidity_Calc'].clip(0, 5) 
    else:
        df['Liquidity_Calc'] = 1.2
        
    # D. Dynamika Zatrudnienia
    if 'Employment' in df.columns:
        df['Employment_Growth'] = df.groupby('PKD_Code')['Employment'].pct_change(periods=12).fillna(0)
    else:
        df['Employment_Growth'] = 0

    # --- 2. MAPOWANIE WRAŻLIWOŚCI (Ryzyko Sektorowe) ---
    risk_sensitivity = {
        '41': {'wibor': 1.0, 'energy': 0.3}, # Budowlanka
        '68': {'wibor': 1.0, 'energy': 0.2}, # Nieruchomości
        '24': {'wibor': 0.4, 'energy': 1.0}, # Metale
        '35': {'wibor': 0.3, 'energy': -0.5},# Energetyka
        '49': {'wibor': 0.5, 'energy': 0.9}, # Transport
        '10': {'wibor': 0.4, 'energy': 0.6}, # Spożywka
        '62': {'wibor': 0.1, 'energy': 0.1}, # IT
    }
    
    def get_risk(pkd, kind):
        return risk_sensitivity.get(pkd, {'wibor': 0.5, 'energy': 0.5}).get(kind, 0.5)

    df['Risk_WIBOR_Weight'] = df['PKD_Code'].apply(lambda x: get_risk(x, 'wibor'))
    df['Risk_Energy_Weight'] = df['PKD_Code'].apply(lambda x: get_risk(x, 'energy'))

    # --- 3. NORMALIZACJA (0-100) ---
    scaler = MinMaxScaler(feature_range=(0, 100))
    
    cols_to_norm = {
        'Rev_Growth_YoY': 'Norm_Growth',
        'Profit_Margin': 'Norm_Margin',
        'Google_Trends': 'Norm_Google',     
        'WIBOR': 'Norm_WIBOR',              
        'Energy_Price': 'Norm_Energy',      
        'Bankruptcy_Rate': 'Norm_Bankrupt', 
        'Liquidity_Calc': 'Norm_Liquidity', 
        'Employment_Growth': 'Norm_Employ'  
    }
    
    for col, norm_name in cols_to_norm.items():
        if col in df.columns:
            if df[col].std() == 0:
                 df[norm_name] = 50
            else:
                df[norm_name] = scaler.fit_transform(df[[col]])
        else:
            df[norm_name] = 50

    # --- 4. RYZYKO ZŁOŻONE ---
    # Jeśli brakuje kolumn makro, wstawiamy 0
    if 'Norm_WIBOR' not in df.columns: df['Norm_WIBOR'] = 0
    if 'Norm_Energy' not in df.columns: df['Norm_Energy'] = 0

    df['Total_Risk_Raw'] = (
        (df['Norm_WIBOR'] * df['Risk_WIBOR_Weight']) + 
        (df['Norm_Energy'] * df['Risk_Energy_Weight'])
    )
    df['Norm_Total_Risk'] = scaler.fit_transform(df[['Total_Risk_Raw']])

    # --- 5. FINALNY WZÓR (PKO INDEX) ---
    df['PKO_SCORE'] = (
        (0.15 * df['Norm_Margin']) + 
        (0.15 * df['Norm_Growth']) +
        (0.10 * df['Norm_Liquidity']) +
        (0.20 * df['Norm_Google']) +
        (0.10 * df['Norm_Employ']) +
        (0.15 * (100 - df['Norm_Total_Risk'])) +  
        (0.15 * (100 - df['Norm_Bankrupt']))      
    )
    
    df['PKO_SCORE_FINAL'] = scaler.fit_transform(df[['PKO_SCORE']])
    
    return df

def main():
    if USE_MOCK_DATA:
        pass # Tu byłby mock, ale skupiamy się na Real Data
    
    master_df = load_real_data()
    
    if master_df is not None:
        master_df = calculate_index(master_df)
        
        os.makedirs(os.path.dirname(PATH_OUTPUT), exist_ok=True)
        
        # Wybieramy kluczowe kolumny
        cols_to_save = [
            'Date', 'PKD_Code', 
            'PKO_SCORE_FINAL', 'PKO_SCORE',
            'Revenue', 'Profit', 'Liquidity_Calc', 'Employment', 'Bankruptcy_Rate',
            'Google_Trends', 'WIBOR', 'Energy_Price',
            'Norm_Growth', 'Norm_Margin', 'Norm_Liquidity', 'Norm_Employ',
            'Norm_Google', 'Norm_Total_Risk', 'Norm_Bankrupt'
        ]
        # Zapisz tylko te, które istnieją (zabezpieczenie)
        cols_to_save = [c for c in cols_to_save if c in master_df.columns]
        
        master_df[cols_to_save].to_csv(PATH_OUTPUT, index=False)
        
        print(f"✅ SUKCES! Wygenerowano MASTER_DATA.csv ({len(master_df)} wierszy)")
        print(master_df[['Date', 'PKD_Code', 'PKO_SCORE_FINAL']].tail())

if __name__ == "__main__":
    main()