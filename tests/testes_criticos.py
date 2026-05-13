# -*- coding: utf-8 -*-
import json
import os
import sys
from collections import Counter

# Forcar UTF-8 no terminal Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()
from agent.graph import graph

# Leitura com encoding explicito
with open("data/tickets.json", encoding="utf-8") as f:
    tickets = json.load(f)

# Usar comparacao por bytes para evitar problemas de encoding
critico  = "Cr\u00edtico"           # Crítico
seguranca = "Seguran\u00e7a da Informa\u00e7\u00e3o"  # Segurança da Informação

teste = [
    t for t in tickets
    if t["_expected_priority"] == critico
    or t["_service_type"] == seguranca
][:20]

print(f"Testando {len(teste)} tickets\n")

if len(teste) == 0:
    print("ERRO: nenhum ticket encontrado.")
    print("Verifique se o arquivo tickets.json esta em UTF-8.")
    sys.exit(1)

acertos = 0
obtidos = Counter()

for t in teste:
    entrada = {k: v for k, v in t.items() if not k.startswith("_")}
    r = graph.invoke(entrada)
    prio     = r.get("priority", "")
    esperado = t["_expected_priority"]
    servico  = t["_service_type"]
    tid      = t["ticket_id"]

    obtidos[prio] += 1
    ok = "OK" if prio == esperado else "ERRO"
    if prio == esperado:
        acertos += 1

    print(f"[{ok}] {tid}: esperado={esperado} obtido={prio} | {servico}")

total = len(teste)
pct   = round(acertos / total * 100, 1)
print(f"\nAcerto: {acertos}/{total} ({pct}%)")
print(f"Distribuicao obtida: {dict(obtidos)}")