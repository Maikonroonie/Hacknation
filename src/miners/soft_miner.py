import pandas as pd
from pytrends.request import TrendReq
import yfinance as yf
import time
import os
from datetime import datetime


PKD_KEYWORDS_MAP = {
    # --- SEKTORY PRODUKCYJNE ---
    # Rolnictwo: koszty (nawozy) i przychody (pszenica/zboże)
    "PKD_01": "nawozy + cena pszenicy + skup zbóż + dopłaty bezpośrednie",
    
    # Spożywka: podstawowe produkty (masło/cukier) + hasła drożyzny
    "PKD_10": "cena masła + cena cukru + mąka + ceny żywności",
    
    # Drewno: surowiec (tarcica) + opał (pellet/drewno)
    "PKD_16": "drewno cena + tarcica + tartak + pellet + więźba dachowa",
    
    # Materiały budowlane: beton/cement (baza) + wykończeniówka (płytki/okna)
    "PKD_23": "cement cena + beton + styropian + cegła + pustak",
    
    # Metale: stal (pręty) + surowce wtórne (złom)
    "PKD_24": "stal cena + złom + pręty zbrojeniowe + aluminium cena",
    
    # Automotive: kupno auta + naprawy (części)
    "PKD_29": "salon samochodowy + toyota + skoda + mechanik + części samochodowe",
    
    # Meble: ogólne + konkretne (kuchnie/sofy)
    "PKD_31": "meble + kuchnia + szafa + ikea + agata meble",
    
    # Energetyka: rachunki (prąd/gaz) + inwestycje (fotowoltaika)
    "PKD_35": "cena prądu + taryfa g11 +pgnig + fotowoltaika + pompa ciepła",

    # --- BUDOWNICTWO I NIERUCHOMOŚCI ---
    # Budowlanka: plany (projekt) + finanse (kredyt) + wykonanie (budowa)
    "PKD_41": "budowa domu + projekt domu + kredyt hipoteczny + pozwolenie na budowę",
    
    # Nieruchomości: rynek wtórny (otodom/olx) + ceny + notariusz
    "PKD_68": "mieszkania na sprzedaż + wynajem + ceny mieszkań + otodom",

    # --- USŁUGI I LOGISTYKA ---
    # Hurt: typowe hasła biznesowe
    "PKD_46": "hurtownia + palety + zaopatrzenie + dystrybucja",
    
    # Detal: zakupy codzienne + promocje
    "PKD_47": "gazetka promocyjna + biedronka + lidl + wyprzedaż + galeria handlowa",
    
    # Transport: koszty (paliwo) + zlecenia
    "PKD_49": "cena paliwa + olej napędowy + giełda transportowa + trans + spedycja",
    
    # Turystyka: wczasy + hotele (booking)
    "PKD_55": "wakacje + hotel + noclegi + booking + biuro podróży",
    
    # IT: praca (najlepszy wskaźnik kondycji sektora) + nauka
    "PKD_62": "praca it + programista + kurs java + python + bootcamps"
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
    # 1. Stwórz katalog jeśli nie istnieje
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. Pobierz dane
    trends_df = fetch_google_trends()
    macro_df = fetch_macro_data()

    if trends_df.empty:
        print("Błąd: Nie udało się pobrać trendów. Sprawdź połączenie z internetem.")
        return

    # 3. Łączenie danych (Merge)
    print("\n--- 3. Łączenie danych i zapis ---")
    
    # Sortowanie po dacie
    trends_df = trends_df.sort_values('Data')
    macro_df = macro_df.sort_values('Data')

    # Używamy merge_asof, aby dopasować tygodniowe dane z Trends do tygodniowych z Yahoo
    # (nawet jeśli dni tygodnia się minimalnie różnią)
    final_df = pd.merge_asof(trends_df, macro_df, on='Data', direction='nearest')

    # Selekcja kolumn zgodnie z wymaganiem: 
    # Data | Kod_PKD | Google_Trend_Score | WIBOR | Cena_Paliwa
    final_cols = ['Data', 'Kod_PKD', 'Google_Trend_Score', 'WIBOR', 'Cena_Paliwa']
    final_df = final_df[final_cols]

    # Zapis
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    final_df.to_csv(output_path, index=False)
    
    print(f"SUKCES! Plik został zapisany w: {output_path}")
 

if __name__ == "__main__":
    main()