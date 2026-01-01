import streamlit as st

# Create the LLM
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    openai_api_key=st.secrets["OPENAI_API_KEY"],
    model=st.secrets["OPENAI_MODEL"],
)

# Embeddings model
MODEL_NAME = st.secrets["EMBED_MODEL"]

from neo4j_graphrag.embeddings.sentence_transformers import SentenceTransformerEmbeddings
embeddings = SentenceTransformerEmbeddings(model=MODEL_NAME)