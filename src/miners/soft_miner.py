import pandas as pd
from pytrends.request import TrendReq
import yfinance as yf
import time
import os
from datetime import datetime


PKD_KEYWORDS_MAP = {
    # --- SEKTORY PRODUKCYJNE ---
    # Rolnictwo
    "PKD_01": "pszenica cena + rzepak cena + nawozy + mleko skup + ciągnik rolniczy",
    
    # Spożywcza
    "PKD_10": "cena masła + cukier cena + mąka + ceny żywności + olej rzepakowy",
    
    # Drewno
    "PKD_16": "pellet cena + drewno opałowe + tarcica + tartak + więźba dachowa",
    
    # Materiały budowlane
    "PKD_23": "cement cena + beton towarowy + pustak + kostka brukowa + styropian",
    
    # Metale
    "PKD_24": "cena złomu + cena stali + pręty zbrojeniowe + miedź cena + aluminium",
    
    # Automotive
    "PKD_29": "nowe samochody + części samochodowe + mechanik + opony + produkcja aut",
    
    # Meble
    "PKD_31": "meble kuchenne + szafa na wymiar + sofa + ikea + meble biurowe",
    
    # Energetyka
    "PKD_35": "cena prądu + taryfa prąd + gaz cena + fotowoltaika + pompa ciepła",

    # --- BUDOWNICTWO I NIERUCHOMOŚCI ---
    # Budowlanka
    "PKD_41": "budowa domu + kredyt hipoteczny + deweloper + stan deweloperski + pozwolenie na budowę",
    
    # Nieruchomości
    "PKD_68": "mieszkania na sprzedaż + wynajem mieszkań + ceny mieszkań + notariusz + rynek wtórny",

    # --- USŁUGI I LOGISTYKA ---
    # Hurt
    "PKD_46": "hurtownia + palety + zaopatrzenie + dystrybutor + faktura vat",
    
    # Detal
    "PKD_47": "promocje + gazetka + biedronka + lidl + wyprzedaż",
    
    # Transport
    "PKD_49": "cena paliwa + diesel + giełda transportowa + spedycja + transport ciężarowy",
    
    # Turystyka
    "PKD_55": "wakacje + noclegi + booking + hotel + ferie",
    
    # IT
    "PKD_62": "praca it + programista + kurs python + strony www + b2b it"
}

OUTPUT_DIR = "Hacknation/data/processed"
OUTPUT_FILE = "soft_data.csv"

def fetch_google_trends():
    print("--- 1. Rozpoczynam pobieranie Google Trends (to może chwilę potrwać) ---")
    
    pytrends = TrendReq(hl='pl-PL', tz=360)
    all_trends = []

    for pkd, keyword in PKD_KEYWORDS_MAP.items():
        try:
            pytrends.build_payload([keyword], cat=0, timeframe='today 5-y', geo='PL', gprop='')
            data = pytrends.interest_over_time()

            if not data.empty:
                df = data.reset_index()
                df = df[['date', keyword]] # Bierzemy datę i wynik (0-100)
                df.columns = ['Data', 'Google_Trend_Score'] # Zmiana nazw kolumn
                df['Kod_PKD'] = pkd
                all_trends.append(df)
            else:
                print(f"   [!] Brak danych dla {keyword}")

            time.sleep(2.5)

        except Exception as e:
            print(f"   [!!!] Błąd przy {pkd}: {e}")
            print("   Spróbuj uruchomić skrypt ponownie za kilka minut.")

    if all_trends:
        return pd.concat(all_trends)
    else:
        return pd.DataFrame()

def fetch_macro_data():
    """Pobiera dane makroekonomiczne: Paliwa (Yahoo) + Symulacja WIBOR/Inflacja"""
    print("\n--- 2. Pobieranie danych Makroekonomicznych ---")
    
    # A. Ceny Paliw (Ropa Brent jako proxy kosztów energii dla przemysłu)
    # Symbol: BZ=F (Brent Crude Oil)
    print("   Pobieram ceny ropy (Yahoo Finance)...")
    oil_data = yf.download("BZ=F", period="5y", interval="1wk", progress=False)
    
    macro_df = oil_data['Close'].reset_index()
    macro_df.columns = ['Data', 'Cena_Paliwa']
    
    # Usunięcie strefy czasowej z daty (dla zgodności z Trends)
    macro_df['Data'] = macro_df['Data'].dt.tz_localize(None)

    print("   Uzupełniam dane o WIBOR i Inflację (Symulacja/Stałe)...")
    
    # Przyjmujemy uproszczenie na potrzeby modelu:
    # 2020-2021: Niskie stopy (~0.2%), 2022-2023: Wysokie (~5-6%), 2024-2025: ~5.8%
    # Tutaj dla uproszczenia kodu dajemy aktualną wartość, 
    # ale możesz tu wpiąć prawdziwy plik CSV, jeśli organizator go dostarczył.
    
    macro_df['WIBOR'] = 5.85    # Aktualny poziom
    macro_df['Inflacja'] = 4.5  # Szacunkowa inflacja
    
    return macro_df

def main():
    # --- POPRAWKA: Deklaracja global musi być na samym początku ---
    global OUTPUT_FILE, OUTPUT_DIR 
    
    print(f"Zapisuję dane do: {OUTPUT_DIR}")
    
    # Próba utworzenia katalogu, z fallbackiem
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
        except OSError:
            print("Nie mogę utworzyć folderu w podanej ścieżce. Zapiszę w bieżącym katalogu.")
            OUTPUT_DIR = "."
            OUTPUT_FILE = "soft_data.csv"

    trends_df = fetch_google_trends()
    macro_df = fetch_macro_data()

    if trends_df.empty:
        print("Błąd: Nie udało się pobrać trendów.")
        return

    print("\n--- 3. Łączenie danych ---")
    trends_df = trends_df.sort_values('Data')
    
    if not macro_df.empty and 'Data' in macro_df.columns:
        macro_df = macro_df.sort_values('Data')
        final_df = pd.merge_asof(trends_df, macro_df, on='Data', direction='nearest')
    else:
        print("Ostrzeżenie: Brak danych makro. Używam domyślnych.")
        final_df = trends_df
        final_df['WIBOR'] = 5.85
        final_df['Cena_Paliwa'] = 80.0

    wanted_cols = ['Data', 'Kod_PKD', 'Google_Trend_Score', 'WIBOR', 'Cena_Paliwa']
    final_cols = [c for c in wanted_cols if c in final_df.columns]
    final_df = final_df[final_cols]

    full_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    final_df.to_csv(full_path, index=False)
    
    print(f"SUKCES! Plik gotowy: {full_path}")
    print(final_df.head())

if __name__ == "__main__":
    main()