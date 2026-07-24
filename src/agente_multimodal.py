"""Agente Multimodal de Imagen (BONUS OPCIONAL).

El enunciado exige implementar al menos uno de dos agentes adicionales: multimodal de imagen o
de accion. Este proyecto implementa el de accion (agente_accion.py) como obligatorio y este
agente multimodal como extension opcional.

Simplificacion de diseno (documentada en el README): en vez de un loop agentico con tools, se
hace una unica llamada multimodal directa a Gemini Vision via LangChain, porque el caso de uso
(analizar UNA imagen y responder sobre ella) no requiere razonamiento multi-paso con tools.
"""
import base64
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import GOOGLE_API_KEY, LLM_MODEL_VISION

_llm_vision = ChatGoogleGenerativeAI(model=LLM_MODEL_VISION, temperature=0, google_api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT_MULTIMODAL = """Eres el Agente Multimodal de Imagen del Departamento Legal de
Patito S.A. Analizas imagenes de contratos, formularios o documentos escaneados: extraes texto
relevante y verificas elementos visibles como firmas, sellos, fechas o clausulas. No inventes
contenido que no puedas ver con claridad en la imagen; si algo no es legible, dilo
explicitamente. Tu respuesta es orientativa y no sustituye la revision de un abogado."""


def _extension_a_mime(ruta: str) -> str:
    ext = Path(ruta).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def analizar_imagen(ruta_imagen: str, pregunta: str) -> dict:
    """Analiza una imagen local con Gemini Vision y responde la pregunta del usuario sobre ella."""
    mime = _extension_a_mime(ruta_imagen)
    data_b64 = base64.b64encode(Path(ruta_imagen).read_bytes()).decode("utf-8")

    mensaje = HumanMessage(
        content=[
            {"type": "text", "text": f"{SYSTEM_PROMPT_MULTIMODAL}\n\nPregunta del usuario: {pregunta}"},
            {"type": "image_url", "image_url": f"data:{mime};base64,{data_b64}"},
        ]
    )
    respuesta = _llm_vision.invoke([mensaje])
    return {"agente": "Agente Multimodal de Imagen", "respuesta": respuesta.content}
