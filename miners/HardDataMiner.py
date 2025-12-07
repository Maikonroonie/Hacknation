import pandas as pd
import numpy as np
import os

# --- KONFIGURACJA ŚCIEŻEK ---
# Ustalanie ścieżek względem lokalizacji tego skryptu
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) 
DATA_DIR = os.path.join(PROJECT_ROOT,'Hacknation', 'my-react-app', 'public', 'data')

PATH_FINANCE = os.path.join(DATA_DIR, 'wsk_fin.csv')
PATH_BANKRUPTCY = os.path.join(DATA_DIR, 'krz_pkd.csv')
PATH_OUTPUT_HARD = os.path.join(DATA_DIR, 'processed', 'hard_datav2.csv')

# Lista branż (PKD 2-cyfrowe)
KEY_INDUSTRIES = [
    '01', '10', '16', '23', '24', '29', '31', '35', 
    '41', '68', '46', '47', '49', '55', '62'
]

def process_finance_data():
    """Wczytuje i czyści dane finansowe z GUS"""
    print("⏳ Przetwarzanie danych finansowych (Smart Mapping)...")
    
    try:
        # Próba wczytania z różnymi separatorami
        try:
            df = pd.read_csv(PATH_FINANCE, sep=';', dtype=str)
        except:
            df = pd.read_csv(PATH_FINANCE, sep=',', dtype=str)
            
        # Czyszczenie nazw kolumn (usuwamy spacje na początku/końcu)
        df.columns = [c.strip() for c in df.columns]
        
        # Inteligentne szukanie kolumny z kodem PKD i Wskaźnikiem
        pkd_col = next((c for c in df.columns if 'PKD' in c), None)
        wsk_col = next((c for c in df.columns if 'SKAZNIK' in c or 'ska' in c.lower()), None)
        
        if not pkd_col or not wsk_col:
            print(f"❌ BŁĄD: Nie znaleziono kolumn PKD/Wskaźnik. Dostępne: {df.columns}")
            return pd.DataFrame()
            
        # Ujednolicenie nazw
        df = df.rename(columns={pkd_col: 'PKD', wsk_col: 'WSKAZNIK'})
        
        # Filtrowanie PKD (pierwsze 2 cyfry)
        df['PKD_Main'] = df['PKD'].str.replace(r'\D', '', regex=True).str[:2]
        df = df[df['PKD_Main'].isin(KEY_INDUSTRIES)].copy()

        # Funkcja do czyszczenia polskich liczb (np. "1 234,56")
        def clean_currency(x):
            if isinstance(x, str):
                x = x.replace('\xa0', '').replace(' ', '') # Usuń spacje tysięczne
                if x.lower() in ['bd', '#n/d', '', 'nan', 'nd', '-']: return 0.0
                x = x.replace(',', '.') # Zamień przecinek na kropkę
                try: return float(x)
                except: return 0.0
            return float(x) if x else 0.0

        # Znajdź kolumny z latami (wszystkie > 2000)
        year_cols = [c for c in df.columns if c.strip().isdigit() and int(c.strip()) > 2000]
        
        for col in year_cols:
            df[col] = df[col].apply(clean_currency)

        # --- SMART MAPOWANIE ---
        # Klucz to fragment tekstu, którego szukamy. Wartość to nasza nazwa kolumny.
        keyword_map = {
            'przychody ogółem': 'Revenue',
            'wynik finansowy netto': 'Profit',
            'liczba jednostek': 'Company_Count',
            'zobowiązania krótkoterminowe': 'Short_Term_Liabilities',
            'kapitał obrotowy': 'NWC',
            'aktywa obrotowe': 'Current_Assets', # Może nie istnieć
            'przeciętne zatrudnienie': 'Employment' # Może nie istnieć
        }

        def map_indicator(val):
            val_lower = str(val).lower()
            for key, target in keyword_map.items():
                if key in val_lower:
                    return target
            return None

        df['WSKAZNIK_EN'] = df['WSKAZNIK'].apply(map_indicator)
        
        # Zostawiamy tylko rozpoznane wiersze
        df = df.dropna(subset=['WSKAZNIK_EN']).copy()

        # Pivot (Zamiana wierszy na kolumny)
        df_melted = df.melt(id_vars=['PKD_Main', 'WSKAZNIK_EN'], value_vars=year_cols, var_name='Year', value_name='Value')
        
        df_fin = df_melted.pivot_table(
            index=['Year', 'PKD_Main'],
            columns='WSKAZNIK_EN',
            values='Value',
            aggfunc='sum'
        ).reset_index()

        # Data
        df_fin['Date'] = pd.to_datetime(df_fin['Year'] + '-01-01')

        # Uzupełnij brakujące kolumny zerami
        for target_col in keyword_map.values():
            if target_col not in df_fin.columns:
                df_fin[target_col] = 0.0
        
        return df_fin

    except Exception as e:
        print(f"❌ Błąd w process_finance_data: {e}")
        return pd.DataFrame()

def process_bankruptcy_data():
    """Wczytuje dane o upadłościach"""
    print("⏳ Przetwarzanie danych o upadłościach...")
    if not os.path.exists(PATH_BANKRUPTCY):
        print("⚠️ Brak pliku upadłości.")
        return None
        
    try:
        # Wczytanie z separatorem ;
        df = pd.read_csv(PATH_BANKRUPTCY, sep=';')
        
        # Normalizacja nazw kolumn na małe litery
        df.columns = [c.lower().strip() for c in df.columns]
        
        pkd_col = next((c for c in df.columns if 'pkd' in c), None)
        year_col = next((c for c in df.columns if 'rok' in c or 'data' in c), None)
        val_col = next((c for c in df.columns if 'liczba' in c or 'upad' in c), None)

        if not pkd_col or not year_col or not val_col:
            print("❌ Nie rozpoznano kolumn w pliku upadłości.")
            return None

        # Czyszczenie PKD
        df['PKD_Main'] = df[pkd_col].astype(str).str[:2]
        df = df[df['PKD_Main'].isin(KEY_INDUSTRIES)].copy()
        
        # Rok jako string
        df['Year'] = df[year_col].astype(str)
        
        # Agregacja
        df_grouped = df.groupby(['Year', 'PKD_Main'])[val_col].sum().reset_index()
        df_grouped.rename(columns={val_col: 'Liczba_Upadlosci'}, inplace=True)
        
        return df_grouped
        
    except Exception as e:
        print(f"⚠️ Błąd odczytu upadłości: {e}")
        return None

def main_prepare():
    try:
        # Stwórz folder wyjściowy
        if not os.path.exists(os.path.dirname(PATH_OUTPUT_HARD)):
            os.makedirs(os.path.dirname(PATH_OUTPUT_HARD))

        # 1. Pobierz Finanse
        df_fin = process_finance_data()
        if df_fin.empty: return

        # 2. Pobierz Upadłości
        df_bankr = process_bankruptcy_data()

        # 3. Łączenie
        if df_bankr is not None:
            df_hard = pd.merge(df_fin, df_bankr, on=['Year', 'PKD_Main'], how='left')
            df_hard['Liczba_Upadlosci'] = df_hard['Liczba_Upadlosci'].fillna(0)
        else:
            df_hard = df_fin
            df_hard['Liczba_Upadlosci'] = 0

        df_hard.rename(columns={'PKD_Main': 'PKD_Code'}, inplace=True)

        # --- OBLICZENIA I NAPRAWA DANYCH (Feature Engineering) ---
        
        # A. Naprawa Aktywów Obrotowych (gdy brak w pliku, ale jest NWC)
        # Jeśli Current_Assets są puste (suma bliska 0), wyliczamy je: Assets = NWC + Liabilities
        if df_hard['Current_Assets'].sum() <= 10.0:
            print("💡 Brak 'Aktywa obrotowe' w pliku. Wyliczam z: NWC + Zobowiązania.")
            df_hard['Current_Assets'] = df_hard['NWC'] + df_hard['Short_Term_Liabilities']

        # B. Płynność (Liquidity)
        # Zabezpieczenie: jeśli Liabilities=0, dajemy bezpieczną wartość (np. 2.0)
        df_hard['Liquidity_Ratio'] = np.where(
            df_hard['Short_Term_Liabilities'] > 0,
            df_hard['Current_Assets'] / df_hard['Short_Term_Liabilities'],
            2.0 
        )

        # C. Wskaźnik Upadłości (Bankruptcy Rate)
        df_hard['Bankruptcy_Rate'] = np.where(
            df_hard['Company_Count'] > 0,
            df_hard['Liczba_Upadlosci'] / df_hard['Company_Count'],
            0.0
        )

        # D. Dynamika Rozwoju (Employment/Company Growth)
        # Sortowanie jest kluczowe dla funkcji shift()
        df_hard = df_hard.sort_values(by=['PKD_Code', 'Date'])
        
        # Jeśli nie ma danych o zatrudnieniu, używamy liczby firm
        target_col = 'Employment'
        if df_hard['Employment'].sum() <= 10.0:
            print("💡 Brak danych o zatrudnieniu. Używam 'Liczba jednostek' do dynamiki.")
            target_col = 'Company_Count'

        # Obliczanie zmiany rok do roku
        df_hard['Prev_Val'] = df_hard.groupby('PKD_Code')[target_col].shift(1)
        
        df_hard['Employment_Dynamics'] = np.where(
            (df_hard['Prev_Val'] > 0),
            (df_hard[target_col] - df_hard['Prev_Val']) / df_hard['Prev_Val'],
            0.0
        )
        
        # Sprzątanie
        df_hard = df_hard.drop(columns=['Prev_Val'])

        # Zapis
        df_hard.to_csv(PATH_OUTPUT_HARD, index=False)
        print(f"✅ Hard Data Przetworzone! Wynik: {PATH_OUTPUT_HARD}")
        
        # Podgląd kontrolny (ostatnie 5 wierszy)
        print("\n--- PODGLĄD DANYCH ---")
        print(df_hard[['Date', 'PKD_Code', 'Current_Assets', 'Liquidity_Ratio', 'Employment_Dynamics']].tail())

    except Exception as e:
        print(f"❌ Błąd krytyczny: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main_prepare()