import streamlit as st
import json
import os

# Configurações de arquivos
FILE_PENDING = '../outputs/results.json'
FILE_APPROVED = '../outputs/approve.json'
FILE_REJECTED = '../outputs/reject.json'

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

# Inicialização do estado da sessão
if 'requests' not in st.session_state:
    st.session_state.requests = load_json(FILE_PENDING)

def process_request(action):
    # Remove a primeira requisição da lista
    current_req = st.session_state.requests.pop(0)
    
    # Define o arquivo de destino
    target_file = FILE_APPROVED if action == "approve" else FILE_REJECTED
    
    # Carrega dados existentes, adiciona o novo e salva
    history = load_json(target_file)
    history.append(current_req)
    save_json(target_file, history)
    
    # Atualiza o arquivo de pendentes
    save_json(FILE_PENDING, st.session_state.requests)
    
    st.success(f"Requisição {'Aprovada' if action == 'approve' else 'Rejeitada'} com sucesso!")

# --- Interface Streamlit ---
st.title("🛠️ Aprovação da classificação do agente")

if not st.session_state.requests:
    st.info("Não há requisições pendentes no momento.")
    if st.button("Verificar novos arquivos"):
        st.session_state.requests = load_json(FILE_PENDING)
        st.rerun()
else:
    req_atual = st.session_state.requests[0]
    
    st.subheader(f"Analisando Requisição (Restantes: {len(st.session_state.requests)})")
    
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
            process_request("approve")
            st.rerun()
            
    with col2:
        if st.button("❌ Rejeitar", use_container_width=True):
            process_request("reject")
            st.rerun()

