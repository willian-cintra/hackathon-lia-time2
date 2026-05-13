# Hackathon LIA
# Processo 3.1: AGETIC - Triagem Inteligente de Chamados de Suporte de TIC

Time 2 — Emily Flores · Arthur Schneider · Thiago Poganski · Willian Cintra

---

## Sobre o projeto

A AGETIC (Agência de Tecnologia da Informação e Comunicação) opera a Central de Serviços de TIC da UFMS, atendendo requisições, incidentes e problemas da comunidade universitária. A cada início de turno, o analista de primeiro nível lê manualmente todos os chamados abertos, define prioridade, categoriza e, nos casos mais simples, já redige uma resposta inicial.

Este projeto automatiza esse pipeline com um agente LangGraph, reduzindo o tempo de triagem e liberando os analistas para os atendimentos de maior complexidade.

---

## O que o agente faz

O agente recebe chamados em texto livre e executa quatro etapas em sequência:

**Priorização** — estima urgência e impacto do chamado e calcula a prioridade resultante por uma matriz determinística (não pelo LLM). A combinação urgência × impacto sempre produz o mesmo resultado, independente do modelo.

**Categorização e escalonamento** — classifica o chamado como Requisição, Incidente ou Problema (framework ITIL), identifica o tipo de serviço conforme o Catálogo TIC oficial da UFMS (Resolução 78/2020) e define a fila de atendimento (N1, N2 ou N3).

**Rascunho de resposta** — para chamados simples (Requisição de baixa ou média prioridade), gera automaticamente um rascunho de e-mail para o usuário, usando exemplos da base de conhecimento como referência de tom e conteúdo.

**Encerramento** — registra todas as decisões com justificativas textuais, salva o resultado em JSON individual e CSV consolidado, e persiste os chamados que precisam de analista humano em uma fila dedicada.

---

## Arquitetura

O grafo é construído com `StateGraph` do LangGraph. Cada nó tem responsabilidade única e o estado é imutável entre eles — cada nó retorna apenas os campos que é responsável por preencher.

```
START
  │
  ▼
[ingest]          valida campos obrigatórios e normaliza o texto
  │
  ▼
[score_priority]  LLM estima urgência e impacto
  │               PRIORITY_MATRIX calcula a prioridade (determinístico)
  ▼
[classify_type]   LLM classifica categoria, tipo de serviço e fila
  │
  ▼
[route_fn]        Requisição + prioridade Baixo ou Médio  →  draft
  │               qualquer outro caso                     →  queue
  │
  ├── draft ──▶  [draft_response]   gera rascunho com few-shot dinâmico
  │
  └── queue ──▶  [queue_only]       registra na fila humana
                       │
                       ▼
                    [emit]           JSON + CSV + log estruturado
                       │
                      END
```

O roteamento entre `draft` e `queue` é determinístico — a regra está no código, não no LLM. O LLM é usado apenas onde há julgamento subjetivo: estimativa de urgência/impacto, classificação do tipo de chamado e geração de texto.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Orquestração de agentes | LangGraph |
| Integração com LLM | LangChain OpenAI via OpenRouter |
| Modelo | google/gemma-4-31b-it |
| Estado do grafo | TypedDict com Literal types e Optional |
| Testes | pytest |
| Gestão de dependências | pip + requirements.txt |

---

## Estrutura do projeto

```
hackathon-lia-time2/
├── agent/
│   ├── graph.py              # definição do grafo e função de roteamento
│   ├── llm.py                # instâncias singleton do LLM com retry e rastreamento de tokens
│   ├── state.py              # TicketState — estado tipado do grafo
│   ├── nodes/
│   │   ├── ingest.py         # validação e normalização da entrada
│   │   ├── score_priority.py # priorização com PRIORITY_MATRIX
│   │   ├── classify_type.py  # categorização e escalonamento
│   │   ├── draft_response.py # geração de rascunho com few-shot dinâmico
│   │   ├── queue_only.py     # persistência da fila humana
│   │   └── emit.py           # saída JSON, CSV e log estruturado
│   └── utils/
│       └── few_shot.py       # busca exemplos da knowledge base por tipo de serviço
├── prompts/
│   ├── classify_type.md      # prompt com definições ITIL e catálogo TIC oficial
│   ├── score_priority.md     # prompt com critérios de urgência, impacto e regras especiais
│   └── draft_response.md     # prompt com formato de resposta e ANS por serviço
├── data/
│   ├── tickets.json          # 151 tickets sintéticos com gabarito para avaliação
│   └── knowledge_base.json   # 36 exemplos de resposta por tipo de serviço
├── tests/
│   ├── conftest.py           # fixtures compartilhadas
│   └── test_nodes.py         # 37 testes unitários sem chamada ao LLM
├── outputs/                  # gerado em runtime — não versionado
├── run_stub.py               # execução de demonstração com 3 tickets
├── run_batch.py              # processamento do dataset completo com métricas
├── .env.example              # template de variáveis de ambiente
└── requirements.txt
```

---

## Como rodar

### Pré-requisitos

- Python 3.11 ou superior
- Conta no [OpenRouter](https://openrouter.ai) com créditos disponíveis

### Instalação

```bash
git clone https://github.com/willian-cintra/hackathon-lia-time2.git
cd hackathon-lia-time2

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edite o .env e preencha sua OPENROUTER_API_KEY
```

### Executando

```bash
# Demonstração com 3 tickets representativos
python run_stub.py

# Processamento completo do dataset com métricas de acerto
python run_batch.py

# Testes unitários (não requerem API key)
pytest tests/test_nodes.py -v
```

### Saídas geradas

Após rodar o `run_batch.py`, a pasta `outputs/` conterá:

- `TKT-001.json ... TKT-151.json` — decisão completa e justificativas de cada ticket
- `results.csv` — todos os tickets consolidados em planilha
- `human_queue.json` — chamados encaminhados para analista humano
- `metrics.json` — acerto por dimensão, tempo médio e consumo de tokens
- `run.jsonl` — log estruturado com uma linha JSON por ticket processado

---

## Resultados

Avaliado sobre 151 tickets sintéticos gerados a partir do processo oficial da AGETIC, com gabarito verificado matematicamente pela PRIORITY_MATRIX e pela lógica do `route_fn`.

| Dimensão | Acerto |
|---|---|
| Categoria (Requisição / Incidente / Problema) | 94.7% |
| Prioridade (Crítico / Alto / Médio / Baixo) | 75.5% |
| Rota (draft / fila humana) | 84.8% |
| Erros de execução | 0 / 151 |
| Tempo médio por ticket | 9.3s |

Toda decisão vem acompanhada de justificativa textual — nenhuma saída do agente é caixa-preta.

---

## Decisões de design relevantes

**Prioridade calculada por matriz, não pelo LLM.** O modelo estima urgência e impacto separadamente; a combinação é calculada por uma tabela fixa no código. Isso garante que a mesma urgência e o mesmo impacto produzam sempre a mesma prioridade, independente do modelo ou da temperatura.

**Few-shot dinâmico na geração de rascunhos.** Antes de gerar o rascunho, o sistema busca na knowledge base os exemplos mais relevantes para o tipo de serviço do chamado. Um chamado de Redes recebe exemplos de Redes; um chamado de Manutenção recebe exemplos de Manutenção. O prompt fixo define apenas o formato.

**Roteamento determinístico.** A decisão entre gerar rascunho ou encaminhar para analista humano é uma regra de código, não uma decisão do LLM. Qualquer Incidente ou Problema vai para a fila humana. Requisições de alta prioridade também. Apenas Requisições de prioridade Baixo ou Médio recebem rascunho automático.

**Tratamento de falhas por camada.** O `ingest` valida a entrada antes de qualquer chamada ao LLM. O `llm.py` trata 6 tipos distintos de erro de API com mensagens específicas e retry automático. O `route_fn` tem fallback seguro para dados ausentes — sempre vai para fila humana quando não consegue classificar.