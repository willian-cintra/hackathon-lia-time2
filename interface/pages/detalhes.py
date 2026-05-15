import streamlit as st
import json
import os
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent.config import DRAFT_TICKETS_DIR, QUEUE_TICKETS_DIR, TICKETS_PATH

st.title("🔍 Fluxo de Entradas e Saídas")
st.markdown("Visualize o conteúdo original do ticket e o processamento realizado pela IA.")

@st.cache_data
def load_data():
    entradas_originais = {}
    if TICKETS_PATH.exists():
        with open(TICKETS_PATH, 'r', encoding='utf-8') as f:
            data_orig = json.load(f)
            entradas_originais = {t.get('ticket_id'): t for t in data_orig}

    paths = {
        'Draft (Rascunho Automático)':   os.path.join(str(DRAFT_TICKETS_DIR), '*.json'),
        'Queue (Fila de Especialistas)': os.path.join(str(QUEUE_TICKETS_DIR), '*.json'),
    }

    all_tickets = []
    for rota, path in paths.items():
        for file_path in glob.glob(path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    tid  = data.get('ticket_id')
                    if tid in entradas_originais:
                        data['entrada_original'] = entradas_originais[tid].get('text')
                        data['canal_original']   = entradas_originais[tid].get('channel')
                        data['perfil_original']  = entradas_originais[tid].get('requester_profile')
                    data['status_rota'] = rota
                    all_tickets.append(data)
                except json.JSONDecodeError:
                    pass
    return all_tickets

tickets_data = load_data()

if not tickets_data:
    st.warning("Nenhum ticket processado encontrado. Execute run_batch.py primeiro.")
else:
    st.markdown("### 🔍 Filtros")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        lista_ids = sorted([t.get('ticket_id') for t in tickets_data if t.get('ticket_id')])
        filtro_ids = st.multiselect("Filtrar por ID do Ticket", options=lista_ids, placeholder="Selecione os IDs")
    with col_f2:
        filtro_prio = st.multiselect("Filtrar por Prioridade", options=["Crítico", "Alto", "Médio", "Baixo"], placeholder="Selecione as Prioridades")

    tickets_filtrados = tickets_data.copy()
    if filtro_ids:
        tickets_filtrados = [t for t in tickets_filtrados if t.get('ticket_id') in filtro_ids]
    if filtro_prio:
        tickets_filtrados = [t for t in tickets_filtrados if t.get('priority') in filtro_prio]

    ordem_prio = {"Crítico": 0, "Alto": 1, "Médio": 2, "Baixo": 3}
    tickets_filtrados.sort(key=lambda x: ordem_prio.get(x.get('priority', 'Baixo'), 99))

    st.divider()
    st.write(f"Exibindo {len(tickets_filtrados)} de {len(tickets_data)} tickets.")

    for t in tickets_filtrados:
        prio  = t.get('priority', 'Baixo')
        cate  = t.get('category', 'Não identificada')
        emoji = "🔴" if prio == "Crítico" else "🟠" if prio == "Alto" else "🟡" if prio == "Médio" else "🟢"
        failsafe = bool(t.get('llm_error'))

        with st.expander(f"{emoji} {t.get('ticket_id', 'S/ID')} — {t.get('service_type', 'Geral')} ({prio})" + (" ⚠️" if failsafe else "")):

            if failsafe:
                st.warning(f"⚠️ **Fail-safe ativado:** {t.get('llm_error')}")

            col_in, col_meta = st.columns([2, 1])

            with col_in:
                st.subheader("📥 Entrada (tickets.json)")
                st.info(t.get('entrada_original') or t.get('text') or 'Texto não disponível.')

            with col_meta:
                st.subheader("⚙️ Classificação")
                st.write(f"**Canal:** {t.get('canal_original') or t.get('channel', '—')}")
                st.write(f"**Perfil:** {t.get('perfil_original') or t.get('requester_profile', '—')}")
                st.write(f"**Urgência:** {t.get('urgency', '—')}")
                st.write(f"**Impacto:** {t.get('impact', '—')}")
                st.write(f"**Fila:** `{t.get('queue', '—')}`")
                st.write(f"**Rota:** {t.get('status_rota', t.get('route_decision', '—'))}")

            st.markdown("**Justificativa Técnica:**")
            st.success(
                f"**Classificação:** O ticket foi identificado como **{cate}**. "
                f"**Prioridade:** Definida como **{prio}**.\n\n"
                f"**Análise detalhada:** {t.get('classification_justification', 'Sem justificativa adicional disponível.')}"
            )

            if t.get('draft_response'):
                st.markdown("**Sugestão de Resposta Gerada:**")
                st.markdown(f"""
                <div style="background-color:#f8f9fa;padding:20px;border-radius:10px;
                            border-left:5px solid #d1d8e0;color:#1a1c23;
                            white-space:pre-wrap;line-height:1.5;">
                {t.get('draft_response')}
                </div>
                """, unsafe_allow_html=True)

            st.divider()

if st.button("🔄 Recarregar dados"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("### Legenda\n🔴 Crítico | 🟠 Alto | 🟡 Médio | 🟢 Baixo")
