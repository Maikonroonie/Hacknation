import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Indeks Branż PKO BP",
    page_icon="📈",
    layout="wide"
)

# --- 2. TYTUŁ I HEADER ---
st.title("🏦 Indeks Koniunktury Branżowej")
st.markdown("**System wczesnego ostrzegania i oceny ryzyka sektorowego**")
st.markdown("---")

# --- 3. PANEL BOCZNY (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Panel Sterowania")
    
    # Wybór branży (Dropdown)
    wybrana_branza = st.selectbox(
        "Wybierz sektor do analizy:",
        ["Budownictwo", "Transport", "HoReCa", "Handel Detaliczny", "IT / Usługi"]
    )
    
    st.info(f"Analizujesz: **{wybrana_branza}**")
    st.write("Wersja: v1.0 (Hackathon)")

# --- 4. GENEROWANIE DANYCH (MOCK DATA - TYMCZASOWE) ---
# To symuluje dane, dopóki koledzy nie podeślą plików CSV
def get_mock_data():
    dates = pd.date_range(start="2023-01-01", periods=24, freq="ME")
    base_score = np.random.randint(50, 80)
    # Tworzymy losowy wykres
    random_walk = np.cumsum(np.random.randn(24) * 2) 
    scores = np.clip(base_score + random_walk, 0, 100)
    
    df = pd.DataFrame({"Data": dates, "Score": scores})
    return df

# Pobieramy dane
df = get_mock_data()
current_score = df["Score"].iloc[-1]
prev_score = df["Score"].iloc[-2]
delta = current_score - prev_score

# --- 5. GŁÓWNE LICZNIKI (KPI) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Aktualny Indeks Kondycji (0-100)", 
        value=f"{current_score:.1f}", 
        delta=f"{delta:.1f} m/m"
    )

with col2:
    ryzyko = "Wysokie 🔴" if current_score < 50 else "Niskie 🟢"
    st.metric(label="Ocena Ryzyka", value=ryzyko)

with col3:
    st.metric(label="Sentyment Mediów", value="Pozytywny 👍", delta="+12% wzmianek")

# --- 6. WYKRES (PLOTLY) ---
st.subheader(f"📊 Przebieg historyczny i prognoza: {wybrana_branza}")

fig = go.Figure()

# Linia historii (Granatowa)
fig.add_trace(go.Scatter(
    x=df['Data'], 
    y=df['Score'],
    mode='lines+markers',
    name='Historia (Dane twarde)',
    line=dict(color='#00305F', width=3)
))

# Linia prognozy (Czerwona przerywana)
future_dates = pd.date_range(start=df['Data'].iloc[-1], periods=7, freq="ME")
future_scores = [current_score + (i * np.random.randn()) for i in range(7)]

fig.add_trace(go.Scatter(
    x=future_dates,
    y=future_scores,
    mode='lines',
    name='Prognoza AI (12 msc)',
    line=dict(color='red', width=2, dash='dash')
))

fig.update_layout(
    xaxis_title="Data",
    yaxis_title="Wartość Indeksu",
    template="plotly_white",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# --- 7. ALARMY I KOMENTARZE ---
st.subheader("⚠️ Sygnały Ostrzegawcze")
c1, c2 = st.columns(2)

with c1:
    st.error("📉 **Koszt Energii:** Wzrost o 15% r/r obniża marże w tym sektorze.")
    st.warning("⚖️ **Legislacja:** Nowe wymogi UE wchodzą w życie od przyszłego kwartału.")

with c2:
    with st.expander("🔍 Zobacz analizę sentymentu (Google Trends)"):
        st.write("Najczęściej wyszukiwane frazy negatywne:")
        st.code(["upadłość", "długi", "zatory płatnicze"])
        st.progress(65, text="Natężenie negatywnych newsów: 65%")