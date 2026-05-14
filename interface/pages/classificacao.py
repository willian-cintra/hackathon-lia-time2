import streamlit as st
import json
import os
import glob
from agent.config import DRAFT_TICKETS_DIR, APROOVE_PATH, REJECT_PATH

# Configurações de arquivos
DIR_PENDING   = str(DRAFT_TICKETS_DIR)
FILE_APPROVED = str(APROOVE_PATH)
FILE_REJECTED = str(REJECT_PATH)


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


# --- Interface Streamlit ---
PAGE_TITLE = "Aprovação da classificação do agente"
PAGE_ICON  = "🛠️"

st.title(PAGE_ICON + PAGE_TITLE)

arquivos_pendentes = sorted(glob.glob(os.path.join(DIR_PENDING, '*.json')))

if not arquivos_pendentes:
    st.info("Não há requisições pendentes no momento.")
    if st.button("Verificar novos arquivos"):
        st.rerun()
else:
    arquivo_atual = arquivos_pendentes[0]
    req_atual = load_json(arquivo_atual)

    st.subheader(f"Analisando Requisição (Restantes na fila: {len(arquivos_pendentes)})")
    st.caption(f"Arquivo de origem: `{os.path.basename(arquivo_atual)}`")

    with st.container(border=True):
        dados_formatados = [
            {"Campo": str(chave).capitalize().replace("_", " "), "Informação": str(valor)}
            for chave, valor in req_atual.items()
        ]
        st.table(dados_formatados)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Aprovar", use_container_width=True, type="primary"):
            process_request("approve", arquivo_atual)
            st.rerun()

    with col2:
        if st.button("❌ Rejeitar", use_container_width=True):
            process_request("reject", arquivo_atual)
            st.rerun()