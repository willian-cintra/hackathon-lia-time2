# agent/logger.py
"""
Configuração central de logging do agente AGETIC.

Como usar em qualquer módulo do projeto:
    from agent.logger import get_logger
    logger = get_logger(__name__)
    logger.info("mensagem")

Níveis disponíveis (do mais ao menos grave):
    logger.critical(...)   # falha que encerra o processo
    logger.error(...)      # erro recuperável, operação falhou
    logger.warning(...)    # algo inesperado mas o fluxo continua
    logger.info(...)       # progresso normal de execução
    logger.debug(...)      # detalhes para diagnóstico (silenciado em prod)
"""

import logging
import sys
from agent.config import OUTPUTS_DIR, AGENT_LOG_PATH, AGETIC_DEBUG as _DEBUG

# ── Diretório e arquivo de log ────────────────────────────────────────────────
LOG_DIR  = OUTPUTS_DIR
LOG_FILE = AGENT_LOG_PATH

# ── Formato das mensagens ─────────────────────────────────────────────────────
LOG_FORMAT  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Nível padrão: INFO em produção, DEBUG se AGETIC_DEBUG estiver setado ──────
LOG_LEVEL = logging.DEBUG if _DEBUG else logging.INFO

_configured = False  # guarda para não adicionar handlers duplicados


def _setup_root_logger() -> None:
    """Configura o root logger uma única vez."""
    global _configured
    if _configured:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Handler 1 — console (stdout)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(LOG_LEVEL)
    root.addHandler(console)

    # Handler 2 — arquivo rotativo
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # arquivo sempre guarda tudo
    root.addHandler(file_handler)

    # Silenciar loggers barulhentos de bibliotecas externas
    for noisy in ("httpx", "httpcore", "openai", "urllib3", "langchain"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger nomeado, garantindo que a configuração
    central foi aplicada antes do primeiro uso.
    """
    _setup_root_logger()
    return logging.getLogger(name)
