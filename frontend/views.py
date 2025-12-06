import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from frontend.components import metric_card

# --- WIDOK 1: RANKING ---
def render_ranking(df):
    st.markdown("#### 🏆 Zestawienie Kondycji Gospodarczej")
    
    if df.empty:
        st.warning("Brak danych.")
        return

    latest_date = df['Date'].max()
    df_curr = df[df['Date'] == latest_date].copy().sort_values("Final_Score", ascending=False)
    
    # 1. KPI GŁÓWNE
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Średnia Rynkowa", f"{df_curr['Final_Score'].mean():.1f}")
    with c2: metric_card("Lider Rynku", df_curr.iloc[0]['Branża'])
    with c3: metric_card("Zagrożony Sektor", df_curr.iloc[-1]['Branża'])

    st.write("") # Odstęp

    # 2. WYKRES I TABELA
    col_chart, col_tab = st.columns([3, 2])
    
    with col_chart:
        st.markdown("**Mapa Cieplna Branż**")
        fig = px.bar(
            df_curr.sort_values("Final_Score", ascending=True),
            x="Final_Score", y="Branża", orientation='h',
            text_auto='.1f',
            color="Final_Score",
            color_continuous_scale=["#b71c1c", "#f0f2f6", "#0d47a1"] # Red -> Grey -> PKO Blue
        )
        fig.update_layout(plot_bgcolor='white', height=600, xaxis=dict(range=[0,105]), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_tab:
        st.markdown("**Lista Szczegółowa**")
        st.dataframe(
            df_curr[['Branża', 'Ocena', 'Final_Score']],
            column_config={
                "Final_Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f")
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )

# --- WIDOK 2: DETALE ---
def render_details(master, preds, branze_dict):
    st.markdown("#### 📊 Analiza Wgłębi")
    
    opts = list(branze_dict.values())
    sel = st.selectbox("Wybierz branżę:", opts)
    pkd = [k for k,v in branze_dict.items() if v == sel][0]
    
    d_hist = master[master['PKD_Code'] == pkd].sort_values('Date')
    d_pred = preds[preds['PKD_Code'] == pkd].sort_values('Date') if not preds.empty else pd.DataFrame()
    
    if d_hist.empty:
        st.error("Brak danych historycznych.")
        return

    # Wykres
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d_hist['Date'], y=d_hist['Final_Score'], name='Historia', line=dict(color='#00305F', width=4)))
    
    if not d_pred.empty:
        last = d_hist.iloc[-1]
        # Łącznik
        dates = [last['Date']] + d_pred['Date'].tolist()
        vals = [last['Final_Score']] + d_pred['Final_Score'].tolist()
        fig.add_trace(go.Scatter(x=dates, y=vals, name='Prognoza AI', line=dict(color='#E91E63', width=3, dash='dash')))

    fig.update_layout(template="plotly_white", height=450, hovermode="x unified", title=f"Trend dla: {sel}")
    st.plotly_chart(fig, use_container_width=True)