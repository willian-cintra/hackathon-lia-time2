import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="AGETIC - Triagem Inteligente de Chamados de Suporte de TIC",
    layout="wide"
)

pagina_classificacao = st.Page(
    page="pages/classificacao.py",
    title="Aprovação da classificação do agente",
    icon="🛠️",
    default=True
)

pagina_relatorio = st.Page(
    page="pages/relatorio.py",
    title="Relatório CSV",
    icon="📊"
)

menu = st.navigation(
    {
        "Ações": [pagina_classificacao],
        "Dados": [pagina_relatorio]
    }
)

menu.run()