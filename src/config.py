"""Configuracion central del proyecto: variables de entorno, rutas y parametros de RAG.

Todas las credenciales se leen desde variables de entorno (.env), nunca se hardcodean.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------
# Credenciales y modelos (Gemini via variables de entorno)
# --------------------------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite")
LLM_MODEL_VISION = os.getenv("LLM_MODEL_VISION", "gemini-3.1-flash-lite")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

# --------------------------------------------------------------
# Rutas del proyecto
# --------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstores"
REGISTRO_PATH = BASE_DIR / "registro_solicitudes_legal.txt"

# --------------------------------------------------------------
# Parametros de chunking y recuperacion (RAG)
# --------------------------------------------------------------
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K = 4

if not GOOGLE_API_KEY:
    print(
        "ADVERTENCIA: GOOGLE_API_KEY no esta configurada. "
        "Copia .env.example a .env y completa tu API Key antes de ejecutar el proyecto."
    )
