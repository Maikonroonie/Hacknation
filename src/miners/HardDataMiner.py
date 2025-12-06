import pandas as pd
import numpy as np
import os

# --- KONFIGURACJA ŚCIEŻEK ---
PATH_FINANCE = 'wsk_fin.csv'       # Plik z danymi finansowymi
PATH_BANKRUPTCY = 'krz_pkd.csv'    # Plik z upadłościami
PATH_OUTPUT_HARD = 'data/processed/hard_data.csv' # Gdzie zapisać wynik

# Lista interesujących nas branż (PKD 2-cyfrowe)
KEY_INDUSTRIES = [
    '01', '10', '16', '23', '24', '29', '31', '35', 
    '41', '68', '46', '47', '49', '55', '62'
]

# --- 1. PRZETWARZANIE DANYCH FINANSOWYCH (wsk_fin.csv) ---
def process_finance_data():
    print("⏳ Przetwarzanie danych finansowych...")
    
    # Wczytanie danych
    try:
        df = pd.read_csv(PATH_FINANCE, sep=';', dtype={'PKD': str})
    except FileNotFoundError:
        print(f"❌ Nie znaleziono pliku: {PATH_FINANCE}")
        return pd.DataFrame()

    # Filtrowanie tylko wybranych branż (pierwsze 2 cyfry)
    df['PKD_Main'] = df['PKD'].str[:2]
    df = df[df['PKD_Main'].isin(KEY_INDUSTRIES)].copy()

    # Funkcja czyszcząca liczby
    def clean_currency(x):
        if isinstance(x, str):
            x = x.replace('\xa0', '').replace(' ', '')
            if x.lower() in ['bd', '#n/d', '']: return 0.0
            x = x.replace(',', '.')
        return float(x)

    # Konwersja kolumn z latami na liczby
    years = [str(y) for y in range(2010, 2025)]
    for col in years:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)

    # --- MAPOWANIE WSKAŹNIKÓW (TUTAJ zaszła główna zmiana) ---
    # UWAGA: Sprawdź, czy nazwy kluczy (np. 'Aktywa obrotowe') dokładnie pasują 
    # do nazw w Twoim pliku CSV (kolumna WSKAZNIK).
    indicators_map = {
        'GS Przychody ogółem ': 'Revenue',
        'NP Wynik finansowy netto (zysk netto) ': 'Profit',
        'EN Liczba jednostek gospodarczych ': 'Company_Count',
        # Nowe wskaźniki potrzebne do funkcjonalności ze zdjęcia:
        'Aktywa obrotowe ': 'Current_Assets',                 # Do Płynności
        'Zobowiązania krótkoterminowe ': 'Short_Term_Liabilities', # Do Płynności
        'Przeciętne zatrudnienie ': 'Employment'              # Do Dynamiki Zatrudnienia
    }
    
    # Filtrujemy tylko potrzebne wskaźniki
    df = df[df['WSKAZNIK'].isin(indicators_map.keys())].copy()
    df['WSKAZNIK_EN'] = df['WSKAZNIK'].map(indicators_map)

    # Melt - Zamiana lat z kolumn na wiersze
    df_melted = df.melt(
        id_vars=['PKD_Main', 'WSKAZNIK_EN'],
        value_vars=[y for y in years if y in df.columns],
        var_name='Year',
        value_name='Value'
    )

    # Pivot - Rozrzucenie wskaźników do osobnych kolumn
    df_fin_final = df_melted.pivot_table(
        index=['Year', 'PKD_Main'],
        columns='WSKAZNIK_EN',
        values='Value',
        aggfunc='sum'
    ).reset_index()

    # Tworzymy datę
    df_fin_final['Date'] = pd.to_datetime(df_fin_final['Year'] + '-01-01')
    
    # Sprawdzenie czy nowe kolumny istnieją (na wypadek braku w CSV)
    expected_cols = ['Revenue', 'Profit', 'Company_Count', 'Current_Assets', 'Short_Term_Liabilities', 'Employment']
    for col in expected_cols:
        if col not in df_fin_final.columns:
            print(f"⚠️ Uwaga: Brak kolumny '{col}' po przetworzeniu. Wstawiam 0.")
            df_fin_final[col] = 0.0

    return df_fin_final[['Date', 'PKD_Main'] + expected_cols]

# --- 2. PRZETWARZANIE DANYCH O UPADŁOŚCIACH ---
def process_bankruptcy_data():
    print("⏳ Przetwarzanie danych o upadłościach...")
    try:
        df = pd.read_csv(PATH_BANKRUPTCY, sep=';', dtype={'pkd': str})
        
        df['PKD_Main'] = df['pkd'].str[:2]
        df = df[df['PKD_Main'].isin(KEY_INDUSTRIES)].copy()
        
        # Agregacja
        df_grouped = df.groupby(['rok', 'PKD_Main'])['liczba_upadlosci'].sum().reset_index()
        df_grouped['Date'] = pd.to_datetime(df_grouped['rok'].astype(str) + '-01-01')
        
        return df_grouped[['Date', 'PKD_Main', 'liczba_upadlosci']]
    except Exception as e:
        print(f"⚠️ Nie można wczytać pliku upadłości: {e}")
        return None

# --- 3. GŁÓWNA FUNKCJA ---
def main_prepare():
    try:
        # 1. Dane Finansowe
        df_fin = process_finance_data()
        if df_fin.empty:
            print("❌ Brak danych finansowych. Przerywam.")
            return

        # 2. Dane Upadłościowe
        df_bankr = process_bankruptcy_data()

        # 3. Łączenie
        if df_bankr is not None:
            df_hard = pd.merge(df_fin, df_bankr, on=['Date', 'PKD_Main'], how='left')
            df_hard['liczba_upadlosci'] = df_hard['liczba_upadlosci'].fillna(0)
        else:
            df_hard = df_fin
            df_hard['liczba_upadlosci'] = 0

        # Zmiana nazwy PKD na standardową
        df_hard = df_hard.rename(columns={'PKD_Main': 'PKD_Code'})

        # --- NOWE FUNKCJONALNOŚCI (WYLICZENIA) ---

        # A. Wskaźnik Upadłości (Szkodowość)
        df_hard['Bankruptcy_Rate'] = np.where(
            df_hard['Company_Count'] > 0,
            df_hard['liczba_upadlosci'] / df_hard['Company_Count'],
            0
        )

        # B. Płynność (Liquidity) -> (Current_Assets / Short_Term_Liabilities)
        # Zabezpieczenie przed dzieleniem przez zero
        df_hard['Liquidity_Ratio'] = np.where(
            df_hard['Short_Term_Liabilities'] > 0,
            df_hard['Current_Assets'] / df_hard['Short_Term_Liabilities'],
            0 # Jeśli brak zobowiązań, można przyjąć 0 lub NaN (tu bezpieczniej 0 dla modelu ML)
        )

        # C. Dynamika Zatrudnienia (Employment Dynamics) -> (Emp_T - Emp_T-1) / Emp_T-1
        # Najpierw musimy posortować dane, żeby shift() brał poprawnie rok poprzedni
        df_hard = df_hard.sort_values(by=['PKD_Code', 'Date'])

        # Obliczamy przesunięcie (poprzedni rok dla tej samej branży)
        df_hard['Employment_Prev_Year'] = df_hard.groupby('PKD_Code')['Employment'].shift(1)

        # Wyliczenie wzoru
        df_hard['Employment_Dynamics'] = np.where(
            df_hard['Employment_Prev_Year'] > 0,
            (df_hard['Employment'] - df_hard['Employment_Prev_Year']) / df_hard['Employment_Prev_Year'],
            0 # Brak historii lub zerowe zatrudnienie rok wcześniej
        )

        # Czyszczenie pomocniczych kolumn
        df_hard = df_hard.drop(columns=['Employment_Prev_Year'])

        # --- ZAPIS ---
        os.makedirs(os.path.dirname(PATH_OUTPUT_HARD), exist_ok=True)
        df_hard.to_csv(PATH_OUTPUT_HARD, index=False)
        
        print(f"\n✅ Sukces! Plik zapisano: {PATH_OUTPUT_HARD}")
        print("Podgląd nowych kolumn:")
        print(df_hard[['Date', 'PKD_Code', 'Liquidity_Ratio', 'Employment_Dynamics']].tail())

    except Exception as e:
        print(f"❌ Błąd krytyczny: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main_prepare()