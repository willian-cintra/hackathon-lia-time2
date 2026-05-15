import streamlit as st
import json
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent.config import METRICS_PATH, GRAPH_PNG

st.title("📊 Dashboard de Performance — Processo 3.1")

@st.cache_data
def load_metrics():
    if METRICS_PATH.exists():
        with open(METRICS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

metrics = load_metrics()

if metrics:
    # ── KPIs principais ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tickets Processados",  metrics.get('total_tickets', '—'))
    c2.metric("Acurácia (Rota)",      f"{metrics.get('acerto_rota', {}).get('percentual', '—')}%")
    c3.metric("Tempo Médio",          f"{metrics.get('tempo_medio_segundos', '—')}s")
    c4.metric("Consumo de Tokens",    f"{metrics.get('tokens', {}).get('total', 0):,}")

    st.divider()

    # ── Indicadores oficiais AGETIC ───────────────────────────────────────────
    indicadores = metrics.get('indicadores_agetic', {})
    if indicadores:
        st.subheader("📋 Indicadores Oficiais AGETIC")
        st.caption("Fonte: Ficha de Indicadores SECLI/DINTEC/AGETIC")

        ia1 = indicadores.get('chamados_diarios_encerrados', {})
        ia2 = indicadores.get('tempo_atendimento_medio', {})
        ia3 = indicadores.get('taxa_automacao', {})

        ci1, ci2, ci3 = st.columns(3)
        ci1.metric(
            "Chamados Diários Encerrados",
            f"{ia1.get('percentual', '—')}%",
            delta=f"Meta 2023: {ia1.get('meta_2023', '98%')}",
            help=ia1.get('descricao', ''),
        )
        ci2.metric(
            "Tempo de Atendimento Médio",
            f"{ia2.get('segundos', '—')}s",
            delta=f"Meta 2023: {ia2.get('meta_2023', '3h')}",
            help=ia2.get('descricao', ''),
        )
        ci3.metric(
            "Taxa de Automação",
            f"{ia3.get('percentual', '—')}%",
            help=ia3.get('descricao', ''),
        )
        st.divider()

    # ── Gráficos ──────────────────────────────────────────────────────────────
    col_chart, col_stats = st.columns([2, 1])

    with col_chart:
        st.subheader("Distribuição de Rotas")
        df_rota = pd.DataFrame(
            list(metrics.get('distribuicao_rota', {}).items()),
            columns=['Rota', 'Quantidade']
        )
        st.bar_chart(df_rota.set_index('Rota'))

    with col_stats:
        st.subheader("Precisão do Modelo")
        st.write(f"**Categoria:** {metrics.get('acerto_categoria', {}).get('percentual', '—')}%")
        st.write(f"**Prioridade:** {metrics.get('acerto_prioridade', {}).get('percentual', '—')}%")
        st.write(f"**Rota:** {metrics.get('acerto_rota', {}).get('percentual', '—')}%")
        st.divider()
        st.write(f"**Erros:** {metrics.get('erros', 0)}")
        st.write(f"**Tempo total:** {metrics.get('tempo_total_minutos', '—')} min")
        st.info(f"ID da Execução: `{metrics.get('execution_id', '—')}`")

    # ── Visualização do grafo ─────────────────────────────────────────────────
    st.divider()
    st.subheader("🔀 Visualização do Grafo LangGraph")
    if GRAPH_PNG.exists():
        st.image(str(GRAPH_PNG), caption="Grafo de processamento do agente AGETIC", use_column_width=True)
    else:
        st.info("Grafo não gerado. Execute `python save_graph.py` na raiz do projeto.")

else:
    st.warning("Arquivo metrics.json não encontrado. Execute `run_batch.py` para gerar as métricas.")

if st.button("🔄 Recarregar métricas"):
    st.cache_data.clear()
    st.rerun()
