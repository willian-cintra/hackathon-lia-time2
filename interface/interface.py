import streamlit as st
import json
import os
import glob

# Configurações de arquivos
DIR_PENDING = 'outputs/tickets'
FILE_APPROVED = 'outputs/approve.json'
FILE_REJECTED = 'outputs/reject.json'

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
    # Remove a primeira requisição da lista
    req_data = load_json(filepath)
    
    # Define o arquivo de destino
    target_file = FILE_APPROVED if action == "approve" else FILE_REJECTED
    
    # Carrega dados existentes, adiciona o novo e salva
    history = load_json(target_file)
    history.append(req_data)
    save_json(target_file, history)
    
    # Atualiza o arquivo de pendentes
    try:
        os.remove(filepath)
    except Exception as e:
        st.error(f"Erro ao deletar o arquivo {filepath}: {e}")
        return
    st.success(f"Requisição {'Aprovada' if action == 'approve' else 'Rejeitada'} com sucesso!")

# --- Interface Streamlit ---
st.title("🛠️ Aprovação da classificação do agente")
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
    # Exibição dos dados da requisição
    with st.container(border=True):
        #st.json(req_atual) # Exibe o JSON de forma formatada
        # Converte o dicionário JSON em uma lista formatada para a tabela
        dados_formatados = [
            {"Campo": str(chave).capitalize().replace("_", " "), "Informação": str(valor)} 
            for chave, valor in req_atual.items()
        ]
        
        # Exibe os dados usando uma tabela estática e limpa
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
st.sidebar.markdown("---")
st.sidebar.write(f"**Diretório de entrada:** `{DIR_PENDING}/`")
