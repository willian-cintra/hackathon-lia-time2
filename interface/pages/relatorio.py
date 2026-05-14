import streamlit as st
import pandas as pd
import os

TITLE = "Relatório CSV"

# Configuração da página 
st.set_page_config(page_title=TITLE, page_icon="📊", layout="wide")

st.title(TITLE)

# Defina o caminho do seu CSV (volte uma pasta se o CSV estiver na raiz do projeto)
ARQUIVO_CSV = '../outputs/results.csv' 

# Função em cache para não recarregar o CSV pesado toda vez que interagir com a tela
@st.cache_data
def carregar_dados(caminho):
    if os.path.exists(caminho):
        # Lê o CSV e retorna um DataFrame do Pandas
        return pd.read_csv(caminho)
    return None

df = carregar_dados(ARQUIVO_CSV)

if df is not None:
    # Exibe um resumo rápido
    st.caption(f"Total de registros encontrados: {len(df)}")
    
    # st.dataframe exibe uma tabela interativa (permite ordenar, rolar e ajustar colunas)
    # st.table(df) exibiria uma tabela estática em HTML, mas é ruim para CSVs grandes
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Exemplo extra: Botão para limpar o cache se o CSV mudar em background
    if st.button("🔄 Recarregar CSV"):
        st.cache_data.clear()
        st.rerun()
else:
    st.warning(f"O arquivo CSV não foi encontrado no caminho: `{ARQUIVO_CSV}`")