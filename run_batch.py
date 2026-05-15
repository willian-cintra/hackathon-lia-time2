import asyncio
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from agent.graph import graph
from agent.llm import get_token_totals, reset_token_totals
from agent.logger import get_logger
from agent.config import (
    TICKETS_PATH, METRICS_PATH, LOG_JSONL_PATH,
    AGETIC_BATCH_SIZE, OUTPUTS_DIR,
)

logger = get_logger(__name__)

BATCH_SIZE = AGETIC_BATCH_SIZE
LOG_PATH   = LOG_JSONL_PATH

with open(TICKETS_PATH, encoding="utf-8") as f:
    tickets = json.load(f)
    
    #Ajuste para realizar 5 testes
    tickets = tickets[:20]

execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
reset_token_totals()

logger.info("Execução iniciada | id=%s tickets=%d batch_size=%d", execution_id, len(tickets), BATCH_SIZE)

total         = len(tickets)
erros         = 0
acerto_cat    = 0
acerto_prio   = 0
acerto_rota   = 0
rota_draft    = 0
rota_queue    = 0
tempos        = []
erros_detalhe = []

inicio_total = time.time()


async def processar_ticket(ticket: dict) -> dict:
    """Processa um único ticket de forma assíncrona."""
    esperado = {k: v for k, v in ticket.items() if k.startswith("_")}
    entrada  = {k: v for k, v in ticket.items() if not k.startswith("_")}
    inicio   = time.time()

    try:
        resultado = await graph.ainvoke(entrada)
        tempo_ms  = round((time.time() - inicio) * 1000)
        return {
            "ok":       True,
            "entrada":  entrada,
            "esperado": esperado,
            "resultado": resultado,
            "tempo_ms": tempo_ms,
        }
    except Exception as e:
        tempo_ms = round((time.time() - inicio) * 1000)
        logger.error("Falha no ticket %s: %s", entrada.get("ticket_id", "?"), e)
        return {
            "ok":       False,
            "entrada":  entrada,
            "erro":     str(e),
            "tempo_ms": tempo_ms,
        }


async def processar_todos():
    global erros, acerto_cat, acerto_prio, acerto_rota
    global rota_draft, rota_queue

    for i in range(0, total, BATCH_SIZE):
        lote = tickets[i:i + BATCH_SIZE]
        ids  = [t["ticket_id"] for t in lote]
        logger.info("Lote %d/%d: %s", i//BATCH_SIZE + 1, -(-total//BATCH_SIZE), ids)

        tarefas   = [processar_ticket(t) for t in lote]
        resultados = await asyncio.gather(*tarefas)

        for r in resultados:
            tid = r["entrada"]["ticket_id"]

            if not r["ok"]:
                erros += 1
                erros_detalhe.append({"ticket_id": tid, "erro": r["erro"]})
                logger.error("  ERRO %s: %s", tid, r["erro"])
                continue

            tempos.append(r["tempo_ms"])
            resultado = r["resultado"]
            esperado  = r["esperado"]

            cat_ok  = resultado.get("category")      == esperado.get("_expected_category")
            prio_ok = resultado.get("priority")       == esperado.get("_expected_priority")
            rota_ok = resultado.get("route_decision") == esperado.get("_expected_route")

            if cat_ok:  acerto_cat  += 1
            if prio_ok: acerto_prio += 1
            if rota_ok: acerto_rota += 1

            rota = resultado.get("route_decision", "")
            if rota == "draft": rota_draft += 1
            if rota == "queue": rota_queue += 1

            status = "OK" if (cat_ok and prio_ok and rota_ok) else "~~ "
            tokens = resultado.get("tokens_used", 0)
            logger.info(
                "  %s %s | %-10s | %-8s | %s | %s tokens | %dms",
                status, tid,
                resultado.get("category", "?"),
                resultado.get("priority", "?"),
                rota,
                f"{tokens:,}",
                r["tempo_ms"],
            )


asyncio.run(processar_todos())

tempo_total = time.time() - inicio_total
processados = total - erros

pct_cat  = round(acerto_cat  / processados * 100, 1) if processados else 0
pct_prio = round(acerto_prio / processados * 100, 1) if processados else 0
pct_rota = round(acerto_rota / processados * 100, 1) if processados else 0
t_medio  = round(sum(tempos) / len(tempos) / 1000, 1) if tempos else 0

tokens = get_token_totals()

relatorio = (
    f"\n{'='*60}\n"
    f"  RELATÓRIO — AGETIC Triagem Inteligente  [{execution_id}]\n"
    f"{'='*60}\n\n"
    f"  Total de tickets:         {total}\n"
    f"  Processados com sucesso:  {processados}\n"
    f"  Erros de execução:        {erros}\n\n"
    f"  Acerto — Categoria:       {acerto_cat}/{processados}  ({pct_cat}%)\n"
    f"  Acerto — Prioridade:      {acerto_prio}/{processados}  ({pct_prio}%)\n"
    f"  Acerto — Rota:            {acerto_rota}/{processados}  ({pct_rota}%)\n\n"
    f"  Tickets → draft:          {rota_draft}\n"
    f"  Tickets → fila humana:    {rota_queue}\n\n"
    f"  Tempo médio por ticket:   {t_medio}s\n"
    f"  Tempo total:              {round(tempo_total/60, 1)} min\n\n"
    f"  Tokens — prompt:          {tokens['prompt']:,}\n"
    f"  Tokens — completion:      {tokens['completion']:,}\n"
    f"  Tokens — total:           {tokens['total']:,}\n"
    f"  Chamadas ao LLM:          {tokens['calls']:,}\n"
    f"  Custo médio por ticket:   {round(tokens['total']/processados) if processados else 0:,} tokens\n"
    f"{'='*60}"
)
logger.info(relatorio)

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

metricas = {
    "execution_id":      execution_id,
    "dataset":           str(TICKETS_PATH),
    "total_tickets":     total,
    "processados":       processados,
    "erros":             erros,
    "acerto_categoria":  {"absoluto": acerto_cat,  "percentual": pct_cat},
    "acerto_prioridade": {"absoluto": acerto_prio, "percentual": pct_prio},
    "acerto_rota":       {"absoluto": acerto_rota, "percentual": pct_rota},
    "distribuicao_rota": {"draft": rota_draft, "queue": rota_queue},
    "tempo_medio_segundos": t_medio,
    "tempo_total_minutos":  round(tempo_total / 60, 1),
    "batch_size":        BATCH_SIZE,
    "tokens": {
        "prompt":           tokens["prompt"],
        "completion":       tokens["completion"],
        "total":            tokens["total"],
        "chamadas_llm":     tokens["calls"],
        "media_por_ticket": round(tokens["total"] / processados) if processados else 0,
    },
    "log":           str(LOG_PATH),
    "erros_detalhe": erros_detalhe,
}

with open(METRICS_PATH, "w", encoding="utf-8") as f:
    json.dump(metricas, f, ensure_ascii=False, indent=2)

logger.info("Métricas salvas em %s", str(METRICS_PATH))
logger.info("Log estruturado em %s", str(LOG_PATH))
