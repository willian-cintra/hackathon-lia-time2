import streamlit as st

# Opcional: Configurações globais da página
st.set_page_config(page_title="AGETIC - Triagem Inteligente de Chamados de Suporte de TIC", layout="wide")


pagina_classificacao = st.Page(
    page="pages/classificacao.py", 
    title="Aprovação da classificação do agente", # O nome que vai aparecer no menu
    icon="🛠️", 
    default=True # Faz desta a página inicial ao abrir o site
)

pagina_relatorio = st.Page(
    page="pages/relatorio.py", 
    title="Relatório CSV", # O nome que vai aparecer no menu
    icon="📊"
)

# 2. Criação do menu de navegação lateral
# Você pode até agrupar por seções se quiser, passando um dicionário
menu = st.navigation(
    {
        "Ações": [pagina_classificacao],
        "Dados": [pagina_relatorio]
    }
)

# 3. Executa a página selecionada
menu.run()