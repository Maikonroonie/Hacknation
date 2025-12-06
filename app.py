import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Indeks Branż PKO BP | AI Forecast",
    page_icon="🏦",
    layout="wide"
)

# --- 2. SŁOWNIK BRANŻ ---
BRANZE_MAPA = {
    1: "Rolnictwo (01)",
    10: "Produkcja Żywności (10)",
    16: "Produkcja Drewna (16)",
    23: "Produkcja Minerałów (23)",
    24: "Produkcja Metali (24)",
    29: "Produkcja Pojazdów (29)",
    31: "Produkcja Mebli (31)",
    35: "Energetyka (35)",
    41: "Budownictwo (41)",
    46: "Handel Hurtowy (46)",
    47: "Handel Detaliczny (47)",
    49: "Transport Lądowy (49)",
    55: "Zakwaterowanie / HoReCa (55)",
    62: "IT / Oprogramowanie (62)",
    68: "Obsługa Nieruchomości (68)"
}

# Funkcja pomocnicza do oceny (używana dla obu zbiorów danych)
def ocen_klase(score):
    if pd.isna(score): return "Brak Danych ⚪"
    if score >= 80: return "Lider Rozwoju 🚀"
    if score >= 60: return "Stabilna ⚖️"
    if score >= 40: return "Obserwuj 🟡"
    return "Zagrożona ⚠️"

# --- 3. ŁADOWANIE DANYCH (WERSJA PANCERNA V2) ---
@st.cache_data
def load_data():
    master = pd.DataFrame()
    preds = pd.DataFrame()

    # --- A. Wczytanie Historii (MASTER_DATA) ---
    try:
        master = pd.read_csv("data/processed/MASTER_DATA.csv")
        master['Date'] = pd.to_datetime(master['Date'])
        
        # 1. Mapowanie Nazw
        if 'PKD_Code' in master.columns:
            master['Branża'] = master['PKD_Code'].map(BRANZE_MAPA)
        
        # 2. Naprawa kolumny Final_Score
        if 'PKO_SCORE_FINAL' in master.columns:
            master['Final_Score'] = master['PKO_SCORE_FINAL']
        elif 'Final_Score' not in master.columns:
            master['Final_Score'] = 50.0 # Awaryjnie

        # 3. WYMUSZENIE KOLUMNY 'KLASA' (To naprawia Twój błąd!)
        master['Klasa'] = master['Final_Score'].apply(ocen_klase)

        # 4. Uzupełnienie brakujących kolumn składowych (jeśli ich nie ma w CSV)
        cols_missing = ['Score_Finanse', 'Score_Sentyment', 'Score_Ryzyko']
        for col in cols_missing:
            if col not in master.columns:
                master[col] = master['Final_Score'] # Domyślnie równe średniej, żeby wykres działał

        master['Typ'] = 'Historia'
        
    except Exception as e:
        st.error(f"⚠️ Problem z plikiem historycznym: {e}")

    # --- B. Wczytanie Predykcji (predictions.csv) ---
    try:
        preds = pd.read_csv("data/processed/predictions.csv")
        preds['Date'] = pd.to_datetime(preds['Date'])
        
        if 'PKD_Code' in preds.columns:
            preds['Branża'] = preds['PKD_Code'].map(BRANZE_MAPA)
        
        # Mapowanie Score
        if 'Predicted_Score' in preds.columns:
            preds['Final_Score'] = preds['Predicted_Score']
        elif 'Final_Score' not in preds.columns:
            preds['Final_Score'] = 50.0

        # Generowanie Klasy dla predykcji
        preds['Klasa'] = preds['Final_Score'].apply(ocen_klase)
        
        # Uzupełnienie składowych dla predykcji
        for col in ['Score_Finanse', 'Score_Sentyment', 'Score_Ryzyko']:
            if col not in preds.columns:
                preds[col] = preds['Final_Score']

        preds['Typ'] = 'Prognoza'

    except Exception as e:
        st.warning(f"⚠️ Brak pliku predykcji lub błąd formatu: {e}")

    return master, preds

# Ładujemy dane globalnie
master, preds = load_data()

# --- 4. WIDOK: RANKING (MASZYNA CZASU) ---
def render_ranking():
    st.header("🏆 Ranking Kondycji Branż")
    
    if master.empty and preds.empty:
        st.error("Brak danych do wyświetlenia.")
        return

    # 1. Tworzymy wspólną listę dat
    dates_m = master['Date'] if not master.empty else pd.Series(dtype='datetime64[ns]')
    dates_p = preds['Date'] if not preds.empty else pd.Series(dtype='datetime64[ns]')
    
    all_dates = pd.concat([dates_m, dates_p]).dropna().unique()
    all_dates_sorted = sorted(all_dates, reverse=True)
    
    date_options = [pd.to_datetime(d).strftime('%Y-%m-%d') for d in all_dates_sorted]
    
    # Domyślna data: Ostatnia data historyczna (żeby pokazać "TERAZ")
    default_idx = 0
    if not master.empty:
        last_hist = master['Date'].max().strftime('%Y-%m-%d')
        if last_hist in date_options:
            default_idx = date_options.index(last_hist)

    # UI
    col_sel, col_info = st.columns([1, 3])
    with col_sel:
        sel_date_str = st.selectbox("📅 Wybierz moment w czasie:", date_options, index=default_idx)
    
    sel_date = pd.to_datetime(sel_date_str)
    
    # Decyzja: Historia czy Prognoza?
    max_hist = master['Date'].max() if not master.empty else pd.Timestamp.min
    is_forecast = sel_date > max_hist
    
    # Wybór odpowiedniego DataFrame
    if is_forecast:
        df_rank = preds[preds['Date'] == sel_date].copy()
        msg_type = "🔮 TRYB PROGNOZY (AI)"
        msg_color = "blue"
    else:
        df_rank = master[master['Date'] == sel_date].copy()
        msg_type = "📜 TRYB HISTORYCZNY"
        msg_color = "green"
        
    with col_info:
        if is_forecast:
            st.info(f"**{msg_type}:** Analizujesz przewidywania na dzień {sel_date_str}.")
        else:
            st.success(f"**{msg_type}:** Analizujesz twarde dane z dnia {sel_date_str}.")

    if df_rank.empty:
        st.warning("Brak danych dla wybranej daty.")
        return

    # Sortowanie
    df_rank = df_rank.sort_values(by="Final_Score", ascending=False).reset_index(drop=True)

    # Kafelki TOP 3
    c1, c2, c3 = st.columns(3)
    if len(df_rank) >= 3:
        with c1: st.success(f"🥇 **{df_rank.iloc[0]['Branża']}**\n\nScore: {df_rank.iloc[0]['Final_Score']:.1f}")
        with c2: st.info(f"🥈 **{df_rank.iloc[1]['Branża']}**\n\nScore: {df_rank.iloc[1]['Final_Score']:.1f}")
        with c3: st.warning(f"🥉 **{df_rank.iloc[2]['Branża']}**\n\nScore: {df_rank.iloc[2]['Final_Score']:.1f}")

    # Wykres
    st.markdown("### 📊 Porównanie Branż")
    
    # Paleta kolorów dla Klasy
    color_map = {
        "Lider Rozwoju 🚀": "#00CC00",
        "Stabilna ⚖️": "#00305F",
        "Obserwuj 🟡": "#FFC107",
        "Zagrożona ⚠️": "#FF4B4B"
    }
    
    fig = px.bar(
        df_rank, 
        x="Final_Score", 
        y="Branża", 
        orientation='h',
        color="Klasa", # Teraz ta kolumna na pewno istnieje!
        text_auto='.1f',
        color_discrete_map=color_map
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela
    with st.expander("Szczegółowa tabela"):
        st.dataframe(df_rank, use_container_width=True)

# --- 5. WIDOK: SZCZEGÓŁY (WYKRESY HYBRYDOWE) ---
def render_details():
    st.header("📈 Centrum Analityczne")
    
    opts = list(BRANZE_MAPA.values())
    sel = st.selectbox("Wybierz sektor:", opts)
    pkd = [k for k, v in BRANZE_MAPA.items() if v == sel][0]
    
    # Filtrowanie
    d_m = master[master['PKD_Code'] == pkd].sort_values('Date') if not master.empty else pd.DataFrame()
    d_p = preds[preds['PKD_Code'] == pkd].sort_values('Date') if not preds.empty else pd.DataFrame()
    
    # Ostatni punkt historii
    last_hist_row = d_m.iloc[-1] if not d_m.empty else None
    
    # KPI
    k1, k2, k3, k4 = st.columns(4)
    curr = last_hist_row['Final_Score'] if last_hist_row is not None else 0
    fut = d_p.iloc[-1]['Final_Score'] if not d_p.empty else 0
    
    k1.metric("Aktualny Wynik", f"{curr:.1f}")
    k2.metric("Prognoza (2026)", f"{fut:.1f}", delta=f"{fut-curr:.1f}")
    
    # --- WYKRES LINIOWY (HYBRYDOWY) ---
    c_main, c_radar = st.columns([2, 1])
    
    with c_main:
        st.markdown("#### 📅 Historia i Prognoza AI")
        fig = go.Figure()
        
        # 1. Historia
        if not d_m.empty:
            fig.add_trace(go.Scatter(
                x=d_m['Date'], y=d_m['Final_Score'],
                mode='lines', name='Historia',
                line=dict(color='#00305F', width=4)
            ))
            
        # 2. Prognoza (łączona)
        if not d_p.empty and last_hist_row is not None:
            # Tworzymy linię, która zaczyna się od ostatniego punktu historii
            # Żeby nie było dziury na wykresie
            p_dates = [last_hist_row['Date']] + d_p['Date'].tolist()
            p_scores = [last_hist_row['Final_Score']] + d_p['Final_Score'].tolist()
            
            fig.add_trace(go.Scatter(
                x=p_dates, y=p_scores,
                mode='lines', name='Prognoza AI',
                line=dict(color='#FF4B4B', width=3, dash='dot')
            ))
            
            # Przedział ufności (jeśli dostępny)
            if 'Confidence_Upper' in d_p.columns:
                # Dodajemy punkt startowy do przedziału ufności też (jako punkt zero uncertainty)
                upper = [last_hist_row['Final_Score']] + d_p['Confidence_Upper'].tolist()
                lower = [last_hist_row['Final_Score']] + d_p['Confidence_Lower'].tolist()
                
                fig.add_trace(go.Scatter(
                    x=p_dates + p_dates[::-1], # x tam i z powrotem
                    y=upper + lower[::-1],     # y góra i dół
                    fill='toself',
                    fillcolor='rgba(255, 75, 75, 0.15)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Przedział ufności (95%)',
                    showlegend=True
                ))

        fig.add_hline(y=50, line_dash="dash", line_color="gray")
        fig.update_layout(height=450, margin=dict(l=20,r=20,t=40,b=20), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    # --- RADAR ---
    with c_radar:
        st.markdown("#### 🕸️ Składowe Oceny")
        # Używamy danych z ostatniego punktu historii lub predykcji
        target_row = last_hist_row if not d_m.empty else (d_p.iloc[0] if not d_p.empty else None)
        
        if target_row is not None:
            cats = ['Finanse', 'Ryzyko (Niskie)', 'Sentyment']
            # Pobieramy wartości bezpiecznie (z domyślnym 50 jak brak)
            val_fin = target_row.get('Score_Finanse', target_row['Final_Score'])
            val_risk = target_row.get('Score_Ryzyko', target_row['Final_Score'])
            val_sent = target_row.get('Score_Sentyment', target_row['Final_Score'])
            
            vals = [val_fin, val_risk, val_sent]
            
            fig_r = go.Figure(data=go.Scatterpolar(
                r=vals, theta=cats, fill='toself', marker_color='#00305F'
            ))
            fig_r.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                height=350, margin=dict(t=40, b=40)
            )
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.info("Brak danych do wykresu radarowego.")

# --- 6. MAIN ---
def main():
    with st.sidebar:
        st.header("🏦 PKO Bank Polski")
        st.caption("System Analizy Branżowej v3.0")
        st.write("---")
        page = st.radio("Nawigacja", ["🏆 Ranking Liderów", "📊 Analiza Szczegółowa"])
        
    if page == "🏆 Ranking Liderów":
        render_ranking()
    elif page == "📊 Analiza Szczegółowa":
        render_details()

if __name__ == "__main__":
    main()