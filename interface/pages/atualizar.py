import streamlit as st
import sys
import subprocess

st.title("🔄 Atualizar tickets")

if st.button("Rodar LLM"):
    with st.spinner("Rodando..."):
        # Executa como se estivesse digitando no terminal: python funcoes/script_atualizacao.py
        processo = subprocess.run(
            [sys.executable, "run_batch.py"], 
            capture_output=True, 
            text=True
        )
        
        if processo.returncode == 0:
            st.success("Concluído!")
        else:
            st.error("Erro")
            st.code(processo.stderr) # Mostra o erro do terminal