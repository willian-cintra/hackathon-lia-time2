import streamlit as st
import pandas as pd
import json
import os
import glob

st.set_page_config(page_title="Detalhamento de Fluxo - AGETIC", layout="wide")

st.title("🔍 Fluxo de Entradas e Saídas")
st.markdown("Visualize o conteúdo original do ticket e o processamento realizado pela IA.")

@st.cache_data
def load_data():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    
    # Carrega a fonte da verdade para as entradas
    tickets_json_path = os.path.join(base_dir, 'data/tickets.json')
    entradas_originais = {}
    if os.path.exists(tickets_json_path):
        with open(tickets_json_path, 'r', encoding='utf-8') as f:
            data_orig = json.load(f)
            # Mapeia ticket_id -> objeto completo do ticket
            entradas_originais = {t.get('ticket_id'): t for t in data_orig}

    # Carrega os resultados processados
    outputs_dir = os.path.join(base_dir, 'outputs/tickets')
    paths = {
        'Draft (Rascunho Automático)': os.path.join(outputs_dir, 'draft', '*.json'),
        'Queue (Fila de Especialistas)': os.path.join(outputs_dir, 'queue', '*.json')
    }
    
    all_tickets = []
    for rota, path in paths.items():
        for file_path in glob.glob(path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    tid = data.get('ticket_id')
                    
                    if tid in entradas_originais:
                        data['entrada_original'] = entradas_originais[tid].get('text')
                        data['canal_original'] = entradas_originais[tid].get('channel')
                        data['perfil_original'] = entradas_originais[tid].get('requester_profile')
                    
                    data['status_rota'] = rota
                    all_tickets.append(data)
                except json.JSONDecodeError:
                    pass
    return all_tickets

tickets_data = load_data()

if not tickets_data:
    st.warning("Nenhum ticket processado encontrado.")
else:
    # --- SEÇÃO DE FILTROS ---
    st.markdown("### 🔍 Filtros")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        lista_ids = sorted([t.get('ticket_id') for t in tickets_data if t.get('ticket_id')])
        filtro_ids = st.multiselect("Filtrar por ID do Ticket", options=lista_ids, placeholder="Selecione os IDs")
    
    with col_f2:
        lista_prioridades = ["Crítico", "Alto", "Médio", "Baixo"]
        filtro_prio = st.multiselect("Filtrar por Prioridade", options=lista_prioridades, placeholder="Selecione as Prioridades")

    # Aplicação dos filtros
    tickets_filtrados = tickets_data.copy()
    if filtro_ids:
        tickets_filtrados = [t for t in tickets_filtrados if t.get('ticket_id') in filtro_ids]
    if filtro_prio:
        tickets_filtrados = [t for t in tickets_filtrados if t.get('priority') in filtro_prio]

    # Ordenação (Crítico primeiro)
    ordem_prio = {"Crítico": 0, "Alto": 1, "Médio": 2, "Baixo": 3}
    tickets_filtrados.sort(key=lambda x: ordem_prio.get(x.get('priority', 'Baixo'), 99))

    st.divider()

    # --- EXIBIÇÃO DOS TICKETS ---
    for t in tickets_filtrados:
        prio = t.get('priority', 'Baixo')
        cate = t.get('category', 'Não identificada')
        emoji = "🔴" if prio == "Crítico" else "🟠" if prio == "Alto" else "🟡" if prio == "Médio" else "🟢"
        
        with st.expander(f"{emoji} {t.get('ticket_id', 'S/ID')} - {t.get('service_type', 'Geral')} ({prio})"):
            
            col_in, col_meta = st.columns([2, 1])
            
            with col_in:
                st.subheader("📥 Entrada (tickets.json)")
                st.info(t.get('entrada_original', 'Texto não encontrado no tickets.json'))
            
            with col_meta:
                st.subheader("⚙️ Classificação")
                st.write(f"**Perfil:** {t.get('perfil_original', '—')}")
                st.write(f"**Fila:** `{t.get('queue', '—')}`")
                st.write(f"**Rota:** {t.get('status_rota')}")

            st.markdown("**Justificativa Técnica:**")
            texto_justificativa = (
                f"**Classificação:** O ticket foi identificado como **{cate}**. "
                f"**Prioridade:** Definida como **{prio}**. \n\n"
                f"**Análise detalhada:** {t.get('classification_justification', 'Sem justificativa adicional disponível.')}"
            )
            st.success(texto_justificativa)
            
            if t.get('draft_response'):
                st.markdown("**Sugestão de Resposta Gerada:**")
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #d1d8e0; color: #1a1c23; white-space: pre-wrap; line-height: 1.5;">
                {t.get('draft_response')}
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()

st.sidebar.markdown("### Legenda\n🔴 Crítico | 🟠 Alto")
st.sidebar.markdown("🟡 Médio | 🟢 Baixo")