import pandas as pd
import numpy as np

# --- KONFIGURACJA ŚCIEŻEK ---
# Pliki wejściowe (te, które masz)
PATH_FINANCE = 'wsk_fin.csv'       # Plik z przychodami, zyskami (wiersze to lata w kolumnach)
PATH_BANKRUPTCY = 'krz_pkd.csv'    # Plik z upadłościami (wiersze to pojedyncze zdarzenia)
PATH_OUTPUT_HARD = 'data/processed/hard_data.csv' # Gdzie zapisać wynik

# Lista interesujących nas branż (PKD 2-cyfrowe)
KEY_INDUSTRIES = [
    '01', '10', '16', '23', '24', '29', '31', '35', 
    '41', '68', '46', '47', '49', '55', '62'
]

# --- 1. PRZETWARZANIE DANYCH FINANSOWYCH (wsk_fin.csv) ---
def process_finance_data():
    print("⏳ Przetwarzanie danych finansowych...")
    # Wczytanie z wymuszeniem PKD jako tekst
    df = pd.read_csv(PATH_FINANCE, sep=';', dtype={'PKD': str})
    
    # Filtrowanie tylko wybranych branż (pierwsze 2 cyfry)
    df['PKD_Main'] = df['PKD'].str[:2]
    df = df[df['PKD_Main'].isin(KEY_INDUSTRIES)].copy()

    # Funkcja czyszcząca liczby (usuwanie spacji, zamiana przecinków)
    def clean_currency(x):
        if isinstance(x, str):
            x = x.replace('\xa0', '').replace(' ', '')
            if x.lower() == 'bd': return 0.0
            x = x.replace(',', '.')
        return float(x)

    # Lista lat dostępnych w pliku
    years = [str(y) for y in range(2010, 2025)] # Bierzemy np. od 2010
    for col in years:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency)

    # Mapowanie nazw wskaźników na angielskie (zgodne z Twoim kodem głównym)
    # Revenue = Przychody ogółem
    # Profit = Wynik finansowy netto
    indicators_map = {
        'GS Przychody ogółem ': 'Revenue',
        'NP Wynik finansowy netto (zysk netto) ': 'Profit',
        'EN Liczba jednostek gospodarczych ': 'Company_Count' # Potrzebne do mianownika upadłości
    }
    
    # Filtrujemy tylko potrzebne wskaźniki
    df = df[df['WSKAZNIK'].isin(indicators_map.keys())].copy()
    df['WSKAZNIK_EN'] = df['WSKAZNIK'].map(indicators_map)

    # Melt (Topienie) - Zamiana lat z kolumn na wiersze
    df_melted = df.melt(
        id_vars=['PKD_Main', 'WSKAZNIK_EN'],
        value_vars=[y for y in years if y in df.columns],
        var_name='Year',
        value_name='Value'
    )

    # Pivot - Rozrzucenie wskaźników do osobnych kolumn (Revenue, Profit obok siebie)
    # Sumujemy wartości dla całej grupy PKD (np. 01.11 + 01.12 -> 01)
    df_fin_final = df_melted.pivot_table(
        index=['Year', 'PKD_Main'],
        columns='WSKAZNIK_EN',
        values='Value',
        aggfunc='sum'
    ).reset_index()

    # Tworzymy datę (ustawiamy na styczeń danego roku, bo dane są roczne)
    df_fin_final['Date'] = pd.to_datetime(df_fin_final['Year'] + '-01-01')
    
    return df_fin_final[['Date', 'PKD_Main', 'Revenue', 'Profit', 'Company_Count']]

# --- 2. PRZETWARZANIE DANYCH O UPADŁOŚCIACH (krz_pkd.csv) ---
def process_bankruptcy_data():
    print("⏳ Przetwarzanie danych o upadłościach...")
    # Tutaj zakładam strukturę pliku krz_pkd.csv na podstawie Twoich pytań
    # Jeśli masz tam kolumnę 'rok', 'pkd', 'liczba_upadlosci'
    df = pd.read_csv(PATH_BANKRUPTCY, sep=';', dtype={'pkd': str})
    
    # Wyciągnięcie głównego PKD (2 cyfry)
    df['PKD_Main'] = df['pkd'].str[:2]
    df = df[df['PKD_Main'].isin(KEY_INDUSTRIES)].copy()
    
    # Grupowanie po Roku i PKD
    df_grouped = df.groupby(['rok', 'PKD_Main'])['liczba_upadlosci'].sum().reset_index()
    
    # Tworzenie daty
    df_grouped['Date'] = pd.to_datetime(df_grouped['rok'].astype(str) + '-01-01')
    
    return df_grouped[['Date', 'PKD_Main', 'liczba_upadlosci']]

# --- 3. ŁĄCZENIE (MERGE) ---
def main_prepare():
    try:
        # Pobierz dane
        df_fin = process_finance_data()
        
        # Opcjonalnie: jeśli plik upadłości nie istnieje/ma błędy, pomiń
        try:
            df_bankr = process_bankruptcy_data()
            # Łączymy finanse z upadłościami
            df_hard = pd.merge(df_fin, df_bankr, on=['Date', 'PKD_Main'], how='left')
            df_hard['liczba_upadlosci'] = df_hard['liczba_upadlosci'].fillna(0)
        except Exception as e:
            print(f"⚠️ Ostrzeżenie: Nie udało się wczytać upadłości ({e}). Generuję bez nich.")
            df_hard = df_fin
            df_hard['liczba_upadlosci'] = 0

        # Obliczenie wskaźnika upadłości (Szkodowość)
        # Unikamy dzielenia przez zero
        df_hard['Bankruptcy_Rate'] = np.where(
            df_hard['Company_Count'] > 0,
            df_hard['liczba_upadlosci'] / df_hard['Company_Count'],
            0
        )

        # Sprzątanie nazw kolumn pod Twój główny skrypt
        df_hard = df_hard.rename(columns={'PKD_Main': 'PKD_Code'})
        
        # Zapis do pliku CSV
        import os
        os.makedirs(os.path.dirname(PATH_OUTPUT_HARD), exist_ok=True)
        df_hard.to_csv(PATH_OUTPUT_HARD, index=False)
        print(f"✅ Hard Data gotowe! Zapisano w: {PATH_OUTPUT_HARD}")
        print(df_hard.head())

    except Exception as e:
        print(f"❌ Błąd krytyczny: {e}")

if __name__ == "__main__":
    main_prepare()