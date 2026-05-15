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
    title="Aprovação de rascunho",
    icon="🛠️"
)

pagina_classificacaoqueue = st.Page(
    page="pages/classificacaoqueue.py",
    title="Aprovação da classificação do agente",
    icon="🛠️",
    default=True
)

pagina_relatoriocsv = st.Page(
    page="pages/relatoriocsv.py",
    title="Relatório CSV",
    icon="📊"
)

pagina_relatoriodistribuicao = st.Page(
    page="pages/relatoriodistribuicao.py",
    title="Relatório de distribuição",
    icon="📊"
)

menu = st.navigation(
    {
        "Ações": [pagina_classificacao,pagina_classificacaoqueue],
        "Dados": [pagina_relatoriocsv,pagina_relatoriodistribuicao]
    }
)

menu.run()