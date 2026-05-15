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

df_raw = carregar_dados(ARQUIVO_CSV)

if df_raw is not None:
    st.write("### 🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)

    # Função auxiliar para extrair as opções únicas e adicionar o "Selecionar tudo"
    def obter_opcoes(coluna):
        if coluna in df_raw.columns:
            # Converte para string para evitar problemas caso existam dados mistos ou nulos
            valores = sorted([str(v) for v in df_raw[coluna].dropna().unique()])
            return ["Selecionar tudo"] + valores
        return ["Selecionar tudo"]

    with col1:
        filtro_ticket = st.multiselect(
            "Ticket ID", 
            options=obter_opcoes('ticket_id'),
            placeholder="Selecione as opções"
        )
    with col2:
        filtro_categoria = st.multiselect(
            "Categoria", 
            options=obter_opcoes('category'),
            placeholder="Selecione as opções"
        )
    with col3:
        filtro_prioridade = st.multiselect(
            "Prioridade", 
            options=obter_opcoes('priority'),
            placeholder="Selecione as opções"
        )
    with col4:
        filtro_servico = st.multiselect(
            "Tipo de Serviço", 
            options=obter_opcoes('service_type'),
            placeholder="Selecione as opções"
        )
    with col5:
        # O Nível agora puxa da coluna 'queue' conforme solicitado
        filtro_level = st.multiselect(
            "Nível", 
            options=obter_opcoes('queue'),
            placeholder="Selecione as opções"
        )

    # Aplicação da lógica de filtragem
    df_filtrado = df_raw.copy()

    # Só filtra se o usuário selecionou algo E se a opção "Selecionar tudo" NÃO estiver entre as escolhas
    if filtro_ticket and "Selecionar tudo" not in filtro_ticket:
        df_filtrado = df_filtrado[df_filtrado['ticket_id'].astype(str).isin(filtro_ticket)]
        
    if filtro_categoria and "Selecionar tudo" not in filtro_categoria:
        df_filtrado = df_filtrado[df_filtrado['category'].astype(str).isin(filtro_categoria)]
        
    if filtro_prioridade and "Selecionar tudo" not in filtro_prioridade:
        df_filtrado = df_filtrado[df_filtrado['priority'].astype(str).isin(filtro_prioridade)]
        
    if filtro_servico and "Selecionar tudo" not in filtro_servico:
        df_filtrado = df_filtrado[df_filtrado['service_type'].astype(str).isin(filtro_servico)]
        
    if filtro_level and "Selecionar tudo" not in filtro_level:
        df_filtrado = df_filtrado[df_filtrado['queue'].astype(str).isin(filtro_level)]

    st.divider()
    
    # Exibição dos resultados
    st.caption(f"Mostrando {len(df_filtrado)} de {len(df_raw)} registros encontrados.")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

else:
    st.warning(f"O arquivo CSV não foi encontrado no caminho: `{ARQUIVO_CSV}`")