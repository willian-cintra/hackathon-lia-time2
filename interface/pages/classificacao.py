import streamlit as st
import json
import os
import glob
from agent.config import DRAFT_TICKETS_DIR, APROOVE_PATH, REJECT_PATH

# Configurações de arquivos
DIR_PENDING   = str(DRAFT_TICKETS_DIR)
FILE_APPROVED = str(APROOVE_PATH)
FILE_REJECTED = str(REJECT_PATH)

# ── Cores por prioridade ──────────────────────────────────────────────────────
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
                return []
    return []


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def process_request(action, filepath):
    req_data = load_json(filepath)

    target_file = FILE_APPROVED if action == "approve" else FILE_REJECTED

    history = load_json(target_file)
    history.append(req_data)
    save_json(target_file, history)

    try:
        os.remove(filepath)
    except Exception as e:
        st.error(f"Erro ao deletar o arquivo {filepath}: {e}")
        return
    st.success(f"Requisição {'Aprovada' if action == 'approve' else 'Rejeitada'} com sucesso!")


# ── Interface ─────────────────────────────────────────────────────────────────
st.title("🛠️ Aprovação da classificação do agente")

arquivos_pendentes = sorted(glob.glob(os.path.join(DIR_PENDING, '*.json')))

if not arquivos_pendentes:
    st.info("Não há requisições pendentes no momento.")
    if st.button("Verificar novos arquivos"):
        st.rerun()
else:
    arquivo_atual = arquivos_pendentes[0]
    ticket = load_json(arquivo_atual)

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    col_id, col_fila = st.columns([3, 1])
    with col_id:
        st.subheader(f"Ticket: `{ticket.get('ticket_id', '—')}`")
        st.caption(f"Arquivo: `{os.path.basename(arquivo_atual)}`")
    with col_fila:
        st.metric("Na fila", f"{len(arquivos_pendentes)} ticket(s)")

    st.divider()

    # ── Aviso de fail-safe ────────────────────────────────────────────────────
    if ticket.get("llm_error"):
        st.warning(
            f"⚠️ **Fail-safe ativado** — o LLM falhou durante o processamento. "
            f"Os valores abaixo são conservadores e requerem revisão humana.\n\n"
            f"**Motivo:** {ticket['llm_error']}",
            icon="⚠️",
        )

    # ── Cards de classificação ────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    prioridade = ticket.get("priority", "—")
    rota       = ticket.get("route_decision", "—")
    st.markdown("""
        <style>
        /* Altera a fonte do título (Label) */
        [data-testid="stMetricLabel"] {
            font-size: 15px;
            
        }

        /* Altera a fonte do valor (Value) */
        [data-testid="stMetricValue"] {
            font-size : 25px;
        }
        </style>
        """, unsafe_allow_html=True)
    c1.metric("Prioridade", f"{COR_PRIORIDADE.get(prioridade, '⚪')} {prioridade}")
    c2.metric("Categoria",  ticket.get("category",  "—"))
    c3.metric("Tipo de Serviço", ticket.get("service_type", "—"))
    c4.metric("Fila",       ticket.get("queue",     "—"))

    
    st.divider()

    # ── Justificativas ────────────────────────────────────────────────────────
    with st.expander("💡 Justificativas do agente", expanded=False):
        st.markdown("**Prioridade:**")
        st.info(ticket.get("priority_justification", "—"))
        st.markdown("**Classificação:**")
        st.info(ticket.get("classification_justification", "—"))

    # ── Rascunho — só quando route_decision = draft ───────────────────────────
    if rota == "draft" and ticket.get("draft_response"):
        with st.expander("✉️ Rascunho gerado pelo agente", expanded=True):
            new_response = st.text_area(
                label="**Resposta:**", 
                value=ticket.get("draft_response", ""),
                height=150,
                key=f"response_{ticket.get("ticket_id","")}"
            )
            ticket["draft_response"] = new_response
            
            new_closure = st.text_area(
                label="**Encerramento:**",
                value=ticket.get("draft_closure", ""),
                height=100,
                key=f"closure_{ticket.get("ticket_id","")}"
            )
            # Atualiza o dicionário com o texto editado
            ticket["draft_closure"] = new_closure

    st.divider()

    # ── Botões de aprovação ───────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Aprovar", use_container_width=True, type="primary"):
            save_json(arquivo_atual,ticket)
            process_request("approve", arquivo_atual)
            st.rerun()

    with col2:
        if st.button("❌ Rejeitar", use_container_width=True):
            save_json(arquivo_atual,ticket)
            process_request("reject", arquivo_atual)
            st.rerun()