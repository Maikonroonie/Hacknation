import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Indeks Branż PKO BP",
    page_icon="🏦",
    layout="wide"
)

# --- 2. STAŁE I SŁOWNIKI ---
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

# --- 3. FUNKCJE POMOCNICZE (BACKEND) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/processed/MASTER_DATA.csv")
        df['Date'] = pd.to_datetime(df['Date'])
        # Dodajemy kolumnę z nazwą branży dla czytelności
        df['Branża'] = df['PKD_Code'].map(BRANZE_MAPA)
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def get_risk_grade(score):
    if score >= 80: return "A (Bardzo Bezpieczna)", "🟢"
    if score >= 60: return "B (Stabilna)", "🔵"
    if score >= 40: return "C (Podwyższone Ryzyko)", "🟡"
    return "D (Zagrożona)", "🔴"

# --- 4. WIDOK 1: RANKING (NOWOŚĆ!) ---
def render_ranking(df):
    st.header("🏆 Ranking Kondycji Branż (Toplist)")
    st.markdown("Zestawienie sektorów wg `PKO Index Score` na podstawie najnowszych danych.")
    
    # 1. Bierzemy tylko najnowszy miesiąc dla każdej branży
    latest_date = df['Date'].max()
    df_latest = df[df['Date'] == latest_date].copy()
    
    # 2. Sortujemy od najlepszej
    df_ranked = df_latest.sort_values(by="PKO_SCORE_FINAL", ascending=False).reset_index(drop=True)
    df_ranked['Pozycja'] = df_ranked.index + 1
    
    # --- TOP 3 KAFELKI ---
    col1, col2, col3 = st.columns(3)
    if len(df_ranked) >= 3:
        with col1:
            st.info(f"🥇 Lider Rynku: **{df_ranked.iloc[0]['Branża']}**\n\nScore: {df_ranked.iloc[0]['PKO_SCORE_FINAL']:.1f}")
        with col2:
            st.success(f"🥈 Wicelider: **{df_ranked.iloc[1]['Branża']}**\n\nScore: {df_ranked.iloc[1]['PKO_SCORE_FINAL']:.1f}")
        with col3:
            st.warning(f"🥉 Trzecie miejsce: **{df_ranked.iloc[2]['Branża']}**\n\nScore: {df_ranked.iloc[2]['PKO_SCORE_FINAL']:.1f}")

    # --- WYKRES SŁUPKOWY ---
    st.subheader("📊 Porównanie Branż")
    fig = px.bar(
        df_ranked, 
        x="PKO_SCORE_FINAL", 
        y="Branża", 
        orientation='h',
        color="PKO_SCORE_FINAL",
        color_continuous_scale="RdYlGn", # Czerwony -> Zielony
        text_auto='.1f'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
    st.plotly_chart(fig, use_container_width=True)

    # --- TABELA SZCZEGÓŁOWA ---
    st.subheader("📋 Tabela Wyników")
    # Wybieramy tylko ważne kolumny do wyświetlenia
    display_cols = ['Branża', 'PKO_SCORE_FINAL', 'Rev_Growth_YoY', 'Profit_Margin', 'Google_Trends', 'Bankruptcy_Rate']
    
    st.dataframe(
        df_ranked[display_cols],
        column_config={
            "PKO_SCORE_FINAL": st.column_config.ProgressColumn(
                "PKO Score",
                help="Wynik algorytmu (0-100)",
                format="%.1f",
                min_value=0,
                max_value=100,
            ),
            "Rev_Growth_YoY": st.column_config.NumberColumn("Wzrost Przych. %", format="%.1f%%"),
            "Profit_Margin": st.column_config.NumberColumn("Marża %", format="%.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

# --- 5. WIDOK 2: SZCZEGÓŁY (TO CO MIAŁEŚ WCZEŚNIEJ) ---
def render_details(df):
    st.header("🔍 Analiza Szczegółowa Sektora")
    
    # Sidebar lokalny dla tego widoku
    opcje_nazwy = list(BRANZE_MAPA.values())
    wybrana_nazwa = st.selectbox("Wybierz sektor do prześwietlenia:", opcje_nazwy)
    wybrany_kod = [k for k, v in BRANZE_MAPA.items() if v == wybrana_nazwa][0]
    
    df_sector = df[df['PKD_Code'] == wybrany_kod].sort_values('Date')
    latest = df_sector.iloc[-1]
    prev = df_sector.iloc[-2]
    
    # KPI
    c1, c2, c3, c4 = st.columns(4)
    score = latest['PKO_SCORE_FINAL']
    grade, icon = get_risk_grade(score)
    
    c1.metric("Indeks PKO", f"{score:.1f}", f"{score - prev['PKO_SCORE_FINAL']:.1f}")
    c2.metric("Ocena Ryzyka", grade, icon)
    c3.metric("Wzrost Przych. r/r", f"{latest['Rev_Growth_YoY']:.1f}%")
    c4.metric("Marża Zysku", f"{(latest['Profit_Margin']*100):.1f}%") # Poprawka na procenty
    
    # Wykresy (Radar + Historia)
    c_left, c_right = st.columns([1, 2])
    
    with c_left:
        categories = ['Rentowność', 'Wzrost', 'Sentyment (Google)', 'Bezpieczeństwo']
        values = [latest['Norm_Profit_Margin'], latest['Norm_Rev_Growth_YoY'], latest['Norm_Google_Trends'], latest['Norm_Bankruptcy_Rate']]
        fig_radar = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill='toself', marker_color='#00305F'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig_radar, use_container_width=True)
        
    with c_right:
        fig_line = px.line(df_sector, x='Date', y='PKO_SCORE_FINAL', title='Historia Kondycji Branży')
        fig_line.add_hline(y=50, line_dash="dash", line_color="red")
        fig_line.update_traces(line_color='#00305F', line_width=3)
        st.plotly_chart(fig_line, use_container_width=True)

# --- 6. MAIN (ROUTER) ---
def main():
    df = load_data()
    
    if df.empty:
        st.error("Brak danych! Upewnij się, że plik MASTER_DATA.csv istnieje.")
        return

    # Sidebar - Globalna Nawigacja
    with st.sidebar:
        # Zamiast obrazka, dajemy ładny nagłówek. To się nie zepsuje.
        st.header("🏦 PKO Bank Polski")
        st.write("---")
        # To jest Twój Navbar
        page = st.radio("Nawigacja", ["🏆 Ranking Liderów", "📊 Analiza Szczegółowa"], index=0)
        st.write("---")
        st.caption("HackNation v1.0")

    # Routing - Wybór widoku
    if page == "🏆 Ranking Liderów":
        render_ranking(df)
    elif page == "📊 Analiza Szczegółowa":
        render_details(df)

if __name__ == "__main__":
    main()