import streamlit as st

def navbar():
    """Generuje nawigację na górze w stylu Pills"""
    # Używamy kontenera, żeby wycentrować lub dać tło
    st.markdown("### Indeks Branż PKO BP")
    
    # Menu poziome
    selected = st.radio(
        "Nawigacja",
        ["Ranking Liderów", "Analiza Sektorowa", "Metodologia"],
        horizontal=True,
        label_visibility="collapsed",
        key="nav_main"
    )
    return selected

def metric_card(label, value, delta=None):
    """Customowy HTML dla KPI"""
    delta_html = ""
    if delta:
        try:
            d_val = float(delta)
            cls = "delta-pos" if d_val >= 0 else "delta-neg"
            sign = "+" if d_val > 0 else ""
            delta_html = f'<span class="metric-delta {cls}">{sign}{d_val:.2f} r/r</span>'
        except: pass
        
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)