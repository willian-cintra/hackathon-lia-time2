import os
from pathlib import Path

# ── Diretórios base ───────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent   # raiz do projeto
DATA_DIR    = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
PROMPTS_DIR = BASE_DIR / "prompts"

# ── Arquivos de entrada ───────────────────────────────────────────────────────
TICKETS_PATH     = DATA_DIR / "tickets.json"
KNOWLEDGE_BASE_PATH = DATA_DIR / "knowledge_base.json"

# ── Prompts ────────────────────────────────────────────────────────────────────
SCORE_PRIORITY_PROMPT  = PROMPTS_DIR / "score_priority.md"
CLASSIFY_TYPE_PROMPT  = PROMPTS_DIR / "classify_type.md"
DRAFT_RESPONSE_PROMPT = PROMPTS_DIR / "draft_response.md"

# ── Arquivos de saída ─────────────────────────────────────────────────────────
LOG_JSONL_PATH   = OUTPUTS_DIR / "log.jsonl"
RESULTS_CSV_PATH = OUTPUTS_DIR / "results.csv"
METRICS_PATH     = OUTPUTS_DIR / "metrics.json"
QUEUE_PATH       = OUTPUTS_DIR / "human_queue.json"
AGENT_LOG_PATH   = OUTPUTS_DIR / "agent.log"

# ── Variáveis de ambiente ─────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
LLM_MODEL          = os.environ.get("LLM_MODEL", "google/gemma-4-31b-it")
AGETIC_DEBUG       = bool(os.environ.get("AGETIC_DEBUG"))
AGETIC_BATCH_SIZE  = int(os.environ.get("AGETIC_BATCH_SIZE", 5))
