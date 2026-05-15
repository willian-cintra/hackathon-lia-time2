import streamlit as st
import json
import pandas as pd
import os

def load_metrics():
    # Caminho subindo dois níveis (de interface/pages para raiz) e entrando em outputs
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../outputs/metrics.json'))
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

st.title("📊 Dashboard de Performance — Processo 3.1")

metrics = load_metrics()

if metrics:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tickets Processados", metrics['total_tickets'])
    c2.metric("Acurácia (Rota)", f"{metrics['acerto_rota']['percentual']}%")
    c3.metric("Tempo Médio", f"{metrics['tempo_medio_segundos']}s")
    c4.metric("Consumo de Tokens", f"{metrics['tokens']['total']:,}")

    st.divider()

    col_chart, col_stats = st.columns([2, 1])

    with col_chart:
        st.subheader("Distribuição de Rotas")
        df_rota = pd.DataFrame(list(metrics['distribuicao_rota'].items()), columns=['Rota', 'Quantidade'])
        st.bar_chart(df_rota.set_index('Rota'))

    with col_stats:
        st.subheader("Precisão do Modelo")
        st.write(f"**Categoria:** {metrics['acerto_categoria']['percentual']}%")
        st.write(f"**Prioridade:** {metrics['acerto_prioridade']['percentual']}%")
        st.info(f"ID da Execução: {metrics['execution_id']}")
else:
    st.warning("Arquivo metrics.json não encontrado. Execute o processamento para gerar as métricas.")