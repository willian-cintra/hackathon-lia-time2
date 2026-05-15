import os
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = "placeholder-para-geracao-do-grafo"

from agent.graph import graph
from agent.config import GRAPH_PNG
from agent.logger import get_logger

logger = get_logger(__name__)


def save_graph_visualization() -> None:
    logger.info("Gerando visualização do grafo...")

    try:
        png_data = graph.get_graph().draw_mermaid_png()
    except Exception as e:
        logger.error("Falha ao gerar imagem do grafo: %s", e)
        logger.info("Dica: instale a dependência com 'pip install grandalf'")
        raise

    GRAPH_PNG.parent.mkdir(parents=True, exist_ok=True)

    with open(GRAPH_PNG, "wb") as f:
        f.write(png_data)

    logger.info("Grafo salvo em: %s", GRAPH_PNG)


if __name__ == "__main__":
    save_graph_visualization()