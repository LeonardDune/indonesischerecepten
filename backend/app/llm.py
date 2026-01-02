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
MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-mpnet-base-v2")

from neo4j_graphrag.embeddings.sentence_transformers import SentenceTransformerEmbeddings
embeddings = SentenceTransformerEmbeddings(model=MODEL_NAME)
