# llm.py
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

# --- Load .env explicitly ---
# Zorg dat dit pad klopt met de locatie van je .env in het project
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# --- LLM Factory ---
def get_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Set it in the environment or .env file")
    
    model_name = os.getenv("OPENAI_MODEL", "gpt-4")
    return ChatOpenAI(
        api_key=api_key,
        model=model_name
    )

# --- Embeddings Model ---
MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_model = None

def embed_query(text: str):
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model.encode([text], normalize_embeddings=False)[0].tolist()

def embed_documents(texts: list[str]):
    return [embed_query(t) for t in texts]
