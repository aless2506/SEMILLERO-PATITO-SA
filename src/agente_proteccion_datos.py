"""Agente de Proteccion de Datos.

Responde sobre tratamiento de datos personales, consentimiento, derechos de los titulares y
retencion, usando UNICAMENTE su propia base de conocimiento embebida (02_Proteccion_Datos.txt).
"""
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import DATA_DIR, GOOGLE_API_KEY, LLM_MODEL, TOP_K
from .vectorstore_utils import construir_o_cargar_vectorstore

_vectordb_datos = construir_o_cargar_vectorstore(
    doc_path=str(DATA_DIR / "02_Proteccion_Datos.txt"),
    nombre_indice="proteccion_datos",
)


@tool
def buscar_en_base_proteccion_datos(consulta: str) -> str:
    """Busca fragmentos relevantes en la Politica de Proteccion de Datos Personales de Patito S.A.
    Usa esta herramienta SIEMPRE antes de responder sobre tratamiento de datos, consentimiento,
    derechos de los titulares, retencion/eliminacion de datos, seguridad o brechas."""
    resultados = _vectordb_datos.similarity_search(consulta, k=TOP_K)
    if not resultados:
        return "NO_RESULTS"
    return "\n\n".join(
        f"[Fragmento {i} | fuente: {d.metadata.get('fuente', '02_Proteccion_Datos.txt')}]\n"
        f"{d.page_content}"
        for i, d in enumerate(resultados, 1)
    )


_llm_datos = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0, google_api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT_PROTECCION_DATOS = """Eres el Agente de Proteccion de Datos del Departamento Legal
de Patito S.A.

Respondes UNICAMENTE preguntas sobre: principios de proteccion de datos, bases para el
tratamiento, derechos de los titulares, retencion/eliminacion de datos, seguridad y manejo de
brechas, y encargados de tratamiento (proveedores que procesan datos por cuenta de Patito S.A.).

REGLAS:
- SIEMPRE usa la herramienta buscar_en_base_proteccion_datos antes de responder. No respondas
  de memoria.
- Basa tu respuesta UNICAMENTE en los fragmentos recuperados. No inventes plazos, principios ni
  derechos que no esten en la base documental.
- Si los fragmentos recuperados no cubren la pregunta (o la herramienta devuelve NO_RESULTS),
  responde exactamente: "No encontre informacion suficiente en la base documental proporcionada."
- Al final de tu respuesta, indica brevemente de que fragmento(s) sacaste la informacion.
- Aclara que tu respuesta es orientativa y no sustituye la asesoria de un abogado.
- No respondas preguntas de contratos ni de cumplimiento normativo; esas las maneja otro agente
  especializado."""

agente_proteccion_datos = create_agent(
    model=_llm_datos,
    tools=[buscar_en_base_proteccion_datos],
    system_prompt=SYSTEM_PROMPT_PROTECCION_DATOS,
)


def consultar_proteccion_datos(pregunta: str) -> dict:
    """Invoca al agente de proteccion de datos y devuelve respuesta + fuentes usadas."""
    resultado = agente_proteccion_datos.invoke({"messages": [{"role": "user", "content": pregunta}]})
    fuentes = [
        m.content[:300]
        for m in resultado["messages"]
        if type(m).__name__ == "ToolMessage" and m.name == "buscar_en_base_proteccion_datos"
    ]
    return {
        "agente": "Agente de Proteccion de Datos",
        "respuesta": resultado["messages"][-1].content,
        "fuentes": fuentes,
    }
