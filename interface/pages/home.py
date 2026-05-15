import streamlit as st
import pandas as pd
import json
import os
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent.config import TICKETS_DIR, OUTPUTS_DIR, APROOVE_PATH, REJECT_PATH

# --- FUNÇÕES DE CARREGAMENTO ---
# Sem @st.cache_data: os dados mudam a cada aprovação, cache causava leitura desatualizada
def get_pending_stats():
    outputs_dir = str(TICKETS_DIR)
    
    drafts = glob.glob(os.path.join(outputs_dir, 'draft', '*.json'))
    queues = glob.glob(os.path.join(outputs_dir, 'queue', '*.json'))
    
    all_pending = []
    for f in drafts:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            data['origem'] = 'Draft (Rascunho)'
            all_pending.append(data)
            
    for f in queues:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            data['origem'] = 'Queue (Fila Humana)'
            all_pending.append(data)
    
    return drafts, queues, all_pending

def get_evaluated_stats():
    evaluated = []
    for filepath, status in [(str(APROOVE_PATH), 'Aprovado'), (str(REJECT_PATH), 'Rejeitado / Editado')]:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            item['status_avaliacao'] = status
                            evaluated.append(item)
                except json.JSONDecodeError:
                    pass
    return evaluated

# --- CABEÇALHO PERSONALIZADO ---
st.markdown("""
    <style>
        .block-container { padding-top: 4.5rem; }
    </style>
    <div style="margin-bottom: 25px; margin-top: -30px;">
        <h1 style="color: #008db8; font-family: 'Segoe UI', Arial, sans-serif; font-weight: 600; margin-bottom: -15px; font-size: 42px; letter-spacing: 0.5px;">AGETIC - UFMS</h1>
        <h3 style="color: #555555; font-family: 'Segoe UI', Arial, sans-serif; font-weight: 500; font-size: 20px; margin-top: 0px;">Agência de Tecnologia da Informação e Comunicação</h3>
    </div>
""", unsafe_allow_html=True)

st.markdown("### Bem-vindo(a), Servidor(a)!")
st.write("Resumo dos chamados que necessitam de sua análise técnica.")

# --- DADOS ---
# Lê direto do disco a cada renderização (sem cache), garantindo dados sempre atualizados
draft_files, queue_files, total_list = get_pending_stats()
evaluated_list = get_evaluated_stats()
total_pendente = len(total_list)

# --- MÉTRICAS ---
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Total Pendente", total_pendente)
c2.metric("Aguardando Rascunho (Draft)", len(draft_files))
c3.metric("Aguardando Fila (Queue)", len(queue_files))

# --- KANBAN BOARD ---
st.divider()
st.subheader("📋 Kanban de Processos")

prioridades_kanban = ["Crítico", "Alto", "Médio", "Baixo"]
col_k1, col_k2 = st.columns(2)

with col_k1:
    st.markdown("#### 📥 Para Análise")
    with st.container(height=550, border=True):
        for prio in prioridades_kanban:
            pendentes_prio = [t for t in total_list if t.get('priority') == prio]
            if pendentes_prio:
                st.markdown(f"**Prioridade: {prio}**")
                for t in pendentes_prio:
                    tid = t.get('ticket_id', 'S/ID')
                    with st.container(border=True):
                        st.write(f"**ID:** `{tid}`")
                        st.caption(f"{t.get('service_type', '—')} | {t.get('origem', '')}")
                        
                        # Botão de redirecionamento sem o use_container_width=True
                        if st.button("Analisar Agora", key=f"go_{tid}"):
                            st.session_state.ticket_id_focado = tid
                            st.switch_page("pages/classificacao.py")

with col_k2:
    st.markdown("#### ✅ Avaliados")
    with st.container(height=550, border=True):
        for prio in prioridades_kanban:
            avaliados_prio = [t for t in evaluated_list if t.get('priority') == prio]
            if avaliados_prio:
                st.markdown(f"**Prioridade: {prio}**")
                for t in avaliados_prio:
                    with st.container(border=True):
                        cor_status = "green" if "Aprovado" in t.get('status_avaliacao', '') else "red"
                        st.write(f"**ID:** `{t.get('ticket_id', 'S/ID')}`")
                        st.markdown(f":{cor_status}[**{t.get('status_avaliacao', '')}**]")

st.divider()
st.subheader("🛠️ Ações Rápidas")
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("Avaliar Fila Geral", use_container_width=True, type="primary"):
        st.switch_page("pages/classificacao.py")
with col_btn2:
    if st.button("Ver Histórico Completo", use_container_width=True):
        st.switch_page("pages/detalhes.py")

# --- MODIFICAÇÃO AQUI: VISUALIZADOR DA BASE DE CONHECIMENTO ---
st.divider()
st.subheader("📚 Base de Conhecimento Interna")

# Inicializa o estado do botão
if "mostrar_kb" not in st.session_state:
    st.session_state.mostrar_kb = False

if st.button("Mostrar / Ocultar Base de Conhecimento"):
    st.session_state.mostrar_kb = not st.session_state.mostrar_kb
    st.rerun()

# Se o botão foi ativado, carrega o JSON do caminho especificado e exibe como tabela
if st.session_state.mostrar_kb:
    caminho_kb = "/home/emily/Documentos/7_semestre/MDA/processo1/hackathon-lia-time2/data/knowledge_base.json"
    
    if os.path.exists(caminho_kb):
        try:
            with open(caminho_kb, 'r', encoding='utf-8') as f:
                dados_kb = json.load(f)
                
            # Tratamento para garantir que o JSON é lido corretamente pelo Pandas
            if isinstance(dados_kb, list):
                df_kb = pd.DataFrame(dados_kb)
            elif isinstance(dados_kb, dict):
                # Se for dicionário com várias chaves que representam colunas/linhas
                df_kb = pd.DataFrame([dados_kb] if not any(isinstance(v, list) for v in dados_kb.values()) else dados_kb)
            else:
                df_kb = pd.DataFrame([{"Dados": dados_kb}])
                
            st.dataframe(df_kb, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao processar o arquivo JSON: {e}")
    else:
        st.warning(f"Arquivo de base de conhecimento não encontrado no caminho: `{caminho_kb}`")

st.sidebar.markdown(f"**Pendentes:** {total_pendente}\n\n**Críticos:** {len([t for t in total_list if t.get('priority') == 'Crítico'])}")