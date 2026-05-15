import streamlit as st
import json
import os
import glob
import time # Adicionado para dar um pequeno delay antes de mudar de tela
from agent.config import DRAFT_TICKETS_DIR, APROOVE_PATH, REJECT_PATH

# Configurações de caminhos
BASE_OUTPUTS = os.path.abspath(os.path.join(str(DRAFT_TICKETS_DIR), ".."))
DIR_DRAFT    = os.path.join(BASE_OUTPUTS, "draft")
DIR_QUEUE    = os.path.join(BASE_OUTPUTS, "queue")

FILE_APPROVED = str(APROOVE_PATH)
FILE_REJECTED = str(REJECT_PATH)

COR_PRIORIDADE = {
    "Crítico": "🔴",
    "Alto":    "🟠",
    "Médio":   "🟡",
    "Baixo":   "🟢",
}

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def process_request(action, filepath):
    req_data = load_json(filepath)
    target_file = FILE_APPROVED if action == "approve" else FILE_REJECTED
    
    history = load_json(target_file)
    if not isinstance(history, list): 
        history = []
        
    history.append(req_data)
    save_json(target_file, history)
    
    try:
        os.remove(filepath)
    except:
        pass
    
    if action == "approve":
        # Usa o flag já interceptado pelo app.py que chama st.switch_page(pagina_home)
        st.session_state["menu_option"] = "🏠 Tela Inicial (Kanban)"
        st.rerun()
    else:
        st.rerun()

# ── Interface ─────────────────────────────────────────────────────────────────
st.title("🛠️ Aprovação da classificação do agente")

arquivos_draft = glob.glob(os.path.join(DIR_DRAFT, '*.json'))
arquivos_queue = glob.glob(os.path.join(DIR_QUEUE, '*.json'))
todos_arquivos = sorted(arquivos_draft + arquivos_queue)

if not todos_arquivos:
    st.info("Não há requisições pendentes no momento.")
    if st.button("Verificar novos arquivos"):
        st.rerun()
else:
    # 1. Montar lista de opções com um item neutro no início
    opcoes_tickets = ["— Selecione um ticket para iniciar —"]
    mapeamento_tickets = {}
    
    for arq in todos_arquivos:
        dados = load_json(arq)
        tid = dados.get('ticket_id', os.path.basename(arq))
        origem = "Draft" if "draft" in arq.lower() else "Queue"
        label = f"{tid} ({origem})"
        opcoes_tickets.append(label)
        mapeamento_tickets[label] = arq

    # 2. Lógica de índice padrão (Foco do Kanban ou Neutro)
    indice_padrao = 0 # Começa no "Selecione..."
    
    if "ticket_id_focado" in st.session_state and st.session_state.ticket_id_focado:
        target = st.session_state.ticket_id_focado
        for i, label in enumerate(opcoes_tickets):
            if target in label:
                indice_padrao = i
                break
        # Limpa o foco para não interferir em navegações futuras
        del st.session_state["ticket_id_focado"]

    # 3. Seletor de Tickets
    ticket_selecionado = st.selectbox(
        "Tickets pendentes",
        options=opcoes_tickets,
        index=indice_padrao
    )

    # 4. Verificação: Se não selecionou nada, mostra instrução
    if ticket_selecionado == opcoes_tickets[0]:
        st.divider()
        st.info("💡 Por favor, selecione um ticket na lista acima para visualizar os detalhes da classificação e o rascunho da resposta.")
        st.stop() # Para a execução aqui até que um ticket seja escolhido

    # 5. Se selecionou um ticket, carrega os dados
    arquivo_atual = mapeamento_tickets[ticket_selecionado]
    ticket = load_json(arquivo_atual)

    if "editando" not in st.session_state:
        st.session_state.editando = False

    # ── Cabeçalho do Ticket ──────────────────────────────────────────────────
    col_id, col_fila = st.columns([3, 1])
    with col_id:
        st.subheader(f"Analisando Ticket: `{ticket.get('ticket_id', '—')}`")
        st.caption(f"Origem do Arquivo: `{os.path.basename(arquivo_atual)}`")
    with col_fila:
        st.metric("Total na Fila", len(todos_arquivos))

    st.divider()

    # ── Cards de classificação ────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    prioridade = ticket.get("priority", "—")
    
    st.markdown("""
        <style>
        [data-testid="stMetricLabel"] { font-size: 14px; }
        [data-testid="stMetricValue"] { font-size : 22px; }
        </style>
        """, unsafe_allow_html=True)
        
    c1.metric("Prioridade", f"{COR_PRIORIDADE.get(prioridade, '⚪')} {prioridade}")
    c2.metric("Categoria",  ticket.get("category",  "—"))
    c3.metric("Serviço",    ticket.get("service_type", "—"))
    c4.metric("Fila Destino", ticket.get("queue", "—"))

    st.divider()

    # ── Justificativas ────────────────────────────────────────────────────────
    with st.expander("💡 Justificativas do agente", expanded=False):
        st.markdown("**Análise de Prioridade:**")
        st.info(ticket.get("priority_justification", "—"))
        st.markdown("**Análise de Classificação:**")
        st.info(ticket.get("classification_justification", "—"))

    # ── Rascunho / Edição ─────────────────────────────────────────────────────
    if ticket.get("draft_response"):
        with st.expander("✉️ Rascunho da Resposta", expanded=True):
            if st.session_state.editando:
                novo_texto = st.text_area("Editar e-mail:", value=ticket.get("draft_response", ""), height=300)
                if st.button("💾 Salvar Alterações"):
                    ticket["draft_response"] = novo_texto
                    save_json(arquivo_atual, ticket)
                    st.session_state.editando = False
                    st.success("Alterações salvas!")
                    st.rerun()
            else:
                st.success(ticket.get("draft_response", ""))
                
            if ticket.get("draft_closure"):
                st.markdown("**Sugestão de Encerramento:**")
                st.info(ticket.get("draft_closure", ""))

    st.divider()

    # ── Botões de Ação ────────────────────────────────────────────────────────
    
    # Verifica se há um e-mail/rascunho no ticket
    tem_email = bool(ticket.get("draft_response"))

    if tem_email:
        # Layout com dois botões
        col_ap, col_ed = st.columns(2)

        with col_ap:
            if st.button("✅ Aprovar e Finalizar", use_container_width=True, type="primary"):
                process_request("approve", arquivo_atual)

        with col_ed:
            if not st.session_state.editando:
                if st.button("📝 Editar Resposta", use_container_width=True):
                    st.session_state.editando = True
                    st.rerun()
            else:
                if st.button("🚫 Cancelar Edição", use_container_width=True):
                    st.session_state.editando = False
                    st.rerun()
    else:
        # Layout com o botão centralizado quando não tem e-mail
        _, col_ap, _ = st.columns([1, 2, 1])
        
        with col_ap:
            if st.button("✅ Aprovar e Finalizar", use_container_width=True, type="primary"):
                process_request("approve", arquivo_atual)