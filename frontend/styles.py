import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* Ukrycie hamburgera i stopki */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Fonty PKO */
        html, body, [class*="css"] {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }

        /* --- STYL NAWIGACJI (PILLS) --- */
        div[role="radiogroup"] {
            background-color: #11141d; /* Ciemne tło jak na screenie */
            padding: 6px;
            border-radius: 30px; /* Mocne zaokrąglenie */
            display: inline-flex;
            width: fit-content;
            margin-bottom: 25px;
            border: 1px solid #333;
        }
        
        /* Ukrywamy kółka inputów */
        div[role="radiogroup"] label > div:first-child {
            display: none;
        }
        
        /* Styl przycisków */
        div[role="radiogroup"] label {
            margin-right: 0px !important;
            padding: 10px 24px;
            border-radius: 24px;
            border: none;
            transition: all 0.3s ease;
            color: #8b949e; /* Szary tekst nieaktywny */
            font-weight: 500;
            background-color: transparent;
        }
        
        /* Efekt Hover */
        div[role="radiogroup"] label:hover {
            color: white;
        }

        /* Styl AKTYWNEGO przycisku (Streamlit dodaje atrybut data-checked) */
        div[role="radiogroup"] label[data-baseweb="radio"] > div {
             /* Hack: Streamlit trudno stylować selektywnie, ale to działa na kontener */
        }

        /* --- KPI CARDS --- */
        .metric-container {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .metric-label { font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px; }
        .metric-value { font-size: 32px; font-weight: 700; color: #00305F; margin: 10px 0; }
        .metric-delta { font-size: 14px; font-weight: 600; padding: 4px 10px; border-radius: 12px; }
        .delta-pos { background-color: #E8F5E9; color: #2E7D32; }
        .delta-neg { background-color: #FFEBEE; color: #C62828; }

        /* --- TABELA --- */
        .stDataFrame { border: none !important; }
    </style>
    """, unsafe_allow_html=True)