import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./database/salesbot.db")
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./vector_store/chroma_db")
    
    # Model configuration
    MODEL_NAME = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.3
    MAX_TOKENS = 2048