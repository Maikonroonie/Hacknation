import pandas as pd
import os

def getScores():
    # 1. Pobierz folder, w którym leży TEN skrypt (czyli .../data/graph/prep)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Sklej ścieżkę:
    # script_dir -> wyjdź z 'prep' (..) -> wyjdź z 'graph' (..) -> wejdź do 'processed'
    file_path = os.path.join(script_dir, '..', '..', 'processed', 'MASTER_DATA.csv')
    
    # (Opcjonalnie) normpath "wyczyści" ścieżkę, żeby nie wyglądała dziwnie z kropkami
    file_path = os.path.normpath(file_path)

    print(f"Szukam pliku tutaj: {file_path}") # Dla pewności zobaczysz, gdzie szuka

    try:
        # dtype={'PKD_Code': str} jest kluczowe!
        df = pd.read_csv(file_path, dtype={'PKD_Code': str})

        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by='Date', ascending=False)
        latest_df = df.drop_duplicates(subset='PKD_Code', keep='first')
        
        pkd_score_dict = dict(zip(latest_df['PKD_Code'], latest_df['PKO_SCORE_FINAL']))

        print("Wygenerowany słownik:")
        print(pkd_score_dict)
        return pkd_score_dict # Warto zwrócić słownik, żeby użyć go w innej funkcji

    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku. Sprawdź czy plik jest w 'data/processed/'.")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")

# Wywołanie testowe
if __name__ == "__main__":
    getScores()