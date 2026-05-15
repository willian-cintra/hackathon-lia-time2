import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="AGETIC - Triagem Inteligente de Chamados de Suporte de TIC",
    layout="wide"
)

# --- LÓGICA DE AUTENTICAÇÃO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    # Centralizando o formulário de login
    _, col_login, _ = st.columns([1, 2, 1])
    
    with col_login:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #008db8; margin-bottom: -10px;">AGETIC - UFMS</h1>
                <p style="color: #555;">Acesso Restrito ao Sistema de Triagem</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_login"):
            email = st.text_input("E-mail do Servidor", placeholder="exemplo@ufms.br")
            senha = st.text_input("Senha", type="password", placeholder="insira a senha")
            botao_entrar = st.form_submit_button("Acessar Sistema", use_container_width=True)
            
            if botao_entrar:
                if email == "servidor@ufms.br" and senha == "admin123":
                    st.session_state.autenticado = True
                    st.success("Acesso autorizado! Carregando painel...")
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")

# --- CONTROLE DE ACESSO ---
if not st.session_state.autenticado:
    # --- ALTERAÇÃO AQUI: Esconde o menu lateral enquanto não estiver logado ---
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            [data-testid="collapsedControl"] {display: none;}
        </style>
    """, unsafe_allow_html=True)
    
    tela_login()
else:
    # --- Sidebar - Botão Sair ---
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.autenticado = False
        st.rerun()

    # --- Suas Páginas Originais ---
    pagina_classificacao = st.Page(
        page="pages/classificacao.py",
        title="Aprovação da classificação do agente",
        icon="🛠️"
    )

    pagina_relatorio = st.Page(
        page="pages/relatorio.py",
        title="Relatório CSV",
        icon="📊"
    )

    # --- Suas Páginas Novas (Análise) ---
    pagina_dashboard = st.Page(
        page="pages/dashboard.py",
        title="Dashboard Estratégico",
        icon="📈"
    )

    pagina_categorias = st.Page(
        page="pages/categorias.py",
        title="Análise Geral dos Resultados",
        icon="🗂️"
    )

    pagina_detalhes = st.Page(
        page="pages/detalhes.py",
        title="Detalhamento de Fluxo",
        icon="🔍"
    )

    pagina_home = st.Page(
        page="pages/home.py",
        title="Home",  
        icon="🏠",
        default=True
    )

    # --- Navegação ---
    menu = st.navigation(
        {
            "Home": [pagina_home],
            "Ações": [pagina_classificacao],
            "Dados": [pagina_relatorio, pagina_detalhes],
            "Análise": [pagina_dashboard, pagina_categorias]
        }
    )

    # --- LÓGICA DE REDIRECIONAMENTO ---
    if st.session_state.get("menu_option") == "🏠 Tela Inicial (Kanban)":
        st.session_state["menu_option"] = None
        st.switch_page(pagina_home)

    menu.run()