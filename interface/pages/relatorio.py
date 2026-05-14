import streamlit as st
import pandas as pd
import os
from agent.config import RESULTS_CSV_PATH

TITLE       = "Relatório CSV"
ARQUIVO_CSV = str(RESULTS_CSV_PATH)

st.title("📊 " + TITLE)


@st.cache_data
def carregar_dados(caminho):
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return None


df = carregar_dados(ARQUIVO_CSV)

if df is not None:
    st.caption(f"Total de registros encontrados: {len(df)}")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("🔄 Recarregar CSV"):
        st.cache_data.clear()
        st.rerun()
else:
    st.warning(f"O arquivo CSV não foi encontrado no caminho: `{ARQUIVO_CSV}`")