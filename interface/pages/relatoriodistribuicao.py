import streamlit as st
import pandas as pd
import os
from agent.config import RESULTS_CSV_PATH

TITLE       = "Relatório de Distribuição"
ARQUIVO_CSV = str(RESULTS_CSV_PATH)

st.title("📊 " + TITLE)


@st.cache_data
def carregar_dados(caminho):
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return None


df = carregar_dados(ARQUIVO_CSV)

if df is None:
    st.warning(f"Nenhum dado encontrado. Execute o `run_batch.py` para gerar resultados.")
    st.stop()

# ── Cards de métricas ─────────────────────────────────────────────────────────
st.subheader("Resumo")

total    = len(df)
drafts   = int((df["route_decision"] == "draft").sum())  if "route_decision" in df.columns else 0
queue    = int((df["route_decision"] == "queue").sum())  if "route_decision" in df.columns else 0
criticos = int((df["priority"] == "Crítico").sum())      if "priority"       in df.columns else 0
falhas   = int(df["llm_error"].notna().sum())             if "llm_error"      in df.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total de tickets",     total)
c2.metric("✅ Resposta automática", drafts,   help="route_decision = draft")
c3.metric("👤 Fila humana",         queue,    help="route_decision = queue")
c4.metric("🔴 Prioridade Crítica",  criticos, help="tickets com prioridade Crítico")
c5.metric("⚠️ Fail-safes",          falhas,   help="tickets onde o LLM falhou")

st.divider()

# ── Distribuição de prioridades ───────────────────────────────────────────────
if "priority" in df.columns:
    st.subheader("Distribuição de Prioridades")
    dist_prioridade = df["priority"].value_counts().reset_index()
    dist_prioridade.columns = ["Prioridade", "Quantidade"]
    ordem = ["Crítico", "Alto", "Médio", "Baixo"]
    dist_prioridade["Prioridade"] = pd.Categorical(
        dist_prioridade["Prioridade"], categories=ordem, ordered=True
    )
    dist_prioridade = dist_prioridade.sort_values("Prioridade")
    st.bar_chart(dist_prioridade.set_index("Prioridade"))
    st.divider()

# ── Distribuição de categorias ────────────────────────────────────────────────
if "category" in df.columns:
    st.subheader("Distribuição de Categorias")
    dist_categoria = df["category"].value_counts().reset_index()
    dist_categoria.columns = ["Categoria", "Quantidade"]
    st.bar_chart(dist_categoria.set_index("Categoria"))
    st.divider()
