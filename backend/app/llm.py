import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the backend directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Create the LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL", "gpt-4"),
)

# Embeddings model
#MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-mpnet-base-v2")

#from neo4j_graphrag.embeddings.sentence_transformers import SentenceTransformerEmbeddings
#embeddings = SentenceTransformerEmbeddings(model=MODEL_NAME)

from sentence_transformers import SentenceTransformer
import torch
import os

MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-mpnet-base-v2")

_model = None

def embed_query(text: str):
    global _model
    if _model is None:
        # lazy load MPNet pas bij eerste query
        model = SentenceTransformer(MODEL_NAME)

        # INT8 quantization: reduceert geheugen ~60%
        model = torch.quantization.quantize_dynamic(
            model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )
        _model = model

    # single query
    return _model.encode([text], normalize_embeddings=False)[0].tolist()
