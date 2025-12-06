import streamlit as st
import pandas as pd
from frontend import styles, components, views

# --- KONFIGURACJA ---
st.set_page_config(page_title="Indeks Branż", page_icon="🏦", layout="wide")
styles.load_css() # Ładujemy style z frontend/styles.py

# --- DANE ---
BRANZE_MAPA = {
    1: "Rolnictwo", 10: "Produkcja Żywności", 16: "Produkcja Drewna",
    23: "Produkcja Minerałów", 24: "Produkcja Metali", 29: "Motoryzacja",
    31: "Meblarstwo", 35: "Energetyka", 41: "Budownictwo",
    46: "Handel Hurtowy", 47: "Handel Detaliczny", 49: "Transport",
    55: "HoReCa", 62: "Technologie / IT", 68: "Nieruchomości"
}

def get_ocena(s):
    if s >= 80: return "Bardzo Dobra"
    if s >= 60: return "Dobra"
    if s >= 40: return "Przeciętna"
    return "Ryzykowna"

@st.cache_data
def load_data():
    m = pd.DataFrame()
    p = pd.DataFrame()
    try:
        m = pd.read_csv("data/processed/MASTER_DATA.csv")
        m['Date'] = pd.to_datetime(m['Date'])
        if 'PKD_Code' in m.columns: m['Branża'] = m['PKD_Code'].map(BRANZE_MAPA)
        if 'PKO_SCORE_FINAL' in m.columns: m['Final_Score'] = m['PKO_SCORE_FINAL']
        elif 'Final_Score' not in m.columns: m['Final_Score'] = 50.0
        m['Ocena'] = m['Final_Score'].apply(get_ocena)
    except: pass
    
    try:
        p = pd.read_csv("data/processed/predictions.csv")
        p['Date'] = pd.to_datetime(p['Date'])
        if 'PKD_Code' in p.columns: p['Branża'] = p['PKD_Code'].map(BRANZE_MAPA)
        if 'Predicted_Score' in p.columns: p['Final_Score'] = p['Predicted_Score']
    except: pass
    return m, p

# --- APP FLOW ---
def main():
    master_df, preds_df = load_data()
    
    # 1. Nawigacja (z frontend/components.py)
    page = components.navbar()
    
    # 2. Router (z frontend/views.py)
    if page == "Ranking Liderów":
        views.render_ranking(master_df)
    elif page == "Analiza Sektorowa":
        views.render_details(master_df, preds_df, BRANZE_MAPA)
    elif page == "Metodologia":
        st.info("Tutaj opis metodologii...")

if __name__ == "__main__":
    main()