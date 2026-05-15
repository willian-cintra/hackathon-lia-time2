import streamlit as st
import pandas as pd
import json
import os
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent.config import DRAFT_TICKETS_DIR, QUEUE_TICKETS_DIR

st.title("🗂️ Análise por Tipo | Categoria | Nível")
st.markdown("Distribuição dos chamados de acordo com a classificação feita pela IA.")

@st.cache_data
def load_category_data():
    tickets = []

    for file_path in glob.glob(os.path.join(str(DRAFT_TICKETS_DIR), '*.json')):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                data['rota_final'] = 'Draft (Rascunho)'
                tickets.append(data)
            except json.JSONDecodeError:
                pass

    for file_path in glob.glob(os.path.join(str(QUEUE_TICKETS_DIR), '*.json')):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                data['rota_final'] = 'Queue (Fila Humana)'
                tickets.append(data)
            except json.JSONDecodeError:
                pass

    return pd.DataFrame(tickets) if tickets else None

df_tickets = load_category_data()

if df_tickets is not None and not df_tickets.empty:
    cat_col = 'category'     if 'category'     in df_tickets.columns else None
    pri_col = 'priority'     if 'priority'      in df_tickets.columns else None
    svc_col = 'service_type' if 'service_type'  in df_tickets.columns else None
    id_col  = 'ticket_id'    if 'ticket_id'     in df_tickets.columns else None

    if 'queue' in df_tickets.columns:
        df_tickets['nivel_identificado'] = df_tickets['queue'].astype(str)

    if cat_col:
        df_categorias = df_tickets[cat_col].value_counts().reset_index()
        df_categorias.columns = ['Categoria', 'Quantidade Total']

        qtd_baixo   = len(df_tickets[df_tickets[pri_col].astype(str).str.lower() == 'baixo'])   if pri_col else 0
        qtd_critico = len(df_tickets[df_tickets[pri_col].astype(str).str.lower() == 'crítico']) if pri_col else 0

        num_indicadores = len(df_categorias) + 2
        cols = st.columns(num_indicadores)
        for index, row in df_categorias.iterrows():
            cols[index].metric(str(row['Categoria']).capitalize(), str(row['Quantidade Total']))
        cols[len(df_categorias)].metric("Nível Baixo", str(qtd_baixo))
        cols[len(df_categorias) + 1].metric("Nível Crítico", str(qtd_critico))

        st.divider()

        st.subheader("Distribuição por Tipo de Serviço")
        if svc_col:
            df_svc = df_tickets[svc_col].value_counts().reset_index()
            df_svc.columns = ['Tipo de Serviço', 'Quantidade']
            st.bar_chart(df_svc.set_index("Tipo de Serviço"), color="#00cc96")

        st.divider()

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Categoria vs Prioridade")
            if pri_col:
                df_cat_pri = df_tickets.groupby([cat_col, pri_col]).size().unstack(fill_value=0)
                st.bar_chart(df_cat_pri)
        with col_g2:
            st.subheader("Separação por Nível")
            if 'nivel_identificado' in df_tickets.columns:
                df_niveis = df_tickets['nivel_identificado'].value_counts().reset_index()
                df_niveis.columns = ['Nível', 'Quantidade']
                st.bar_chart(df_niveis.sort_values('Nível').set_index("Nível"), color="#ffaa00")

        st.divider()
        st.subheader("Detalhamento dos Tickets Processados")
        st.markdown("### 🔍 Filtros da Tabela")

        f_col1, f_col2, f_col3 = st.columns(3)
        f_col4, f_col5 = st.columns(2)
        df_filtered = df_tickets.copy()

        with f_col1:
            if id_col:
                ids = st.multiselect("ID Ticket", options=sorted(df_tickets[id_col].unique()), placeholder="Selecione as Opções")
                if ids: df_filtered = df_filtered[df_filtered[id_col].isin(ids)]
        with f_col2:
            if cat_col:
                cats = st.multiselect("Categoria", options=sorted(df_tickets[cat_col].unique()), placeholder="Selecione as Opções")
                if cats: df_filtered = df_filtered[df_filtered[cat_col].isin(cats)]
        with f_col3:
            if pri_col:
                pris = st.multiselect("Prioridade", options=sorted(df_tickets[pri_col].unique()), placeholder="Selecione as Opções")
                if pris: df_filtered = df_filtered[df_filtered[pri_col].isin(pris)]
        with f_col4:
            if svc_col:
                svcs = st.multiselect("Tipo de Serviço", options=sorted(df_tickets[svc_col].unique()), placeholder="Selecione as Opções")
                if svcs: df_filtered = df_filtered[df_filtered[svc_col].isin(svcs)]
        with f_col5:
            if 'nivel_identificado' in df_tickets.columns:
                nivs = st.multiselect("Nível", options=sorted(df_tickets['nivel_identificado'].unique()), placeholder="Selecione as Opções")
                if nivs: df_filtered = df_filtered[df_filtered['nivel_identificado'].isin(nivs)]

        if pri_col:
            ordem = ['Crítico', 'Alto', 'Médio', 'Baixo']
            df_filtered[pri_col] = pd.Categorical(df_filtered[pri_col], categories=ordem, ordered=True)
            df_filtered = df_filtered.sort_values(by=pri_col)

        cols_to_show = []
        if id_col: cols_to_show.append(id_col)
        for c in [cat_col, pri_col, svc_col, 'rota_final', 'nivel_identificado']:
            if c and c in df_filtered.columns:
                cols_to_show.append(c)

        st.write(f"Exibindo {len(df_filtered)} de {len(df_tickets)} tickets.")
        st.dataframe(df_filtered[cols_to_show], use_container_width=True)
    else:
        st.error("Coluna de categoria não localizada.")
else:
    st.warning("Nenhum ticket encontrado. Execute run_batch.py primeiro.")

if st.button("🔄 Recarregar dados"):
    st.cache_data.clear()
    st.rerun()
