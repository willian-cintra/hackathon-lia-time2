import json
import os
import time
from dotenv import load_dotenv
from agent.graph import graph

load_dotenv()

# ── Configuração ──────────────────────────────────────────────────────────────
TICKETS_PATH = "data/tickets.json"
METRICS_PATH = "outputs/metrics.json"

# ── Carrega o dataset ─────────────────────────────────────────────────────────
with open(TICKETS_PATH, encoding="utf-8") as f:
    tickets = json.load(f)

print(f"\nIniciando processamento de {len(tickets)} tickets...\n")

# ── Contadores ────────────────────────────────────────────────────────────────
total          = len(tickets)
erros          = 0
acerto_cat     = 0
acerto_prio    = 0
acerto_rota    = 0
rota_draft     = 0
rota_queue     = 0
tempos         = []
erros_detalhe  = []

# ── Processamento ─────────────────────────────────────────────────────────────
for ticket in tickets:

    # separa gabarito dos dados de entrada
    esperado = {k: v for k, v in ticket.items() if k.startswith("_")}
    entrada  = {k: v for k, v in ticket.items() if not k.startswith("_")}

    print(f"[{entrada['ticket_id']}] processando...", end=" ", flush=True)

    inicio = time.time()

    try:
        resultado = graph.invoke(entrada)
        tempo_ms  = round((time.time() - inicio) * 1000)
        tempos.append(tempo_ms)

        # comparação com gabarito
        cat_ok   = resultado.get("category")       == esperado.get("_expected_category")
        prio_ok  = resultado.get("priority")        == esperado.get("_expected_priority")
        rota_ok  = resultado.get("route_decision")  == esperado.get("_expected_route")

        if cat_ok:   acerto_cat  += 1
        if prio_ok:  acerto_prio += 1
        if rota_ok:  acerto_rota += 1

        rota = resultado.get("route_decision", "")
        if rota == "draft": rota_draft += 1
        if rota == "queue": rota_queue += 1

        status = "✓" if (cat_ok and prio_ok and rota_ok) else "~"
        print(f"{status} [{tempo_ms}ms] cat={resultado.get('category')} prio={resultado.get('priority')} rota={rota}")

    except Exception as e:
        tempo_ms = round((time.time() - inicio) * 1000)
        erros += 1
        erros_detalhe.append({
            "ticket_id": entrada["ticket_id"],
            "erro": str(e),
        })
        print(f"✗ ERRO: {e}")

# ── Cálculo das métricas ──────────────────────────────────────────────────────
processados   = total - erros
tempo_medio   = round(sum(tempos) / len(tempos) / 1000, 1) if tempos else 0
tempo_total   = round(sum(tempos) / 1000, 1)

pct_cat   = round(acerto_cat  / processados * 100, 1) if processados else 0
pct_prio  = round(acerto_prio / processados * 100, 1) if processados else 0
pct_rota  = round(acerto_rota / processados * 100, 1) if processados else 0

# ── Relatório no terminal ─────────────────────────────────────────────────────
print(f"""
{'='*55}
  RELATÓRIO FINAL — AGETIC Triagem Inteligente
{'='*55}

  Total de tickets:       {total}
  Processados com sucesso:{processados}
  Erros de execução:      {erros}

  Acerto — Categoria:     {acerto_cat}/{processados}  ({pct_cat}%)
  Acerto — Prioridade:    {acerto_prio}/{processados}  ({pct_prio}%)
  Acerto — Rota:          {acerto_rota}/{processados}  ({pct_rota}%)

  Tickets → draft:        {rota_draft}
  Tickets → fila humana:  {rota_queue}

  Tempo médio por ticket: {tempo_medio}s
  Tempo total:            {tempo_total}s
{'='*55}
""")

# ── Salva metrics.json ────────────────────────────────────────────────────────
os.makedirs("outputs", exist_ok=True)

metricas = {
    "dataset":          TICKETS_PATH,
    "total_tickets":    total,
    "processados":      processados,
    "erros":            erros,
    "acerto_categoria": {"absoluto": acerto_cat,  "percentual": pct_cat},
    "acerto_prioridade":{"absoluto": acerto_prio, "percentual": pct_prio},
    "acerto_rota":      {"absoluto": acerto_rota, "percentual": pct_rota},
    "distribuicao_rota":{"draft": rota_draft, "queue": rota_queue},
    "tempo_medio_segundos": tempo_medio,
    "tempo_total_segundos": tempo_total,
    "erros_detalhe":    erros_detalhe,
}

with open(METRICS_PATH, "w", encoding="utf-8") as f:
    json.dump(metricas, f, ensure_ascii=False, indent=2)

print(f"  Métricas salvas em {METRICS_PATH}\n")